# Changelog

All notable changes to these datasets are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions are dated; dataset releases don't carry a compatibility promise the
way software does, but a major version bump signals a change to the column
structure or to the meaning of an existing column.

## [Unreleased]

### Added
- Three sources, each fetched and identified before being added:
  **Centre for Information Resilience** (`info-res.org`), **The Dial**
  (`thedial.world`) and **OsintCat** (`osintcat.net`).

  The first two come from chasing the bookmark candidates that `v0.5.1`
  recorded as unverifiable. Six of those domains turned out not to be
  blocked but simply gone — no DNS records at all, from two independent
  resolvers — because the organisations had moved. Three of the six were
  already in the catalogue under their working domains all along:
  **GITOC — Global Organized Crime Index** (`ocindex.net`), **CENOZO**
  (`cenozo.org`) and **Rise Project** (`riseproject.ro`), so the
  bookmarks were stale, not the catalogue.

  **La Lista** was dropped, and is the reason identity is checked rather
  than assumed: `lalista.com` resolves, answers `200`, and carries the
  title "La Lista" — but its own description reads "specialists in
  Italian weddings". Matching a name is not identifying a source. No
  substitute domain for it, or for `direktoro.media`, could be
  confirmed, so both stay out.

  `Lingua` and `Paese / Area` are filled only from a signal on the page.
  Centre for Information Resilience declares no `<html lang>` and sits on
  a generic TLD, so both are empty for it rather than inferred from where
  the organisation is based.

### Changed

- `scripts/validate.py` now rejects a repeated `Fonte` when nothing
  distinguishes the rows. Two sources may legitimately share a name —
  **National Bureau of Statistics** is Nigeria, Tanzania and Antigua, and
  **The Sun** is a British tabloid and a Nigerian daily — so a repeat is only
  an error when the rows carry the same `Paese / Area`, or when either is
  missing one.

  The rule was chosen by measuring it, not by intuition. The catalogue had 22
  repeated names; the check flags 5 and lets 17 through, and every one of the
  five turned out to be a real duplicate while all seventeen are namesakes in
  different countries. A bare name-collision check would have reported all 22
  and been ignored.

  The exact-URL and exact-domain checks were already there and stay. They find
  nothing today: no two rows differ only by scheme, `www.` or a trailing slash.
- **`Fonti_OSINT.csv` gains a tenth column, `Provenienza`.** It records which
  directory a row came from and in which batch, as `<list>:<YYYY-MM>`.
  `scripts/discover_candidates.py` stamps it automatically; rows added by hand
  leave it empty.

  **This changes the column structure, so the next release is a major version
  bump** — the first one this catalogue has had.

  The field exists because the catalogue cannot grow much further without it.
  Every bulk addition so far was small enough to review row by row: the IFCN
  pilot was 79 rows and was read one at a time. At a few thousand rows that
  stops being possible, and the alternative — accepting a batch on a sample —
  only works if a rejected batch can be identified and removed in one
  operation. Without provenance it cannot, so a bad directory would have to be
  unpicked by hand, which is the same problem in a worse form.

  It also makes quality measurable rather than asserted. Once the monthly link
  check has a few months of history, the dead-link rate *per batch* says which
  directories are worth using — a fact, where today there would only be an
  impression.

  138 rows are backfilled from git history rather than from guesswork:
  `ifcn:2026-08` (79), `ifcn:2026-09` (7) and `opensanctions:2026-08` (52),
  identified by the commits that introduced them. The remaining 4,986 stay
  **empty**, which here means "not determined", as it does in every other
  optional field: those rows were curated by hand over time and their origin is
  genuinely unknown. Filling them with a plausible-looking label would defeat
  the purpose of the column.

  `scripts/validate.py` rejects a malformed stamp — a bare list name with no
  batch, an impossible month, an uppercase list — while accepting an empty
  field. `scripts/test_validate.py` is new and covers those rules along with
  the requirement that `validate.py` and `discover_candidates.py` agree on the
  column list, since a drift between them would silently emit rows of the
  wrong shape.

- `README.md`'s source counts brought back in line: the catalogue now
  reads 5,124 sources, not 5,108, with six of the twelve category rows
  adjusted for the sixteen restorations and ten additions since `v0.5.1`.
  Field-coverage percentages were re-derived and are unchanged.

  Every figure was recomputed from the CSV rather than adjusted by hand,
  and the twelve category rows now sum exactly to the declared total —
  a check the table had never been held to before.

### Fixed

