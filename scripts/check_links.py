#!/usr/bin/env python3
"""
Check every URL in both datasets and report the ones that look dead.

Run locally:

    python scripts/check_links.py

This is the monthly companion to scripts/validate.py — it doesn't check
structure, it checks whether the URLs still resolve. It never edits the
CSVs; it only reports. Three rules drive every decision here:

1. HTTP 200 is not proof of life. A response is only treated as a success
   if its body doesn't look like a parked domain, a for-sale page, or an
   empty shell — the same failure mode the AmCham Mexico entry hit before
   scripts/validate.py existed (see CHANGELOG.md, v0.2.0).
2. A single failed request is not proof of death. Big sites block
   automated clients. Each URL that doesn't succeed on the first try gets
   retried with a delay and a different browser identity, and a response
   that looks like an anti-bot challenge (Cloudflare/Akamai/CAPTCHA-style
   pages, or status codes like 403/429/503) is reported separately from a
   URL that never resolves at all — the two need different follow-up.
3. Only the site may condemn the site. A refused connection, a reset, a
   timeout or an empty body describe the network between this run and the
   host; they are reported, but they can never make a URL a candidate for
   removal. That takes the server saying the resource is gone (404/410) or
   the domain serving a placeholder. Before any of it is believed, a
   control probe checks that this run can reach the open web at all: if it
   can't, the whole run is marked unusable for removals.

   Rule 3 exists because v0.5.0 removed 21 sources on connection-level
   errors and a stray placeholder string. At least three were alive, among
   them VERA Files, an IFCN verified signatory. Retrying did not catch it —
   the retries repeated the same request from the same network — and
   neither did a second opinion, because scripts/discover_candidates.py
   calls check_url() too and so is the same opinion.

In CI (GITHUB_TOKEN + GITHUB_REPOSITORY set), findings are posted to a
single recurring GitHub issue (label "link-check") instead of a fresh
issue every run, so repeat offenders are visible across months. Run
locally, findings just print — nothing is posted without a token.

Standard library only — no dependencies to install.
"""

import csv
import datetime as dt
import http.cookiejar
import json
import os
import random
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict, namedtuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

OSINT_CSV = REPO / "Fonti_OSINT.csv"
DISINFO_CSV = REPO / "disinfo_sources_master.csv"

# --------------------------------------------------------------------------
# Request behaviour
# --------------------------------------------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# One entry per attempt: request timeout, and (min, max) jittered delay
# before that attempt (the first attempt fires immediately).
ATTEMPT_TIMEOUTS = [12, 15, 20]
RETRY_DELAYS = [(0, 0), (20, 40), (45, 90)]

MAX_WORKERS = 25
MAX_BODY_BYTES = 200_000

SSL_CONTEXT = ssl.create_default_context()

# A shared cookie jar so a redirect chain that gates on a consent/session
# cookie (common on EU institutional and Swiss news sites) can complete
# instead of looping forever — CookieJar is documented as thread-safe.
OPENER = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
    urllib.request.HTTPSHandler(context=SSL_CONTEXT),
)

# A handful of sites still use a client-side meta-refresh instead of an
# HTTP redirect. urllib has no reason to follow that on its own, so a
# small stub body would otherwise look empty/parked even though the page
# is alive — chase it exactly one hop further.
META_REFRESH_RE = re.compile(
    r'<meta[^>]+http-equiv=["\']?refresh["\']?[^>]+content=["\'][^;]*;\s*url=([^"\'>]+)',
    re.IGNORECASE,
)

# Status codes typical of anti-bot / rate-limit responses rather than a
# genuinely missing page.
BLOCKED_STATUS = {401, 403, 405, 429, 503, 999}

# Deliberately specific phrasing lifted from real vendor challenge/block
# pages — not generic words like "captcha" or "akamai", which show up
# harmlessly on huge numbers of ordinary sites (a reCAPTCHA signup widget,
# an Akamai CDN script URL) and would otherwise flag healthy sites as
# blocked. Precision matters more than recall here.
BOT_CHALLENGE_MARKERS = [
    "just a moment...", "attention required! | cloudflare",
    "checking your browser before accessing",
    "our systems have detected unusual traffic from your computer network",
    "unusual traffic from your computer network",
    "press & hold to confirm you are a human",
    "request unsuccessful. incapsula incident id",
    "distil_r_captcha", "px-captcha", "datadome", "perimeterx",
]

