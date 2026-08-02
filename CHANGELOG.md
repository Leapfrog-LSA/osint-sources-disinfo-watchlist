# Changelog

All notable changes to these datasets are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions are dated; dataset releases don't carry a compatibility promise the
way software does, but a major version bump signals a change to the column
structure or to the meaning of an existing column.

## [Unreleased]

### Added

- RSS feeds for **Euronews**, **Africanews**, **DW News**, **DW English** and
  **Hacker News**, which had none. Each was found by probing the domain already
  in the catalogue and confirming the response was a live feed — item count and
  most recent post date — rather than trusting the URL's shape.

## [0.4.0] — 2026-08-01

### Changed

- Twenty-five outlets now state how they are owned or funded in their `Note`.
  The catalogue already used this convention for 134 rows (`agenzia di stato`,
  `pubblica`, `USA governo`); these were the significant omissions — RT, Press
  TV, CGTN, Xinhua, Al Jazeera, RFI and RFE/RL all carried only a country name.

  Ownership was verified per outlet rather than assumed from the country, which
  mattered: **i24NEWS** is privately held by Altice (Patrick Drahi), **Kompas**
  by Kompas Gramedia, **Saudi Gazette** by the Okaz Organization and **Gulf
  News** by Al Nisr Publishing — labelling any of them state media would have
  been false. Conversely **Arab News** is not simply private: its publisher
  SRMG is controlled through funds tracing to the Saudi sovereign wealth fund.

  The notes keep three distinctions the catalogue already made, because
  collapsing them would misinform: an organ of the state (Xinhua), a public
  broadcaster with statutory independence (RFI, RFE/RL), and a private outlet
  aligned with power. Where ownership rests on investigative reporting rather
  than public record — Egypt Today and Youm7, traced to intelligence-linked
  vehicles — the note attributes the claim to Reporters Without Borders' Media
  Ownership Monitor instead of asserting it.

### Added

- Three chamber federations: **AACCLA** (the AmChams' own federation for Latin
  America and the Caribbean), **FGCCC** (Federation of GCC Chambers) and
  **EBO Worldwide Network**.

### Fixed

- The row named **GCC Chambers** pointed at `gcc-sg.org`, which is the
  Secretariat General of the Gulf Cooperation Council — an intergovernmental
  body, not a chamber federation. Renamed to `GCC — Segretariato Generale`
  and its note corrected. The actual federation, `fgccc.org`, is now listed
  separately.

## [0.3.0] — 2026-07-31

### Changed

- **Renamed `Fonti_OSINT_v.0.1.csv` to `Fonti_OSINT.csv`.** The old name carried
  a version that never moved, so a `v0.2.0` checkout still shipped a file called
  `…v.0.1.csv`. The git tag identifies a snapshot; the filename no longer
  pretends to. Filenames are now stable across releases.

  **This breaks direct links to the old path.** Anything fetching the raw file
  needs the new name, or can pin the `v0.2.0` tag to keep the old one.

## [0.2.0] — 2026-07-31

Column structure is unchanged, so anything reading the previous release keeps
working. What changed is the content, plus tooling to keep it honest.

### Added

- **gNews — Ministero della Giustizia** (`gnewsonline.it`), the Italian Ministry
  of Justice's daily, with its RSS feed. Verified as the ministry's own outlet:
  `giustizia.it` embeds its content and links to it directly.
- Four AACCLA member chambers: **AmCham Honduras**, **AmCham Jamaica**,
  **AmCham Peru** and **VenAmCham** (Venezuela). Distinct from the national
  chambers already listed for Peru and Venezuela.

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

### Changed

- Moved 28 Middle Eastern outlets from the `Africa` subsection to
  `Medio Oriente & Nord Africa (MENA)` — Lebanese, Jordanian, Syrian, Iranian,
  Iraqi, Gulf, Israeli and Palestinian titles that had no African remit.
  Publications that *cover* Africa from elsewhere (Jeune Afrique, Le Monde
  Afrique, TRT Africa, Al Jazeera Africa and others) stay under `Africa`:
  the subsection tracks editorial focus, not where a title is published.

### Fixed

- **AmCham Mexico** pointed at `amcham.com`, a parked domain advertising itself
  as for sale, rather than the chamber. Corrected to `amcham.org.mx`. The row
  looked healthy — the URL was well-formed and returned HTTP 200 — which is why
  automated link checking alone doesn't catch this class of error.
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

[Unreleased]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/releases/tag/v0.1.0
