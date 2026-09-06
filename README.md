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

5,124 sources across 12 macro-categories:

| Category | Sources |
|---|---:|
| Media & Testate Giornalistiche | 2,105 |
| Settori Specifici (AI/dev tools, finance, sector-specific) | 1,200 |
| Open Data & Trasparenza | 473 |
| Statistiche & Dati Macroeconomici | 372 |
| Registri Aziendali & Corporate Intelligence | 257 |
| Cybersecurity & Digital OSINT | 171 |
| Geopolitica & Intelligence | 152 |
| Sanzioni, PEP & Compliance | 119 |
| Fact-Checking & Disinformazione | 116 |
| Social Media & Media Monitoring | 79 |
| Sostenibilità & ESG | 46 |
| Diritti Umani & Giudiziario | 34 |

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
| `Provenienza` | Which directory the row came from, and in which batch — see below |

**`Paese / Area`** is not always a country, because not every source has one. A token is any of:

| Form | Example | Meaning |
|---|---|---|
| ISO 3166-1 alpha-2 | `IT`, `US`, `BR` | A single country |
| ISO 3166-2 style subdivision | `IT-Lombardia`, `GB-SCT`, `ES-CT` | A region within a country |
| Region label | `Globale`, `Pan-Africa`, `MENA`, `LatAm`, `Balcani` | Supranational scope, where no single country applies |

Several tokens can be joined with `/` (e.g. `GB/IE`, `IT-Puglia/IT-Basilicata`). **Every token is independently valid**, so splitting on `/` always yields parseable values — there are no bare fragments that depend on a neighbouring token for meaning.

**`Lingua`** uses uppercase ISO 639 codes (`IT`, `EN`, `AR`), joined with `/` when a source publishes in more than one (`EN/FR`, `AR/EN`). `Multi` marks broadly multilingual sources. Three-letter codes appear where no two-letter code exists (e.g. `TET` for Tetum).

**`Accesso`** is a controlled vocabulary: `Gratuito`, `Pubblico`, `Freemium`, `A pagamento`, `Open Source`, `Commerciale`, `Community`, `Premium`, `Enterprise`, `Self-hosted`, `Waitlist`.

**`Provenienza`** records which directory a row came from and in which batch, as `<list>:<YYYY-MM>` — `ifcn:2026-08`, `opensanctions:2026-08`. `scripts/discover_candidates.py` stamps it automatically; rows added by hand leave it empty.

It exists so that a batch can be *measured* and, if it turns out to be bad, *removed in one operation*. A single directory that produces a high rate of dead links six months later is a fact you can only establish if you know which rows came from it — and a bad batch of two thousand rows cannot be undone by re-reading them one by one.

Month granularity is deliberate: the batch is the unit a review sample accepts or rejects, and the unit the monthly link check can score. A finer timestamp would split one batch into many and make both meaningless.

Empty means "not determined", as everywhere else here. The 4,986 rows that predate the column were curated by hand over time and their origin is genuinely unknown; labelling them with a guess would defeat the point of having the field.

### Field coverage

Optional fields are filled only where the value could be established from the source itself — an empty cell means "not determined", never "none".

| Field | Filled |
|---|---:|
| `Note` | 100% |
| `Paese / Area` | 89% |
| `Lingua` | 81% |
| `RSS Feed` | 21% |
| `Accesso` | 7% |

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

The same workflow runs the scripts' own test suite:

```bash
python -m unittest discover -s scripts -p "test_*.py"
```

Those 25 cases cover [`scripts/check_links.py`](scripts/check_links.py), which decides what gets proposed for removal from the catalogue. Each of the three faults that removed a live source in `v0.5.0` has a test named after the source it killed, so a failure says which row is about to be lost. They make no network requests.

### Link checking

`scripts/validate.py` checks that a URL is *well-formed* — it never fetches it. Whether a source is still live is checked separately, on a schedule, by [`scripts/check_links.py`](scripts/check_links.py) via [`.github/workflows/link-check.yml`](.github/workflows/link-check.yml), because dead links accumulate silently between pushes otherwise.