# Hosts that a domain sale/parking service redirects to. Landing on one of
# these is the strongest parked signal there is — it doesn't depend on
# reading the page at all — so it stands on its own.
PARKING_HOSTS = {
    "hugedomains.com", "dan.com", "afternic.com", "sedo.com",
    "sedoparking.com", "bodis.com", "parkingcrew.net", "spaceship.com",
    "above.com", "undeveloped.com",
}

# Phrases from real parked and suspended pages. Unlike PARKING_HOSTS these
# are only text, so they are never conclusive alone: an ordinary article can
# quote any of them. A hit only counts on a page small enough to be a
# placeholder (see PARKED_MAX_TEXT).
#
# "future home of something quite cool" used to live here. It is the stock
# Apache/cPanel placeholder, not a for-sale page, and it matched VERA Files
# — a live IFCN signatory — which is how v0.5.0 came to remove it. A string
# that means "this server is unconfigured" cannot mean "this source is
# gone", so it is not a parked marker.
PARKED_MARKERS = [
    "domain may be for sale", "this domain is for sale", "buy this domain",
    "domain for sale", "the domain has expired", "this web page is parked",
    "parking page", "parkingcrew",
    "account has been suspended", "website disabled", "this account has been suspended",
]

# A parked or suspended page is a placeholder. Above this much text the page
# is doing something else, and a marker in it is a quotation, not a verdict.
PARKED_MAX_TEXT = 20_000

# Codes that say the resource itself is gone, as opposed to refused,
# rate-limited or broken. Only these and a confirmed parked page make a URL
# a candidate for removal.
GONE_STATUS = {404, 410}

BUCKET_TITLES = {
    "gone": "Gone — the server says the resource does not exist (404/410)",
    "parked": "Parked or suspended — the domain resolves to a placeholder",
    "unreachable": "Unreachable from this run — says nothing about the site",
    "blocked": "Blocked by anti-bot protection — needs a manual check",
    "empty": "HTTP 200 with an empty body — inconclusive, check by hand",
    "http_error": "Persistent HTTP error (not a typical anti-bot code)",
    "timeout": "Timed out on every attempt",
    "tls_error": "TLS/certificate error on every attempt",
    "other": "Inconclusive — mixed results across attempts",
}

# The only two buckets a removal may be based on. Everything else describes
# this run's own conditions — a refused connection, a bot wall, a timeout —
# and says nothing about whether the source still exists.
#
# v0.5.0 removed 21 sources, of which at least three were alive, because a
# connection-level failure counted as "dead". It cannot any more: a network
# error is a verdict on the path, not on the host.
REMOVAL_CANDIDATE_BUCKETS = {"gone", "parked"}

BUCKET_ORDER = [
    "gone", "parked", "unreachable", "blocked", "empty",
    "http_error", "timeout", "tls_error", "other",
]


Ref = namedtuple("Ref", "dataset line name column")


@dataclass
class Attempt:
    category: str  # success | gone | parked | empty | blocked | http_error
                    # | dns_error | conn_error | timeout | ssl_error
                    # | other_error
    status: "int | None"
    detail: str


@dataclass
class Verdict:
    bucket: str
    detail: str


# --------------------------------------------------------------------------
# Loading targets
# --------------------------------------------------------------------------

def load_targets():
    targets = []

    with OSINT_CSV.open(encoding="utf-8", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle)):
            line = index + 2
            name = row.get("Fonte", "").strip()
            url = row.get("URL", "").strip()
            if url:
                targets.append((url, Ref(OSINT_CSV.name, line, name, "URL")))
            feed = row.get("RSS Feed", "").strip()
            if feed:
                targets.append((feed, Ref(OSINT_CSV.name, line, name, "RSS Feed")))

    with DISINFO_CSV.open(encoding="utf-8", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle)):
            line = index + 2
            domain = row.get("domain", "").strip()
            if domain:
                targets.append((f"https://{domain}", Ref(DISINFO_CSV.name, line, domain, "domain")))

    by_url = defaultdict(list)
    for url, ref in targets:
        by_url[url].append(ref)
    return by_url


# --------------------------------------------------------------------------
# Checking a single URL
# --------------------------------------------------------------------------

def _parking_host(final_url):
    """The parking service a URL ended up on, or None."""
    host = (urllib.parse.urlparse(final_url or "").hostname or "").lower()
    for known in PARKING_HOSTS:
        if host == known or host.endswith("." + known):
            return host
    return None