- Five duplicate rows resolved, all the same fault: a bulk import had added an
  organisation's **corporate site under the name of its fact-checking arm**,
  while the actual fact-check page was already in the catalogue. Four of the
  five came from the IFCN pilot — this is not something hand curation does to
  itself, and it is the failure mode the new check exists to catch.

  Removed as duplicates, each because the real page is already listed:
  **AP Fact Check** at `ap.org`, which is AP's corporate site, while
  `Associated Press` is catalogued at `apnews.com` and the genuine hub at
  `apnews.com/hub/ap-fact-check`; **EFE Verifica** at
  `efe.com/efe/espana/efeverifica/50001435`, a deep link with a numeric id to
  the same thing as `verifica.efe.com`; and **Reuters Fact Check** at
  `reutersagency.com`, whose own title reads "Reuters: The Trusted,
  International News Agency", with both `Reuters` and the real
  `reuters.com/fact-check` already present.

  Renamed, each taking the name the site gives itself rather than one invented
  here: **Tempo** at `en.tempo.co` becomes **Tempo English** (its title is
  "Tempo.co English"), and **The Canadian Press** at `thecanadianpressnews.ca`
  becomes **The Canadian Press News** (its title is "The Canadian Press News
  Home"), leaving the agency's own `thecanadianpress.com` to keep the plain
  name.
- Thirteen more sources removed in `v0.5.0` restored to `Fonti_OSINT.csv`:
  **Visão**, **World Chambers Federation (ICC)**, **Dillinger News**,
  **Department of Statistics** (Jordan), **INMETRO Brazil**, **National
  Institute of Statistics (INS)** (Romania), **Media Observatory**,
  **Office national de la statistique** (Mauritania), **Poligrafi**,
  **Statistical Office of Slovenia (SURS)**, **W3C**, **Camera di
  Commercio — Tunisia** and **Camera di Commercio — Angola**. With the
  three restored earlier, that accounts for sixteen of the twenty-one.

  Every one of these was removed on a connection-level error and nothing
  else. No server ever said the resource was gone. Under the rule now in
  `CONTRIBUTING.md` none of them was ever a candidate for removal, so
  this undoes a deletion that had no evidence behind it rather than
  asserting a new claim.

  The domains do exist. Each was resolved through two independent public
  resolvers over DNS-over-HTTPS — Google and Cloudflare — and all
  thirteen return `NOERROR` with real A records. The method was
  controlled first: an invented domain returns `NXDOMAIN` from both, live
  sites return `NOERROR`, and — the case that matters — domains this
  environment cannot reach over HTTP still resolve normally, so the
  network filtering in front of HTTP is not reaching into DNS answers.

  What DNS cannot establish is whether a host serves anything, and no
  network available here can fetch eleven of the thirteen. That gap
  closes on its own: back in the catalogue, they are checked every month
  by `scripts/check_links.py` from a runner on an unfiltered network, and
  a genuinely dead one now surfaces as `gone` with the server's own
  verdict attached. **Camera di Commercio — Angola** and **Camera di
  Commercio — Tunisia** are worth watching there: both answer `200` with
  an empty body from two separate networks, which is inconclusive by the
  same rule that a `200` with no content proves nothing.
- **Sci-Hub** (`sci-hub.se`) stays out, now on evidence rather than by
  default: both resolvers return `NXDOMAIN` for it, across `A`, `NS` and
  `SOA`. The domain has no DNS records at all — consistent with the
  seizures and rotations that domain has been through.

## [0.5.1] — 2026-09-01

### Added

- `scripts/test_check_links.py`, and a step in
  `.github/workflows/validate.yml` that runs it. Until now nothing checked
  the scripts at all: the workflow's path filter listed only `*.csv` and
  `scripts/validate.py`, so a change to `check_links.py` — the code that
  decides which sources get proposed for deletion — ran no checks
  whatsoever. The filter is now `scripts/**.py`.

  The suite is 25 cases, no network, standard library only. Each of the
  three faults that removed a live source in `v0.5.0` has a test named
  after the source it killed, so the failure message says which one is
  about to be lost again. The rest cover what must keep working: a genuine
  parked page, a redirect onto a domain-sale host, `404`/`410` as the only
  status that means gone, and a degraded control probe suppressing every
  removal candidate.

  Writing them immediately caught a real ordering bug: a very short
  placeholder page — `Buy this domain` and little else — was tested for
  emptiness before the parked marker, so it came out `empty` (inconclusive)
  instead of `parked`. That erred toward keeping rows rather than losing
  them, so it hurt nothing, but it did quietly weaken the check.

- Seven IFCN verified signatories missing from the catalogue, growing
  `Fact-Checking & Disinformazione` from 109 to 116 rows: **Cek Fakta —
  Liputan 6**, **Doble Check**, **Factchequeado.com**, **Les
  Surligneurs**, **Local Voices Media Network**, **Kashif**,
  **Provereno.Media**.

  Found by re-running the IFCN signatory list against the catalogue after
  VERA Files showed the discovery pilot's verification could not be
  trusted. `verify_candidate()` calls `check_links.check_url()`, so the
  pilot and the link checker are not two opinions but one, and a source
  the checker misjudged was rejected twice over. Of 146 verified
  signatories with a website, 11 were absent; these seven were fetched
  and answer `200` with their own content, from 144 KB (Kashif) to the
  cap.

  The other four were left out, not rejected: **Belarusian Investigative
  Center**, **INTERNEWS KOSOVA**, **Tech4Peace** answer `403` and
  **Knack Magazine** `405` — anti-bot refusals, which say nothing about
  whether the site is real. Adding them on that basis would repeat the
  error in the opposite direction.

  `Lingua` and `Paese / Area` are still filled only from a signal on the
  candidate's own page, and left empty otherwise. **Doble Check** keeps
  its own `doblecheck.cr`, which redirects to the university radio that
  hosts it, rather than the redirect target.
- Six sources found while cross-checking the maintainer's own browser
  bookmarks against the catalogue, each verified live by
  `scripts/check_links.py` before being added: **Agência Pública** (Brazilian
  investigative nonprofit), **Il Dubbio** (Italian daily), **EU Scream** (EU
  affairs newsletter/podcast), **Webz.io** (open/deep/dark web intelligence
  feed) and **Tax Justice Network — Data Portal**. The sixth, **Ojo
  Público**, is a re-addition: the bookmark pointed at `ojo-publico.com`,
  not the `ojopublico.com` removed as dead in `v0.5.0` — a different
  domain, confirmed to be the same outlet's current one by the page's own
  title and description ("OjoPúblico | Periodismo de investigación").
  `Tax Justice Network — Data Portal` (`data.taxjustice.net`) is a distinct
  URL from the organization's main site already in the catalogue
  (`taxjustice.net`, under `Settori Specifici`); both are kept pending a
  decision on whether the data portal is redundant with the parent entry.

  Seven other bookmarked sources could not be checked at all — this
  environment's outbound proxy returned a 502 on the connection itself for
  `thedial.media`, `rise.ro`, `westafricaleaks.org`, `lalista.news`,
  `direktoro.media`, `ocindex.africa` and `centreforinformationresilience.org`,
  consistently on retry, which is a sandbox-side failure rather than a
  verdict on the sites — they're left out rather than guessed at either way.
  An eighth, `osintcat.net`, returned HTTP 503 on all three attempts and
  landed in the same "blocked, not proof of death" bucket link-checking
  already uses. A ninth, `sassate.it`, resolves fine but doesn't
  self-declare as satire or fit any existing category on inspection, so it
  was left out rather than forced into `disinfo_sources_master.csv` or
  `Fonti_OSINT.csv` without the evidence either would need.

### Changed

- `scripts/check_links.py` can no longer propose removing a source over a
  network failure. A finding is a removal candidate only if the server
  answers `404`/`410`, or the domain serves a placeholder; a refused or
  reset connection, a DNS failure, a timeout, an anti-bot wall and a `200`
  with an empty body are each reported in their own category and marked as
  saying nothing about whether the source exists. The old `dead` bucket,
  which lumped connection errors in with genuine disappearance, is now
  `unreachable` and carries no such implication.

  Three specific faults are fixed, one per source wrongly removed in
  `v0.5.0`. An empty `200` body is classified `empty` rather than `parked`.
  The parked-domain check now takes the strong signal on its own — the
  request landing on a domain-sale host — while a text marker only counts
  on a page small enough to be a placeholder, so a phrase quoted inside a
  real article no longer condemns it; the marker that matched VERA Files,
  `future home of something quite cool`, is a stock web-server placeholder
  rather than a for-sale page and has been dropped entirely.

  Each run now begins with a control probe against reference sites. If it
  cannot reach them, the run cannot distinguish a dead source from its own
  broken connectivity, and the report says so at the top and offers no
  removal candidates at all. That alone would have stopped `v0.5.0`.

  `scripts/discover_candidates.py` is unchanged in behaviour but now
  documents that its `verify_candidate()` calls the same `check_url()`, so
  a rejection there is not independent corroboration of a rejection here.
  `CONTRIBUTING.md`'s removal rule is rewritten to match: it required a URL
  "checked more than once, ideally with different timing", which two runs
  from the same network satisfy while proving nothing. It now requires a
  site-level verdict, confirmation from a genuinely different vantage
  point, and a passing control probe.
- `README.md` and `CONTRIBUTING.md` brought back in line with the data and
  the tooling. The counts had drifted: the catalogue reads 5,108 sources,
  not 5,098, with `Fact-Checking & Disinformazione` at 116 rather than
  109, `Media & Testate Giornalistiche` at 2,100 and `Statistiche & Dati
  Macroeconomici` at 368. Field-coverage percentages were re-derived and
  turned out unchanged.

  The link-checking section described two rules where there are now three,
  and omitted the one that matters most — that only a verdict from the
  site itself can make a row a candidate for removal, and that a run whose
  control probe fails offers no candidates at all. Both are documented,
  with what `v0.5.0` cost when they were missing.

  Two of the four scripts were undocumented. `scripts/discover_candidates.py`
  now has a section of its own, including the caveat that it shares
  `check_url()` with the link checker and so cannot corroborate it, and
  the test suite is documented in both files with the command CI runs.

### Fixed

- Three sources removed in `v0.5.0` restored to `Fonti_OSINT.csv`: **VERA
  Files**, **Central Bank of The Gambia** and **Lanka Business Online**.
  They were never dead. Each was re-fetched and answers `200` with its own
  content — VERA Files 120 KB under the title "Truth is our business.",
  the Gambian central bank 67 KB, Lanka Business Online 120 KB after a
  redirect to `www.`, whose canonical form the row now carries.

  The `v0.5.0` entry called these removals "confirmed dead or parked by
  two independent runs of `scripts/check_links.py` on different days."
  That confirmation was not independent: both runs used the same fetch
  logic, so both reproduced the same three faults rather than checking
  each other. `Connection reset by peer` was read as a dead site when it
  is a verdict on the network path (**Central Bank of The Gambia**); a
  `200` with an empty body was read the same way, when the site merely
  redirects and the checker did not follow (**Lanka Business Online**);
  and the parked-domain heuristic matched `future home of something quite
  cool`, a stock web-server placeholder, on a live site (**VERA Files**).

  The third fault also explains a claim made twice: `v0.5.0` cited VERA
  Files as "independently confirmed dead" because the IFCN discovery
  pilot had rejected it too. It shares the fetch logic, so it failed the
  same way. VERA Files is an IFCN verified signatory — the kind of source
  this catalogue exists to hold.

  Fourteen of the other eighteen removals are still unresolved: they
  cannot be reached from the environment this restore was checked in, and
  that is not evidence either way. Only the four confirmed parked —
  **Ojo Público** (`ojopublico.com`, since re-added on its current
  domain), **Luxembourg Times**, **ReportUSA Albania**, **SupChina** —
  stay out on evidence. The fixes to `scripts/check_links.py` are not in
  this change.
- **AIDAA**'s `domain` in `disinfo_sources_master.csv` set to `N/A`, with
  the name moved into `notes` — the same treatment the six rows in
  `v0.5.0` got, and for the same reason: it names an association that
  recurs as a hoax source, not a site. It was the last row in either file
  with a person or organization name in that column.

## [0.5.0] — 2026-08-10

### Added

- 52 sanctions/AML/PEP authorities, growing `Sanzioni, PEP & Compliance`'s
  `AML, Sanzioni & PEP` subsection from 52 to 104 rows. Second pilot of
  `scripts/discover_candidates.py` (`--source opensanctions`), sourced
  from OpenSanctions' own catalogue of the official publishers it
  aggregates. That catalogue turned out to be far noisier than IFCN's:
  a first pass tagged on `list.pep` pulled in national parliaments,
  cited because their members are PEPs by holding office — 115 of 169
  such datasets' publishers were legislatures, against at most one for
  every other tag. Dropping `list.pep` (keeping the cleaner
  `list.pep.bulk`) fixed that structurally; a keyword filter catches
  the rest, but not every language (an English-only list won't stop
  a Riigikogu or a 全国人民代表大会), so this source's output was reviewed
  by hand rather than added on verification alone. Two more were
  dropped by hand from the reviewed set: `Office of Foreign Assets
  Control` pointing at the generic `treasury.gov` (redundant with the
  two OFAC rows already in the catalogue, which point at OFAC's actual
  tools) and `United States Navy` (not a plausible sanctions/PEP/AML
  source).
- 79 fact-checking organizations, growing `Fact-Checking & Disinformazione`
  from 30 to 109 rows. Discovered via `scripts/discover_candidates.py`, a
  pilot for growing the catalogue without lowering the bar for what goes
  into it: candidates come from the IFCN's own "Verified Signatory" list
  (an already-curated directory, not open scraping), each one is fetched
  for real and only kept if it resolves to actual content — of 84
  candidates not already in the catalogue, 5 were rejected as dead or
  parked, including `verafiles.org`, independently confirmed dead in the
  removal below. Language and country are filled only from a signal on
  the candidate's own page (an `<html lang>` attribute, a non-generic
  ccTLD); everything else is left empty rather than guessed. One entry,
  IFCN's plain **"Reuters"** pointing at `reutersagency.com` (their
  corporate site, not a fact-check page), was renamed **Reuters Fact
  Check** to avoid reading as a duplicate of the existing wire-service
  **Reuters** row.
