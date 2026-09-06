# Contributing

Both datasets in this repo are only as useful as they are accurate. The rules below exist to keep it that way — please read before opening a pull request.

## Ground rules

- **Never invent data.** If a field can't be verified (country, language, access type, attribution...), leave it empty rather than guess. An empty cell is honest; a wrong one silently misleads everyone downstream.
- **One change, one purpose.** Keep PRs focused — adding sources, fixing a field, removing dead links. Don't mix unrelated edits.
- **Cite where it matters.** For `disinfo_sources_master.csv` especially, every row needs a real `source` and `evidence_level` — no unverified claims about a domain being malicious/disinformation.

## Check your changes before opening a PR

```bash
python scripts/validate.py
```

This runs automatically on any pull request touching a CSV or a script, so it's faster to catch problems locally first. It needs no dependencies, and lists every problem with its line number in one pass.

It checks structure and vocabularies — that a country code is *well-formed*, not that it's the *right* country. Accuracy is still on you; the rules below are what the checker can't verify.

If you changed anything under `scripts/`, run the tests too — the same workflow does:

```bash
python -m unittest discover -s scripts -p "test_*.py"
```

## Adding a source to `Fonti_OSINT.csv`

Columns: `Macro-categoria`, `Sottosezione`, `Fonte`, `URL`, `RSS Feed`, `Lingua`, `Paese / Area`, `Accesso`, `Note`, `Provenienza`

- **Macro-categoria / Sottosezione**: reuse an existing category if it fits; only add a new one if nothing else applies.
- **Fonte**: the source's actual name, not a generic placeholder. Add a parenthetical qualifier when the name alone is ambiguous (e.g. `Al Jazeera English` vs `Al Jazeera Africa`).

  Two rows may share a name, but only when something tells them apart: `National Bureau of Statistics` is Nigeria, Tanzania and Antigua, and `The Sun` is both a British tabloid and a Nigerian daily. `scripts/validate.py` allows that when the rows carry different `Paese / Area` values, and rejects it otherwise — same country, or a country missing on either side, reads as one source entered twice. If a repeat is flagged and the sources really are different, give each its country; if they are the same source, merge them rather than renaming one to slip past the check.