def classify_response(status, headers, body_bytes, final_url=""):
    text = body_bytes.decode("utf-8", errors="replace").lower()
    header_blob = " ".join(f"{k.lower()}:{v.lower()}" for k, v in (headers.items() if headers else []))

    bot_hit = next((m for m in BOT_CHALLENGE_MARKERS if m in text or m in header_blob), None)
    if bot_hit is None and "access denied" in text and "reference #" in text:
        bot_hit = "access denied ... reference #"  # Akamai's default block page
    if status in BLOCKED_STATUS or bot_hit:
        detail = f"HTTP {status}" + (f", matched anti-bot marker {bot_hit!r}" if bot_hit else "")
        return Attempt("blocked", status, detail)

    if 200 <= status < 300:
        landed_on = _parking_host(final_url)
        if landed_on:
            return Attempt("parked", status, f"HTTP {status}, redirected to parking service {landed_on!r}")

        stripped = re.sub(r"\s+", "", text)
        if len(stripped) < 60:
            # Not a verdict. A server can answer 200 with nothing for a
            # client it doesn't like, and did: Lanka Business Online was
            # removed in v0.5.0 over an empty body while serving 120 KB to
            # an ordinary browser. Report it, never act on it alone.
            return Attempt(
                "empty", status,
                f"HTTP {status}, body is empty or near-empty ({len(body_bytes)} bytes) — "
                f"inconclusive, not evidence the source is gone",
            )

        parked_hit = next((m for m in PARKED_MARKERS if m in text), None)
        if parked_hit and len(stripped) < PARKED_MAX_TEXT:
            return Attempt(
                "parked", status,
                f"HTTP {status}, matched parked-domain marker {parked_hit!r} "
                f"on a {len(stripped)}-character page",
            )
        if parked_hit:
            # The phrase is there but the page is far too substantial to be
            # a placeholder — it is being quoted, not served.
            return Attempt(
                "success", status,
                f"HTTP {status} (marker {parked_hit!r} ignored on a {len(stripped)}-character page)",
            )
        return Attempt("success", status, f"HTTP {status}")

    if 300 <= status < 400:
        # A redirect chain that never lands on a final page — with cookies
        # enabled in fetch_once, that's usually a loop urllib gave up on,
        # not evidence the destination is gone.
        return Attempt("blocked", status, f"HTTP {status}, redirect never reached a final page — needs a manual check")

    if status in GONE_STATUS:
        return Attempt("gone", status, f"HTTP {status} — the server says this resource does not exist")

    return Attempt("http_error", status, f"HTTP {status}")


def _meta_refresh_target(base_url, body_bytes):
    text = body_bytes.decode("utf-8", errors="replace")
    match = META_REFRESH_RE.search(text)
    if not match:
        return None
    return urllib.parse.urljoin(base_url, match.group(1).strip().strip("'\""))


def _request(url, user_agent):
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
        },
    )


def fetch_once(url, user_agent, timeout):
    req = _request(url, user_agent)
    try:
        with OPENER.open(req, timeout=timeout) as resp:
            status, headers, final_url = resp.status, resp.headers, resp.geturl()
            body = resp.read(MAX_BODY_BYTES)
            if 200 <= status < 300:
                stripped = re.sub(r"\s+", "", body.decode("utf-8", errors="replace"))
                if len(stripped) < 500:
                    target = _meta_refresh_target(final_url, body)
                    if target and target != final_url:
                        try:
                            with OPENER.open(_request(target, user_agent), timeout=timeout) as resp2:
                                return classify_response(
                                    resp2.status, resp2.headers,
                                    resp2.read(MAX_BODY_BYTES), resp2.geturl(),
                                )
                        except Exception:
                            pass  # fall through and classify the un-followed stub below
            return classify_response(status, headers, body, final_url)
    except urllib.error.HTTPError as e:
        try:
            body = e.read(MAX_BODY_BYTES)
        except Exception:
            body = b""
        return classify_response(e.code, e.headers, body, getattr(e, "url", url))
    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, socket.timeout):
            return Attempt("timeout", None, "connection timed out")
        if isinstance(reason, socket.gaierror):
            return Attempt("dns_error", None, "DNS resolution failed")
        if isinstance(reason, ssl.SSLError):
            return Attempt("ssl_error", None, f"TLS error: {reason}")
        return Attempt("conn_error", None, f"connection failed: {reason}")
    except (socket.timeout, TimeoutError):
        return Attempt("timeout", None, "connection timed out")
    except ssl.SSLError as e:
        return Attempt("ssl_error", None, f"TLS error: {e}")
    except Exception as e:
        return Attempt("other_error", None, f"{type(e).__name__}: {e}")


