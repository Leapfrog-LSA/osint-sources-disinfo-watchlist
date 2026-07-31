# Changelog

All notable changes to these datasets are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions are dated; dataset releases don't carry a compatibility promise the
way software does, but a major version bump signals a change to the column
structure or to the meaning of an existing column.

## [Unreleased]

### Added

- **gNews — Ministero della Giustizia** (`gnewsonline.it`), the Italian Ministry
  of Justice's daily, with its RSS feed. Verified as the ministry's own outlet:
  `giustizia.it` embeds its content and links to it directly.

- `scripts/validate.py` and a GitHub Actions workflow that runs it on every
  push and pull request touching the data. Checks header and field count,
  required fields, URL format, duplicate URLs and domains, ISO 639 language
  tokens, ISO 3166 country codes and regions, and the controlled vocabularies
  for `Accesso`, `evidence_level` and `cats_flag`.
- Documentation of the column conventions in `README.md`: the three accepted
  forms for `Paese / Area` (country code, subdivision, region label), multiple
  values joined with `/`, and the controlled vocabularies.
- Per-field coverage figures in `README.md`, so an empty cell reads as
  "not determined" rather than "none".
- `CITATION.cff`, so the attribution required by CC BY can be generated from
  the repository page.
- Issue forms for proposing a source, proposing a disinformation domain, and
  reporting a data problem, plus a pull request template. The dropdowns offer
  exactly the vocabularies the validator accepts. The disinformation form
  requires a documenting source and evidence level, since naming a domain as
  disinformation is not a claim this list takes on suspicion alone.
- Badges for CI status, release, stars and issues.

### Fixed

- Nine `Paese / Area` values that matched none of the dataset's conventions:
  `SV_C`, `GA_C`, `SL_C` (stray `_C` suffix), `FR/LU/LU` (spurious country and
  a duplicate), `Globale/Asia`, and two rows using the bare label `Sud`.
- `IT-Calabria/Sicilia` and `IT-Puglia/Basilicata` now fully qualify both
  tokens (`IT-Calabria/IT-Sicilia`, `IT-Puglia/IT-Basilicata`), so splitting a
  multi-value field on `/` always yields independently valid values.

## [0.1.0] — 2026-07-24

Initial release.

### Added

- `Fonti_OSINT_v.0.1.csv` — 4,974 sources across 12 macro-categories, with
  columns for category, name, URL, RSS feed, language, geographic scope,
  access type and notes.
- `disinfo_sources_master.csv` — 114 documented disinformation domains,
  covering the Doppelganger impersonation clones and Italian fake-news and
  satire networks, with attribution, documenting source and evidence level.
- `README.md`, `CONTRIBUTING.md`, `LICENSE` (CC BY 4.0) and `.gitignore`.

[Unreleased]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/releases/tag/v0.1.0
