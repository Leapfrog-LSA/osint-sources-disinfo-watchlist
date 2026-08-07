#!/usr/bin/env python3
"""
Discover new-source candidates from a known directory and verify them
before a human reviews them for Fonti_OSINT.csv.

Run locally:

    python scripts/discover_candidates.py --source ifcn
    python scripts/discover_candidates.py --source opensanctions

Two directories piloted so far: the IFCN's verified fact-checking
signatories (Fact-Checking & Disinformazione), and OpenSanctions' own
catalogue of the official sources it aggregates (AML, Sanzioni & PEP).
It never writes to Fonti_OSINT.csv — it writes a review file with the
same columns, for a human to check and merge by hand, same as every
other change in this repo.

The two sources are not equally clean. IFCN's "Verified Signatory"
status is a single-purpose accreditation — everything that clears it
is, by construction, a fact-checker. OpenSanctions' publisher records
serve OpenSanctions' own citation needs: alongside FIUs and sanctions
authorities, "official" publishers include national parliaments (cited
because their members are PEPs by virtue of holding office), which
don't belong in a compliance-sources list. A keyword filter catches
English-language legislature names; it does not catch a Chinese
People's Congress or an Estonian Riigikogu. For --source opensanctions
specifically, review the output by hand before merging any of it —
don't extend this pilot's "verify then add" pattern to it without
that check.

Three checks before a candidate reaches the review file:

1. Already in the catalogue? Compared by normalised domain, not exact URL,
   so http/https and www. differences don't produce false "new" rows.
2. Actually alive? Reuses scripts/check_links.py's real fetch-and-classify
   logic — a listing in an external directory doesn't mean the site still
   resolves, and HTTP 200 doesn't mean the page has real content either.
3. Any field we can't verify from the source itself (language, country)
   is left empty rather than guessed, per CONTRIBUTING.md.

Standard library only — no dependencies to install.
"""

import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_links as cl  # noqa: E402 — reuse its opener, retry logic and classifier

REPO = Path(__file__).resolve().parent.parent
OSINT_CSV = REPO / "Fonti_OSINT.csv"

OSINT_COLUMNS = [
    "Macro-categoria", "Sottosezione", "Fonte", "URL",
    "RSS Feed", "Lingua", "Paese / Area", "Accesso", "Note",
]

IFCN_API = "https://ifcn-cop-prod-server-8q9x7.ondigitalocean.app/api/organization/signatories"

OPENSANCTIONS_INDEX = "https://data.opensanctions.org/datasets/latest/index.json"
OPENSANCTIONS_TAGS = {
    "list.pep", "list.pep.bulk", "list.sanction", "list.sanction.counter",
    "list.sanction.eu", "list.wanted", "list.debarment", "list.enforcement",
}
# Best-effort only — catches common English legislature names, not every
# language. --source opensanctions output needs a human pass regardless.
LEGISLATURE_KEYWORDS = [
    "parliament", "senate", "congress", "assembly", "chamber", "camera",
    "cámara", "camara", "chambre", "bundestag", "bundesrat", "duma",
    "riksdag", "sejm", "seimas", "saeima", "folketing", "eduskunta",
    "althingi", "knesset", "oireachtas", "cortes", "majlis", "meclis",
    "kenesh", "khural", "rada", "sabor", "nationalrat", "landtag",
    "legislative", "diet", "shura", "mejlis", "jogorku", "verkhovna",
    "stortinget", "house of representatives", "house of commons",
    "national assembly", "supreme council",
]

SOURCES = {
    "ifcn": {
        "macro": "✅ Fact-Checking & Disinformazione",
        "sottosezione": "Fact-Checking & Disinformazione",
        "note": "Fact-checker (rete IFCN) · verifica consigliata",
    },
    "opensanctions": {
        "macro": "⚖️ Sanzioni, PEP & Compliance",
        "sottosezione": "AML, Sanzioni & PEP",
        "note": "Fonte ufficiale citata da OpenSanctions · verifica consigliata prima del merge",
    },
}

# ccTLDs that are widely used as generic/brand domains rather than a real
# country signal — excluded so a ".io" or ".me" site doesn't get a wrong
# country guess. Not exhaustive; err on the side of leaving Paese / Area
# empty when in doubt.
GENERIC_TLDS = {
    "com", "org", "net", "info", "app", "dev", "io", "me", "tv", "co",
    "cc", "biz", "name", "pro", "online", "site", "xyz",
}

LANG_TAG_RE = re.compile(r'<html[^>]+lang=["\']([a-zA-Z]{2})', re.IGNORECASE)


def normalize_domain(url_str):
    u = (url_str or "").strip()
    if not u:
        return None
    if not u.lower().startswith(("http://", "https://")):
        u = "https://" + u
    host = urlparse(u).netloc.lower()
    if not host:
        return None
    return host[4:] if host.startswith("www.") else host