- RSS feeds for **Euronews**, **Africanews**, **DW News**, **DW English** and
  **Hacker News**, which had none. Each was found by probing the domain already
  in the catalogue and confirming the response was a live feed — item count and
  most recent post date — rather than trusting the URL's shape.
- `scripts/check_links.py` and a scheduled workflow
  (`.github/workflows/link-check.yml`) that fetches every URL in both files
  once a month, since `scripts/validate.py` only checks that a URL is
  well-formed, not that it still resolves, and nothing was watching the
  over 6,000 live URLs between pushes. A failed request is retried up to three
  times with a delay and a different browser identity before being reported,
  so an anti-bot block doesn't get reported as a dead link; and a 200
  response is only accepted if the body doesn't look like a parked or
  for-sale page — the same failure mode that got past a plain status check
  in `v0.2.0` (see below). Findings land as a comment on one recurring
  issue rather than a new issue every run. The workflow only reports; it
  never edits either CSV.

### Fixed

- **RTS — Radio-televizija Srbije**'s `RSS Feed` cleared. It pointed at
  `https://rss.html` — not a real domain, but RTS's own homepage markup
  (a protocol-relative `rel=alternate` href with no host) copied verbatim.
  The real target, `https://www.rts.rs/rss.html`, exists but returns a
  completely empty RSS channel, and no working feed was found elsewhere
  on the site.