def summarize(attempts):
    if any(a.category == "success" for a in attempts):
        return None

    cats = [a.category for a in attempts]
    if any(c == "parked" for c in cats):
        bucket = "parked"
    elif all(c == "gone" for c in cats):
        bucket = "gone"
    elif any(c == "blocked" for c in cats):
        bucket = "blocked"
    elif all(c in ("dns_error", "conn_error") for c in cats):
        # Formerly "dead". A refused, reset or unroutable connection is a
        # fact about the path between this runner and the host, and a
        # resolver that answers NXDOMAIN may simply be filtered. Neither
        # licenses a removal.
        bucket = "unreachable"
    elif all(c == "timeout" for c in cats):
        bucket = "timeout"
    elif all(c == "ssl_error" for c in cats):
        bucket = "tls_error"
    elif any(c == "empty" for c in cats):
        bucket = "empty"
    elif any(c == "http_error" for c in cats):
        bucket = "http_error"
    else:
        bucket = "other"

    detail = "; ".join(f"attempt {i + 1}: {a.detail}" for i, a in enumerate(attempts))
    return Verdict(bucket, detail)


# --------------------------------------------------------------------------
# Control probe
# --------------------------------------------------------------------------

# Sites that are about as close to always-up as the web gets, and that don't
# put a bot wall in front of their front page. They are checked through the
# same code path as everything else, so if they fail, the run's own
# connectivity is the problem — not 6,000 sources dying at once.
CONTROL_URLS = [
    "https://example.com",
    "https://www.wikipedia.org",
    "https://www.iana.org",
]
CONTROL_MIN_SUCCESS = 2


def run_control_probe():
    """Check the run itself before trusting anything it says about the data.

    Returns (healthy, lines). A run that cannot reach the reference sites
    cannot tell a dead source from its own broken network, which is exactly
    how v0.5.0 removed live sources.
    """
    results = []
    for url in CONTROL_URLS:
        attempt = fetch_once(url, USER_AGENTS[0], ATTEMPT_TIMEOUTS[0])
        results.append((url, attempt))
    reached = sum(1 for _, a in results if a.category == "success")
    lines = [f"- `{url}` — {a.detail}" for url, a in results]
    return reached >= CONTROL_MIN_SUCCESS, reached, lines


