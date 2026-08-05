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

This runs automatically on every pull request, so it's faster to catch problems locally first. It needs no dependencies, and lists every problem with its line number in one pass.

It checks structure and vocabularies — that a country code is *well-formed*, not that it's the *right* country. Accuracy is still on you; the rules below are what the checker can't verify.

## Adding a source to `Fonti_OSINT.csv`

Columns: `Macro-categoria`, `Sottosezione`, `Fonte`, `URL`, `RSS Feed`, `Lingua`, `Paese / Area`, `Accesso`, `Note`

- **Macro-categoria / Sottosezione**: reuse an existing category if it fits; only add a new one if nothing else applies.
- **Fonte**: the source's actual name, not a generic placeholder. Add a parenthetical qualifier when the name alone is ambiguous (e.g. `Al Jazeera English` vs `Al Jazeera Africa`).
- **URL**: check it resolves before adding. No tracking parameters, no session-specific paths.
- **RSS Feed**: only fill if the feed genuinely exists — check the page's `<link rel="alternate">` tags or a known `/feed`, `/rss.xml` path.
- **Lingua / Paese / Area**: see [the README](README.md#columns) for the exact forms each accepts — `Paese / Area` takes subdivisions (`IT-Lombardia`) and region labels (`Globale`, `MENA`) as well as country codes. Only fill these when you have a real signal: the domain's ccTLD, an explicit statement on the site, or direct knowledge of the outlet. Don't default a country's official language onto every publication in it — plenty of national outlets publish in English (or another second language) for an international audience.
- **Accesso**: what it costs to use, not a content-type label. One of `Gratuito`, `Pubblico`, `Freemium`, `A pagamento`, `Open Source`, `Commerciale`, `Community`, `Premium`, `Enterprise`, `Self-hosted`, `Waitlist`.
- **Note**: short, factual context — what the source covers, notable caveats, why it's included.

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

Every URL in both files is also checked automatically once a month by [`scripts/check_links.py`](scripts/check_links.py) ([`.github/workflows/link-check.yml`](.github/workflows/link-check.yml)); findings land as a comment on a single recurring issue labelled `link-check`, not a fresh one each run. It applies the same "don't trust a single failed request, don't trust HTTP 200 either" logic described below — it only reports, it never edits a CSV. Treat a row in that issue as a lead to verify, same as a link reported manually.

## Removing entries

A source can be removed if: the URL is confirmed dead (checked more than once, ideally with different timing to rule out anti-bot false positives), it's a duplicate of another row, or it turns out not to be a genuine standalone source (e.g. a one-off article citation rather than an ongoing outlet). Note the reason in the commit message.

For `disinfo_sources_master.csv`, a domain going dark is often a takedown rather than a problem to fix — that's the point of documenting it. Don't remove a row just because the domain no longer resolves; keep it unless it's a duplicate or the entry itself was wrong.