- Six rows in `disinfo_sources_master.csv` — **Associazione Agitalia**,
  **Avvocato Giacinto Canzona**, **Ermes Maiolica**, **Lorenzo Croce**,
  **Proto Group**, **Senatore Cirenga** — had a person or
  organization name in `domain` instead of a domain. Reading their
  `notes`, none are clone/typo-squat sites; they document recurring hoax
  subjects and personas from BUTAC/Bufalopedia (e.g. "Senatore Cirenga"
  is the fictional senator from the "emendamento Cirenga" hoax), which
  is worth keeping but isn't what `domain` means. `domain` is now `N/A`,
  matching the convention `authentic_domain` already uses for "no
  specific target," and the name moved into `notes`.
  `scripts/validate.py`'s duplicate-domain check now exempts `N/A`, the
  same way an empty field already is — six rows sharing that literal
  value was never a real collision.

### Removed

- 21 sources from `Fonti_OSINT.csv`, confirmed dead or parked by two
  independent runs of `scripts/check_links.py` on different days —
  `scripts/validate.py` had no way to catch these, since a parked-domain
  page or an empty government portal still returns HTTP 200:
  **Sci-Hub**, **Visão**, **World Chambers Federation (ICC)**,
  **Central Bank of The Gambia**, **Dillinger News**, **Department of
  Statistics** (Jordan), **INMETRO Brazil**, **National Institute of
  Statistics (INS)** (Romania), **Media Observatory**, **Office
  national de la statistique** (Mauritania), **Poligrafi**,
  **Statistical Office of Slovenia (SURS)**, **W3C**, **Camera di
  Commercio — Tunisia**, **Camera di Commercio — Angola**, **Lanka
  Business Online**, **Luxembourg Times**, **Ojo Público**, **SupChina**,
  **VERA Files**, **ReportUSA Albania**.

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

[Unreleased]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/releases/tag/v0.1.0