def check_url(url):
    attempts = []
    for i in range(len(ATTEMPT_TIMEOUTS)):
        if i > 0:
            lo, hi = RETRY_DELAYS[i]
            time.sleep(random.uniform(lo, hi))
        ua = USER_AGENTS[i % len(USER_AGENTS)]
        attempt = fetch_once(url, ua, ATTEMPT_TIMEOUTS[i])
        attempts.append(attempt)
        if attempt.category == "success":
            break
    return summarize(attempts)


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def render_report(by_url, buckets, control_healthy=True, control_reached=0, control_lines=()):
    today = dt.date.today().isoformat()
    total = sum(len(v) for v in buckets.values())
    candidates = sum(len(buckets.get(b, ())) for b in REMOVAL_CANDIDATE_BUCKETS)

    lines = [f"## Monthly link check — {today}", ""]
    lines.append(
        f"Checked {len(by_url)} unique URLs from `Fonti_OSINT.csv` and "
        f"`disinfo_sources_master.csv`. Anything that didn't succeed on the "
        f"first try was retried up to {len(ATTEMPT_TIMEOUTS)} times, with a "
        f"delay and a different browser identity each time, so a single "
        f"anti-bot block or network blip isn't reported as dead. HTTP 200 "
        f"alone isn't treated as success either — the response body is "
        f"checked for parked-domain and bot-challenge pages."
    )

    if not control_healthy:
        lines.append("")
        lines.append(
            f"> ### ⚠ This run is not valid for removals\n"
            f">\n"
            f"> Only {control_reached} of {len(CONTROL_URLS)} reference sites "
            f"could be reached, so this run cannot tell a dead source from "
            f"its own broken connectivity. Everything below is reported for "
            f"the record, and **nothing here may be used to remove a row** — "
            f"re-run from a working network first."
        )
        lines.append("")
        lines.extend(control_lines)

    if total == 0:
        lines.append("")
        lines.append("No problems found this run.")
        return "\n".join(lines)

    lines.append("")
    if not control_healthy:
        lines.append(
            "**Removal candidates: none this run** — the control probe failed "
            "(see above)."
        )
    elif candidates:
        lines.append(
            f"**{candidates} of {total} findings are removal candidates.** Only "
            f"`{'` and `'.join(sorted(REMOVAL_CANDIDATE_BUCKETS))}` qualify: a "
            f"server saying the resource does not exist, or a domain serving a "
            f"placeholder. Every other section below describes this run's own "
            f"conditions — a refused connection, a bot wall, a timeout — and "
            f"says nothing about whether the source still exists."
        )
    else:
        lines.append(
            f"**No removal candidates this run.** All {total} findings are "
            f"inconclusive: they describe this run's conditions, not the "
            f"sources."
        )

    for bucket in BUCKET_ORDER:
        entries = buckets.get(bucket)
        if not entries:
            continue
        lines.append("")
        lines.append(f"### {BUCKET_TITLES[bucket]} ({len(entries)})")
        lines.append("")
        for url, verdict in sorted(entries, key=lambda pair: pair[0]):
            refs = by_url[url]
            ref_str = ", ".join(f"`{r.dataset}:{r.line}` {r.name} ({r.column})" for r in refs)
            lines.append(f"- {ref_str} — {url}")
            lines.append(f"  {verdict.detail}")

    lines.append("")
    lines.append("---")
    lines.append(
        "Nothing above was changed automatically. Even a removal candidate "
        "is a lead, not a verdict: confirm it in a normal browser, from a "
        "network other than this run's, before editing either CSV, per "
        "CONTRIBUTING.md. Two runs of this script are not two opinions — "
        "they share this code, and in `v0.5.0` they agreed with each other "
        "and were both wrong. For `disinfo_sources_master.csv` specifically, "
        "a domain going dark is often a takedown, not something to fix."
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# GitHub issue posting (CI only)
# --------------------------------------------------------------------------

API_ROOT = "https://api.github.com"
ISSUE_LABELS = ["link-check", "data problem"]
GITHUB_BODY_LIMIT = 60_000  # issue/comment bodies are rejected past 65536


def truncate_for_github(text):
    if len(text) <= GITHUB_BODY_LIMIT:
        return text
    return (
        text[:GITHUB_BODY_LIMIT]
        + "\n\n… truncated — see the workflow run's job summary for the full list."
    )


def api_request(method, path, token, payload=None):
    url = f"{API_ROOT}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def post_to_github(repo_slug, token, report):
    owner, repo = repo_slug.split("/")
    existing = api_request(
        "GET",
        f"/repos/{owner}/{repo}/issues?state=open&labels=link-check&per_page=1",
        token,
    )
    if existing:
        number = existing[0]["number"]
        api_request(
            "POST", f"/repos/{owner}/{repo}/issues/{number}/comments", token,
            {"body": truncate_for_github(report)},
        )
        print(f"Commented on existing issue #{number}")
    else:
        intro = (
            "Opened by the monthly link-check workflow "
            "(`.github/workflows/link-check.yml`). Findings are added as a "
            "comment here every run instead of opening a new issue each "
            "month, so a URL that keeps failing across months is visible in "
            "one place.\n\n"
            "Nothing here is auto-fixed or auto-removed — every row still "
            "needs a human to confirm before editing the CSVs, per "
            "CONTRIBUTING.md.\n\n---\n\n"
        )
        created = api_request(
            "POST", f"/repos/{owner}/{repo}/issues", token,
            {
                "title": "Monthly link check — recurring findings",
                "body": truncate_for_github(intro + report),
                "labels": ISSUE_LABELS,
            },
        )
        print(f"Opened issue #{created['number']}")


# --------------------------------------------------------------------------

def main():
    print("Control probe: checking this run's own connectivity...")
    control_healthy, control_reached, control_lines = run_control_probe()
    print(f"  reached {control_reached}/{len(CONTROL_URLS)} reference sites")
    if not control_healthy:
        print("  ! degraded network — findings will be reported but flagged unusable for removals")

    by_url = load_targets()
    urls = list(by_url.keys())
    total_refs = sum(len(v) for v in by_url.values())
    print(f"Checking {len(urls)} unique URLs ({total_refs} references)...")

    buckets = defaultdict(list)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(check_url, url): url for url in urls}
        done = 0
        for future in as_completed(futures):
            url = futures[future]
            verdict = future.result()
            if verdict is not None:
                buckets[verdict.bucket].append((url, verdict))
            done += 1
            if done % 200 == 0 or done == len(urls):
                print(f"  {done}/{len(urls)} checked")

    report = render_report(by_url, buckets, control_healthy, control_reached, control_lines)
    print("\n" + report)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(report + "\n")

    total_flagged = sum(len(v) for v in buckets.values())
    if total_flagged == 0:
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    repo_slug = os.environ.get("GITHUB_REPOSITORY")
    if token and repo_slug:
        post_to_github(repo_slug, token, report)
    else:
        print(
            "\n(GITHUB_TOKEN/GITHUB_REPOSITORY not set — skipping issue "
            "creation, as expected for a local run.)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