- **URL**: check it resolves before adding. No tracking parameters, no session-specific paths.
- **RSS Feed**: only fill if the feed genuinely exists — check the page's `<link rel="alternate">` tags or a known `/feed`, `/rss.xml` path.
- **Lingua / Paese / Area**: see [the README](README.md#columns) for the exact forms each accepts — `Paese / Area` takes subdivisions (`IT-Lombardia`) and region labels (`Globale`, `MENA`) as well as country codes. Only fill these when you have a real signal: the domain's ccTLD, an explicit statement on the site, or direct knowledge of the outlet. Don't default a country's official language onto every publication in it — plenty of national outlets publish in English (or another second language) for an international audience.
- **Accesso**: what it costs to use, not a content-type label. One of `Gratuito`, `Pubblico`, `Freemium`, `A pagamento`, `Open Source`, `Commerciale`, `Community`, `Premium`, `Enterprise`, `Self-hosted`, `Waitlist`.
- **Note**: short, factual context — what the source covers, notable caveats, why it's included.
- **Provenienza**: **leave it empty** when adding by hand. It records which directory a batch of rows came from, as `<list>:<YYYY-MM>`, and [`scripts/discover_candidates.py`](scripts/discover_candidates.py) fills it automatically for the rows it produces. Its purpose is to make a batch measurable and reversible, so putting a value there by hand — or copying one from a neighbouring row — makes a batch look bigger than it was and quietly corrupts both.

## Adding an entry to `disinfo_sources_master.csv`

Columns: `domain`, `impersonated_outlet`, `authentic_domain`, `country`, `tld`, `first_seen`, `campaign`, `attribution`, `source`, `evidence_level`, `cats_flag`, `notes`

- **domain**: the disinformation/clone domain itself, not the outlet it imitates.
- **authentic_domain**: the real outlet's domain, if this is an impersonation. `N/A` if it isn't imitating anyone specific.
- **evidence_level**: how the entry was established — `forensic` (technical/infrastructure analysis, e.g. Qurium), `journalistic` (reported by a newsroom), `judicial` (court/law-enforcement action), `debunker` (fact-checking organization). Don't add an entry you can't back with at least one of these.
- **cats_flag**: the classification — see [the README](README.md#columns-1) for the full list. Use `satire_recognizable` for declared satire and `suspected` when the attribution itself is weak; don't reach for `disinformation_clone` unless the entry really impersonates a specific outlet.
- **attribution**: who's assessed to be behind it, and by whom — attribute the claim, don't state it as fact if the source itself calls it unconfirmed (see the existing `Doppelganger (linked)` row for how to flag weak attribution).
- **notes**: anything a reader needs to correctly interpret the row — geo-fencing, takedown status, why the typo-squat pattern was flagged, etc.

## Reporting problems

Dead link, wrong category, duplicate entry, outdated attribution — open an issue or a PR with the fix. If you're removing something, say why in the PR/commit description.

Every URL in both files is also checked automatically once a month by [`scripts/check_links.py`](scripts/check_links.py) ([`.github/workflows/link-check.yml`](.github/workflows/link-check.yml)); findings land as a comment on a single recurring issue labelled `link-check`, not a fresh one each run. It applies the same "don't trust a single failed request, don't trust HTTP 200 either" logic described below — it only reports, it never edits a CSV. Treat a row in that issue as a lead to verify, same as a link reported manually, and read the report's own header: it says how many findings are actually removal candidates, and whether the run was healthy enough to be believed at all.

## Removing entries

A source can be removed if it's a duplicate of another row, it turns out not to be a genuine standalone source (e.g. a one-off article citation rather than an ongoing outlet), or **the site itself gives a verdict that it is gone**. Note the reason in the commit message.

That last one is narrow on purpose. Only two findings count:

- the server answers **404 or 410** — it is telling you the resource does not exist;
- the domain serves a **placeholder**: it lands on a domain-sale service, or a small page whose text says it is for sale, parked, expired or suspended.

Everything else describes the connection, not the source, and **can never justify a removal**: a refused, reset or unroutable connection, a DNS failure, a timeout, an anti-bot wall (403/429/503, a CAPTCHA or challenge page), a `200` with an empty body. Those mean *you couldn't see the site*, which is not the same as the site being gone. `scripts/check_links.py` sorts its findings into exactly these categories and marks which ones are removal candidates; the rest are leads for a human, nothing more.

Two further rules before you delete a row:

1. **Confirm from a different network.** Two runs of `check_links.py` are not two opinions — they run the same code, and repeating a request from the same place reproduces the same failure. "Independent" means a genuinely different vantage point: your own browser on a normal connection, not a second CI run an hour later. `scripts/discover_candidates.py` calls `check_url()` too, so a rejection there is the *same* opinion as well, not corroboration.
2. **A control probe must have passed.** If the run couldn't reach its reference sites, it couldn't tell a dead source from its own broken networking, and its findings are unusable for removals. The report says so at the top when this happens.

This is not hypothetical caution. `v0.5.0` removed 21 sources under the older, looser version of this rule — "checked more than once, with different timing". At least three were alive and had to be restored, among them **VERA Files**, an IFCN verified signatory: one was condemned by a `Connection reset by peer`, one by an empty body from a site serving 120 KB to a browser, one by a stock web-server placeholder string. The retries agreed each time, because they were the same request from the same network.

For `disinfo_sources_master.csv`, a domain going dark is often a takedown rather than a problem to fix — that's the point of documenting it. Don't remove a row just because the domain no longer resolves; keep it unless it's a duplicate or the entry itself was wrong.