def load_existing_domains():
    domains = set()
    with OSINT_CSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            d = normalize_domain(row.get("URL", ""))
            if d:
                domains.add(d)
    return domains


def fetch_ifcn_candidates():
    req = urllib.request.Request(
        IFCN_API,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    candidates = []
    for org in data.get("organizations", []):
        if org.get("signatory_status") != "Verified Signatory":
            continue
        name = (org.get("name") or "").strip()
        owner = org.get("organization_owner") or {}
        site = (owner.get("website") or "").strip()
        if not name or not site:
            continue
        url = site if site.lower().startswith(("http://", "https://")) else "https://" + site
        parsed = urlparse(url)
        url = parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower()).geturl()
        candidates.append({"name": name, "url": url})
    return candidates


def detect_language(url):
    """Best-effort: only trust an explicit <html lang> from the page itself."""
    try:
        req = cl._request(url, cl.USER_AGENTS[0])
        with cl.OPENER.open(req, timeout=12) as resp:
            body = resp.read(20_000).decode("utf-8", errors="replace")
    except Exception:
        return ""
    match = LANG_TAG_RE.search(body)
    if not match:
        return ""
    lang = match.group(1).upper()
    return lang if len(lang) == 2 else ""


def detect_country(url):
    """Best-effort: only a ccTLD that isn't in generic/repurposed use."""
    host = normalize_domain(url) or ""
    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    if len(tld) == 2 and tld not in GENERIC_TLDS:
        return tld.upper()
    return ""


def is_legislature(name):
    lowered = name.lower()
    return any(keyword in lowered for keyword in LEGISLATURE_KEYWORDS)


def fetch_opensanctions_candidates():
    req = urllib.request.Request(
        OPENSANCTIONS_INDEX,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    seen_urls = set()
    candidates = []
    for dataset in data.get("datasets", []):
        if not (set(dataset.get("tags", [])) & OPENSANCTIONS_TAGS):
            continue
        publisher = dataset.get("publisher") or {}
        if not publisher.get("official"):
            continue
        name = (publisher.get("name_en") or publisher.get("name") or "").strip()
        site = (publisher.get("url") or "").strip()
        if not name or not site or is_legislature(name):
            continue
        parsed = urlparse(site)
        url = parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower()).geturl()
        if url.lower() in seen_urls:
            continue
        seen_urls.add(url.lower())
        country = (publisher.get("country") or "").strip().upper()
        if len(country) != 2:  # e.g. "zz" (multilateral) or blank — not a real country code
            country = ""
        candidates.append({"name": name, "url": url, "country": country})
    return candidates


def verify_candidate(candidate, source_config):
    verdict = cl.check_url(candidate["url"])
    if verdict is not None:
        return None  # dead, parked, blocked, or otherwise unverified — not proof of life
    return {
        "Macro-categoria": source_config["macro"],
        "Sottosezione": source_config["sottosezione"],
        "Fonte": candidate["name"],
        "URL": candidate["url"],
        "RSS Feed": "",
        "Lingua": detect_language(candidate["url"]),
        "Paese / Area": candidate.get("country") or detect_country(candidate["url"]),
        "Accesso": "",
        "Note": source_config["note"],
    }


FETCHERS = {
    "ifcn": fetch_ifcn_candidates,
    "opensanctions": fetch_opensanctions_candidates,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(SOURCES), default="ifcn")
    parser.add_argument("--out", default=None)
    parser.add_argument("--limit", type=int, default=None, help="cap candidates checked, for a quick run")
    args = parser.parse_args()

    source_config = SOURCES[args.source]
    out_path = Path(args.out) if args.out else REPO / f"candidates_{args.source}_review.csv"

    print(f"Fetching candidates from {args.source}...")
    all_candidates = FETCHERS[args.source]()
    print(f"  {len(all_candidates)} candidates")

    existing = load_existing_domains()
    new_candidates = [c for c in all_candidates if normalize_domain(c["url"]) not in existing]
    print(f"  {len(new_candidates)} not already in Fonti_OSINT.csv (by domain)")

    if args.limit:
        new_candidates = new_candidates[: args.limit]

    print(f"Verifying {len(new_candidates)} candidates (this fetches each site for real)...")
    accepted = []
    for i, candidate in enumerate(new_candidates, 1):
        row = verify_candidate(candidate, source_config)
        if row:
            accepted.append(row)
        if i % 20 == 0 or i == len(new_candidates):
            print(f"  {i}/{len(new_candidates)} checked, {len(accepted)} verified alive")

    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OSINT_COLUMNS)
        writer.writeheader()
        writer.writerows(accepted)

    print(f"\n{len(accepted)} candidates verified alive, written to {out_path}")
    print("Nothing was added to Fonti_OSINT.csv — review the file above before merging any of it.")


if __name__ == "__main__":
    main()
