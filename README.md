# OSINT Sources & Disinformation Watchlist

[![Validate datasets](https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/actions/workflows/validate.yml/badge.svg)](https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/actions/workflows/validate.yml)
[![Monthly link check](https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/actions/workflows/link-check.yml/badge.svg)](https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/actions/workflows/link-check.yml)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Release](https://img.shields.io/github/v/release/Leapfrog-LSA/osint-sources-disinfo-watchlist)](https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/releases)
[![Stars](https://img.shields.io/github/stars/Leapfrog-LSA/osint-sources-disinfo-watchlist)](https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/stargazers)
[![Issues](https://img.shields.io/github/issues/Leapfrog-LSA/osint-sources-disinfo-watchlist)](https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/issues)

Two companion CSV datasets for open-source intelligence (OSINT) and due-diligence work:

- **`Fonti_OSINT.csv`** — a curated catalogue of reliable, ongoing sources (media, open data, corporate registries, sanctions/PEP lists, cybersecurity intel, etc.)
- **`disinfo_sources_master.csv`** — a watchlist of documented disinformation domains, impersonation clones, and fake-news networks

They are kept in the same repo because they're produced and maintained together as part of the same research workflow, but they serve opposite purposes: one is a "trust these" list, the other is a "watch out for these" list.

## Contents

```
Fonti_OSINT.csv              the source catalogue
disinfo_sources_master.csv   the disinformation watchlist
scripts/validate.py          checks both files; run before opening a PR
scripts/check_links.py       checks every URL still resolves; runs monthly in CI
CHANGELOG.md                 what changed, by release
CONTRIBUTING.md              conventions and data-quality rules
CITATION.cff                 citation metadata
```

Both files are UTF-8, comma-separated, with a header row and no index column. Every field is optional except `Macro-categoria`, `Sottosezione`, `Fonte` and `URL` — and, in the watchlist, `domain`, `campaign`, `source`, `evidence_level` and `cats_flag`.

```python
import pandas as pd

sources = pd.read_csv("Fonti_OSINT.csv")
italian_feeds = sources[
    sources["Paese / Area"].eq("IT") & sources["RSS Feed"].notna()
]
```

A multi-value field splits on `/`, and every token stands on its own:

```python
sources["Lingua"].str.split("/")          # "EN/FR" -> ["EN", "FR"]
sources["Paese / Area"].str.split("/")    # "GB/IE" -> ["GB", "IE"]
```

## `Fonti_OSINT.csv`

4,982 sources across 12 macro-categories:

| Category | Sources |
|---|---:|
| Media & Testate Giornalistiche | 2,104 |
| Settori Specifici (AI/dev tools, finance, sector-specific) | 1,200 |
| Open Data & Trasparenza | 472 |
| Statistiche & Dati Macroeconomici | 372 |
| Registri Aziendali & Corporate Intelligence | 257 |
| Cybersecurity & Digital OSINT | 170 |
| Geopolitica & Intelligence | 151 |
| Social Media & Media Monitoring | 79 |
| Sanzioni, PEP & Compliance | 67 |
| Sostenibilità & ESG | 46 |
| Diritti Umani & Giudiziario | 34 |
| Fact-Checking & Disinformazione | 30 |

### Columns

| Column | Contents |
|---|---|
| `Macro-categoria` | One of the 12 categories above |
| `Sottosezione` | Finer grouping within the category |
| `Fonte` | Name of the source |
| `URL` | Homepage or section entry point |
| `RSS Feed` | Feed URL, where one exists |
| `Lingua` | Publishing language(s) — see below |
| `Paese / Area` | Country or geographic scope — see below |
| `Accesso` | What it costs to use — see below |
| `Note` | Short factual context |

**`Paese / Area`** is not always a country, because not every source has one. A token is any of:

| Form | Example | Meaning |
|---|---|---|
| ISO 3166-1 alpha-2 | `IT`, `US`, `BR` | A single country |
| ISO 3166-2 style subdivision | `IT-Lombardia`, `GB-SCT`, `ES-CT` | A region within a country |
| Region label | `Globale`, `Pan-Africa`, `MENA`, `LatAm`, `Balcani` | Supranational scope, where no single country applies |

Several tokens can be joined with `/` (e.g. `GB/IE`, `IT-Puglia/IT-Basilicata`). **Every token is independently valid**, so splitting on `/` always yields parseable values — there are no bare fragments that depend on a neighbouring token for meaning.

**`Lingua`** uses uppercase ISO 639 codes (`IT`, `EN`, `AR`), joined with `/` when a source publishes in more than one (`EN/FR`, `AR/EN`). `Multi` marks broadly multilingual sources. Three-letter codes appear where no two-letter code exists (e.g. `TET` for Tetum).

**`Accesso`** is a controlled vocabulary: `Gratuito`, `Pubblico`, `Freemium`, `A pagamento`, `Open Source`, `Commerciale`, `Community`, `Premium`, `Enterprise`, `Self-hosted`, `Waitlist`.

### Field coverage

Optional fields are filled only where the value could be established from the source itself — an empty cell means "not determined", never "none".

| Field | Filled |
|---|---:|
| `Note` | 100% |
| `Paese / Area` | 89% |
| `Lingua` | 81% |
| `RSS Feed` | 22% |
| `Accesso` | 8% |

`RSS Feed` and `Accesso` are sparse largely by nature: many entries are databases, portals and tools that publish no feed and have no single access tier.

## `disinfo_sources_master.csv`

114 documented disinformation domains, two main clusters:

- **Doppelganger campaign** (51 entries) — Russian state-linked infrastructure (SDA/Structura/ANO Dialog) cloning major outlets: Bild, Der Spiegel, Süddeutsche Zeitung, Der Tagesspiegel, T-Online, Welt, FAZ, Neues Deutschland, The Guardian, Mail Online, Reuters, Fox News, ANSA, and others. Sourced from Qurium (2022) and DFRLab (2024).
- **Italian fake-news / satire network** (~60 entries) — typo-squats, hoax sites, and declared satire, sourced from BUTAC/Bufalopedia.

### Columns

| Column | Contents |
|---|---|
| `domain` | The disinformation domain itself |
| `impersonated_outlet` | Name of the outlet being imitated |
| `authentic_domain` | The real outlet's domain, or `N/A` if it imitates no one specific |
| `country` | Country targeted or hosting, same conventions as `Paese / Area` above |
| `tld` | Top-level domain |
| `first_seen` | `YYYY-MM-DD` or `YYYY`, where known |
| `campaign` | Campaign or network the entry belongs to |
| `attribution` | Who is assessed to be behind it, and by whom |
| `source` | Who documented it, with date |
| `evidence_level` | How it was established — see below |
| `cats_flag` | Classification — see below |
| `notes` | Context needed to read the row correctly |

**`evidence_level`** — `forensic` (technical/infrastructure analysis), `journalistic` (newsroom reporting), `judicial` (court or law-enforcement action), `debunker` (fact-checking organisation). Combined with `+` when more than one applies (`forensic+judicial`).

**`cats_flag`** — `disinformation_clone`, `fake_news_portal`, `fake_news_site`, `satire_recognizable`, `suspect_source`, `suspected`.

Note that `satire_recognizable` marks **declared satire** (The Onion, Lercio) — included so it can be recognised and excluded, not because it is deceptive.

## Validation

Both files are checked on every push and pull request by [`scripts/validate.py`](scripts/validate.py) — header and field count, required fields, URL format, duplicate URLs and domains, language and country codes, and the controlled vocabularies above.

Run it locally before opening a PR:

```bash
python scripts/validate.py
```

It needs no dependencies beyond the Python standard library, and reports every problem it finds with a line number rather than stopping at the first.

### Link checking

`scripts/validate.py` checks that a URL is *well-formed* — it never fetches it. Whether a source is still live is checked separately, on a schedule, by [`scripts/check_links.py`](scripts/check_links.py) via [`.github/workflows/link-check.yml`](.github/workflows/link-check.yml), because dead links accumulate silently between pushes otherwise.

Every URL in both files is fetched once a month. Two things make this different from a plain HTTP status check:

- **A single failed request doesn't mean a link is dead.** Large sites routinely block automated clients. A URL that fails is retried up to three times, spaced out with a delay and a different browser identity each time, and a response that looks like an anti-bot challenge (Cloudflare, Akamai, PerimeterX and similar) is reported separately from one that never resolves at all — the two need different follow-up.
- **HTTP 200 is not proof of life.** The response body is checked for parked-domain and for-sale pages, the same failure mode that got past a plain status check in `v0.2.0` (see [`CHANGELOG.md`](CHANGELOG.md)).

Findings are posted to a single recurring issue (label `link-check`) rather than a fresh issue every run, so a URL that keeps failing month after month is visible in one place. The workflow never edits either CSV — a flagged row still needs a human to confirm it before removing or fixing it, per [`CONTRIBUTING.md`](CONTRIBUTING.md).

Run it locally the same way:

```bash
python scripts/check_links.py
```

With no `GITHUB_TOKEN` set, it prints the findings and stops there.

## Versions

Changes are tracked in [`CHANGELOG.md`](CHANGELOG.md). Released versions are tagged, so a specific snapshot can be pinned:

```bash
git clone --branch v0.4.0 https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist.git
```

A major version bump would signal a change to the column structure or to the meaning of an existing column. Adding, correcting or reclassifying rows does not.

Filenames carry no version number — the git tag is what identifies a snapshot, so the paths above stay stable across releases.

> **Moved in v0.3.0:** the catalogue was renamed from `Fonti_OSINT_v.0.1.csv` to `Fonti_OSINT.csv`. Links to the old path resolve only up to the `v0.2.0` tag.

## License and citation

Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) — see [`LICENSE`](LICENSE). You may use, adapt, and redistribute the datasets, including commercially, as long as you credit Leapfrog-LSA / LAWARA AI.

For a ready-made citation, use the **Cite this repository** button on the repository page, or see [`CITATION.cff`](CITATION.cff).