Every URL in both files is fetched once a month. Three things make this different from a plain HTTP status check:

- **A single failed request doesn't mean a link is dead.** Large sites routinely block automated clients. A URL that fails is retried up to three times, spaced out with a delay and a different browser identity each time, and a response that looks like an anti-bot challenge (Cloudflare, Akamai, PerimeterX and similar) is reported separately from one that never resolves at all — the two need different follow-up.
- **HTTP 200 is not proof of life.** The response body is checked for parked-domain and for-sale pages, the same failure mode that got past a plain status check in `v0.2.0` (see [`CHANGELOG.md`](CHANGELOG.md)).
- **Only the site may condemn the site.** A finding counts as a candidate for removal only when the server answers `404`/`410`, or the domain serves a placeholder. A refused or reset connection, a DNS failure, a timeout, a bot wall and a `200` with an empty body each get their own category and are reported as saying nothing about whether the source exists. Each run also opens with a control probe against reference sites: if those can't be reached, the run can't tell a dead source from its own broken networking, and it offers no removal candidates at all.

  This rule was added in `v0.5.1`, after `v0.5.0` removed 21 sources on the older logic. At least three were alive — among them **VERA Files**, an IFCN verified signatory — condemned by a connection reset, an empty body, and a stock web-server placeholder string. Retrying caught none of it, because the retries repeated the same request from the same network.

Findings are posted to a single recurring issue (label `link-check`) rather than a fresh issue every run, so a URL that keeps failing month after month is visible in one place. The report's header says how many findings are actually removal candidates, and whether the run was healthy enough to be believed at all. The workflow never edits either CSV — a flagged row still needs a human to confirm it, from a different network, before removing or fixing it, per [`CONTRIBUTING.md`](CONTRIBUTING.md).

Run it locally the same way:

```bash
python scripts/check_links.py
```

With no `GITHUB_TOKEN` set, it prints the findings and stops there.

### Finding new sources

[`scripts/discover_candidates.py`](scripts/discover_candidates.py) grows the catalogue without lowering the bar for what goes into it. Candidates come from an already-curated directory rather than open scraping, each is fetched for real, and `Lingua` and `Paese / Area` are filled only from a signal on the candidate's own page — an `<html lang>` attribute, a non-generic ccTLD — and left empty otherwise.

```bash
python scripts/discover_candidates.py --source ifcn
python scripts/discover_candidates.py --source opensanctions
```

Two directories are wired up: the IFCN's verified signatories, and OpenSanctions' catalogue of the official publishers it aggregates. It never touches `Fonti_OSINT.csv` — it writes a separate review file with the same columns, for a human to check and merge by hand. The OpenSanctions source in particular needs that review: its publisher list is noisy enough that a keyword filter can't carry the whole job.

One caveat worth knowing: its verification calls the same `check_url()` the link checker uses, so **a candidate it rejects has not had a second opinion**. `v0.5.0` treated a rejection here as independent corroboration of one there and dropped a live IFCN signatory on the strength of the same mistake counted twice.

## Versions

Changes are tracked in [`CHANGELOG.md`](CHANGELOG.md). Released versions are tagged, so a specific snapshot can be pinned:

```bash
git clone --branch v0.5.1 https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist.git
```

A major version bump would signal a change to the column structure or to the meaning of an existing column. Adding, correcting or reclassifying rows does not.

Filenames carry no version number — the git tag is what identifies a snapshot, so the paths above stay stable across releases.

> **Moved in v0.3.0:** the catalogue was renamed from `Fonti_OSINT_v.0.1.csv` to `Fonti_OSINT.csv`. Links to the old path resolve only up to the `v0.2.0` tag.

## License and citation

Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) — see [`LICENSE`](LICENSE). You may use, adapt, and redistribute the datasets, including commercially, as long as you credit Leapfrog-LSA / LAWARA AI.

For a ready-made citation, use the **Cite this repository** button on the repository page, or see [`CITATION.cff`](CITATION.cff).
