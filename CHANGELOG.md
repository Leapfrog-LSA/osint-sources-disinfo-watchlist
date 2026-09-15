# Changelog

All notable changes to these datasets are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions are dated; dataset releases don't carry a compatibility promise the
way software does, but a major version bump signals a change to the column
structure or to the meaning of an existing column.

## [Unreleased]

### Added

- `scripts/sample_batch.py`, which draws the review sample for one batch of
  imported sources, and the acceptance rule to go with it in
  `CONTRIBUTING.md`.

  It replaces reading every imported row, which is what the first two imports
  got and what stops being possible past a few hundred rows. A batch is now
  accepted on a sample instead — and **rejected whole if the sample turns up a
  single defect**, rather than repaired row by row. The directory that produced
  a bad row produced the ones nobody read, so fixing only what was seen leaves
  the rest and buys false confidence.

  Two properties make that honest rather than a formality. The draw is seeded
  from the batch id, so it is a function of the batch and not of when it was
  asked for: nobody can re-roll until the sample looks clean, and a second
  reviewer sees exactly the rows the first one saw. And a batch smaller than
  the sample size is returned whole, so a small import is never signed off on a
  partial read.

  The threshold is zero defects in 60 rows, which by the rule of three puts the
  true defect rate under about 5% with 95% confidence. That is the honest
  reading, and `CONTRIBUTING.md` states it that way rather than implying a
  clean sample means a clean batch. A single defect already weakens it to
  roughly 8% — and every defect found in this catalogue so far was one no
  reviewer would knowingly accept, so there is no sensible number to tolerate.

  What counts as a defect is deliberately narrow and matches the rules already
  in `CONTRIBUTING.md`: the URL does not identify the source it claims to be,
  the row duplicates one already present, or a field carries an unverified
  value. A source the reviewer would not personally have chosen is not a
  defect — that belongs to the directory's inclusion criteria, settled before
  importing.

  Writing the tests caught a real defect in the sampler: an empty batch id
  matched every unstamped row, so `--batch ""` would have presented the
  thousands of rows that predate the `Provenienza` column as a single import
  to sign off on.
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

- **24 national statistics offices**, closing most of the gap in
  `Istituti di Statistica Nazionali`. The subsection covered 156 of the 193 UN
  member states and now covers 180.

  The starting list was wrong in one place and worth saying so: Italy was
  counted as missing, but **ISTAT has been in the catalogue all along**,
  filed under `Istituzioni, Trasparenza & Open Government`. That is a
  classification question, not a gap, and it leaves 36 real ones.

  Every row was fetched and read before being added — not for a `200`, but
  for the name the page gives itself. Six of the URLs the UNSD directory
  supplies failed exactly that test:

  | Country | URL in the directory | What it actually serves |
  |---|---|---|
  | Marshall Islands | `rmiembassyus.org` | the embassy in Washington |
  | Haiti | `ihsi.ht` | redirects to `znaki.fm`, an unrelated domain |
  | Nauru, Tonga, Tuvalu, Vanuatu | `spc.int/prism/…` | one shared regional page — the same document for all four |

  All six answered `200` with a full page. A liveness check would have admitted
  every one of them, and the four Pacific entries would have become four rows
  pointing at the same document.

  A working URL was found for all six, so none of the countries was lost:
  Haiti's IHSI at `ihsi.gouv.ht`, the Marshall Islands' EPPSO at
  `rmieppso.org`, and the four Pacific offices on their own domains —
  `stats.gov.nr`, `tongastats.gov.to`, `stats.gov.tv` and `vnso.gov.vu`.

  `Provenienza` distinguishes where each URL came from, because the two
  directories used are not equally reliable and their yield should be
  measured separately: `unsd:2026-09` (8 rows) for the UNSD directory of
  national statistical offices, `wikipedia.nso:2026-09` (12) for the
  Wikipedia list, and **empty** for the four found by hand, as
  `CONTRIBUTING.md` prescribes for entries added one at a time. UNSD is the
  official source and was tried first; it is also the one carrying all six
  misidentifications above, which is the sort of thing the column exists to
  record.

  **Twelve countries are still missing, and none of them were guessed at.**
  Eritrea and North Korea have no published site at all. Bahrain, Costa Rica,
  Ethiopia, Iran, Lithuania, Palau, South Sudan, Sudan, Eswatini and Venezuela
  have a URL that could not be verified from here — DNS `SERVFAIL`, a
  Cloudflare challenge, an empty page, or a blocked egress — and a source that
  cannot be identified does not get added on the strength of a plausible name.
  Italy is the classification question above.

  Two rows carry a caveat in `Note` rather than being quietly dropped: Kenya's
  KNBS and Vanuatu's VBoS serve an incomplete TLS certificate chain, so the
  monthly check will report them as `tls_error`. `CONTRIBUTING.md` already
  says a TLS error is never grounds for removal; this makes the reason legible
  before someone acts on the report.

  Both batches are under the sample size, so `scripts/sample_batch.py` returns
  them whole and the sample *is* the full review — which is why a batch this
  small was chosen first. `README.md`'s counts were recomputed from the file:
  5,145 sources, `Statistiche & Dati Macroeconomici` 396, and
  `Fact-Checking & Disinformazione` corrected to 113, which had been left at
  116 after the duplicate removals. `Lingua` coverage ticks from 81% to 82%:
  every new row declares one.

- **29 investigative newsrooms from the OCCRP network**, in
  `Giornalismo Investigativo` — the first batch drawn from a professional
  network rather than an institutional register.

  The plan for growing this catalogue says to *measure* a network's yield
  before working it, instead of assuming one. Measured, OCCRP's global
  network page lists **75 organisations, of which the catalogue already held
  45** — a 40% yield, close to the IFCN pilot's 54% (79 of 146). The
  overlap is itself worth knowing: it says the existing hand-curated
  coverage of investigative journalism was already good, and that the value
  of the network is the tail, not the middle.

  30 candidates were left. **One was rejected**: the Belarusian
  Investigative Center (`investigatebel.org`) answers a Cloudflare challenge
  rather than a page, so its identity could not be confirmed from here. It
  is a blocked read, not a dead site, and it is left out rather than
  admitted on the strength of the directory's word.

  The other 29 were each fetched and read. Where the network's link pointed
  at a section — `/en/`, `/ro/`, an `about` page — the row records the
  homepage that section resolves to, verified separately. `Lingua` comes
  from the page and not from the country: four sites declare an `<html lang>`
  their own content contradicts (an Albanian outlet declaring `en`, a Syrian
  one declaring `en-US`, a Georgian one declaring the non-existent code
  `ge`), so the declared value was used only where the content agreed with
  it. A second language is recorded only where that version was fetched and
  found to exist — nine of the twenty-nine.

  19 of the 29 rows carry a feed, each one requested and confirmed to return
  a feed rather than a page — which caught a near-miss: the feed one site
  advertises in its `<head>` is a WordPress *page* comment feed, not the
  site feed, and only the fetch tells them apart. The site feed was found
  and verified separately. The 29 rows span 23 countries, fifteen of them
  places `Giornalismo Investigativo` had no outlet for at all — Albania,
  Austria, Azerbaijan, Bosnia, Belarus, Cyprus, Georgia, Ghana, Moldova,
  Malta, Papua New Guinea, the Solomon Islands, Syria, Togo and Kosovo.

  Batch `occrp:2026-09`. At 29 rows it sits under the sample size, so
  `scripts/sample_batch.py` returns it whole and the sample is again the
  full review — zero defects.

- **Two more networks measured, neither imported yet**, because the point of
  measuring first is to know what a batch is worth before committing to it.

  | Network | Listed | Already catalogued | Candidates | Yield |
  |---|---:|---:|---:|---:|
  | OCCRP | 75 | 45 | 30 | 40% |
  | FIRST.org | 878 | — | 83 | 9% |
  | GIJN | — | — | — | not reachable |

  **FIRST.org's 878 member teams are mostly private.** 489 declare a
  commercial, industrial, financial, ISP or vendor constituency and 286
  serve only their own host organisation, so the headline number is not the
  yield: the part that belongs in an OSINT catalogue is the national CERTs,
  and FIRST's own metadata does not label them. Filtering on a governmental
  host organisation with an external constituency leaves 91, of which 8 are
  already catalogued — **83 candidates, a 9% yield**, and the filter still
  admits a few corporate teams that a review would have to remove. That is a
  workable batch, but a separate one.

  **GIJN could not be measured at all.** Every path on `gijn.org` — the
  member list, the API, even `robots.txt` — answers `403` from this network,
  so there is nothing to report except that. Recording it as unmeasured is
  the point: an estimate here would be exactly the invented number the plan
  was written to avoid.

- **40 national CERT and CSIRT teams** from the FIRST.org directory, in
  `Threat Intelligence & Cybersecurity`, as batch `first:2026-09`.

  **The measured yield was 83 candidates; 40 survived being read.** That gap
  is the finding, not a disappointment: a filter measured on metadata counts
  rows that *look* like national CERTs, and the previous entry said as much —
  "the filter still admits a few corporate teams that a review would have to
  remove". It admitted more than a few, and in a shape metadata could not
  show.

  FIRST publishes a host organisation and a constituency type for each of its
  883 member teams, and both are self-declared. Filtering on a governmental
  host with an external constituency is the best either field supports, and it
  still lets through a vendor (`cyberteq.com`, a commercial security firm
  listed under "Ghana Cybersecurity Authority"), a state telecom operator's
  own CSIRT, a public-procurement authority, and several teams whose declared
  "website" is not the team's page at all but their parent ministry's front
  door — Costa Rica's `micitt.go.cr`, Ukraine's `mod.gov.ua`, Singapore's
  `tech.gov.sg`, Bangladesh's `bppa.gov.bd`. Each of those answers `200` with
  a real government page. **Only reading them separates a CERT from the
  ministry that houses one.**

  So the rule applied here is the identity rule, sharpened for this batch:
  **the page has to identify the CERT, not merely its parent.** 8 candidates
  failed it outright, and 33 could not be read at all — Cloudflare and Akamai
  challenges (`ccb.belgium.be`, `nksc.lt`, `csirt.gob.cl`, `ccn-cert.cni.es`),
  DNS or TLS failures (`aecert.ae`, `cirt.org.bw`, `cicert.ci`, `cert.gov.ng`),
  a 160-byte empty page (`cert.dga.gov.ge`), a stale redirect into a 404
  (INCIBE-CERT). They are blocked reads, not dead sites, and none of them is
  in this batch. **CISA** is the one rescued from that group: a second fetch
  through a different path returned the page, which calls itself "America's
  Cyber Defense Agency".

  Two rows are deliberately not national and say so in `Note`: **CERT RS**
  serves Republika Srpska rather than Bosnia and Herzegovina as a state, and
  **Cyberzaintza** is the Basque Country's agency. Both are official and
  public, both carry an ISO 3166-2 code in `Paese / Area` — `BA-SRP`,
  `ES-Euskadi` — rather than being filed as if they covered a country.

  Two more carry a caveat for the same reason the TLS ones did in
  `unsd:2026-09`: `cert.gov.ua` and `cert.gov.kz` serve a JavaScript shell of
  a couple of kilobytes whose `<title>` is the only thing identifying them.
  That is enough to catalogue and worth writing down before a future link
  check reports them as thin.

  11 of the 40 advertise a feed, each one fetched and confirmed to return a
  feed rather than a page. Cyprus's is `?format=feed&type=rss`, which the site
  prints with `&amp;` in its own `<head>` — copied verbatim it would be wrong,
  so it is stored decoded.

  `CSIRT Italia` sits on `acn.gov.it`, a host the catalogue already carries
  for the agency itself. It is a distinct service rather than a second row for
  one thing, and the new nesting warning agrees: the run reports the same 11
  pairs as before this batch, none of them new.

- **12 central banks, and a correction worth more than the additions**, in
  `Banche Centrali & Autorità Monetarie`. Coverage goes from **143 of the 193
  UN member states to 173** — and only 12 of those 30 came from new rows.

  The subsection looked as though it were missing 50 countries. It was missing
  far fewer, and the difference is entirely in how the existing rows were
  written.

  **Eighteen countries were already covered by a row that named one of them.**
  Three currency unions share a single central bank, and each was filed under a
  single member: the BCEAO under `SN`, the BEAC under `CM`, the Eastern
  Caribbean Central Bank under `Caraibi`. Their `Paese / Area` now lists every
  member state, taken from each bank's own site rather than from memory —
  BCEAO's own *États membres* page names all eight, BEAC's *la BEAC* page all
  six, ECCB's home page all eight including Anguilla and Montserrat.

  **The Bank of South Sudan was filed under `SD`.** Its own `Note` read
  "South Sudan", so the country code was the error, not the row. That one
  character was hiding a real gap: with South Sudan's bank standing in for
  Sudan, **Sudan's own central bank looked catalogued and was not**. It is now
  in, at `cbos.gov.sd`.

  That was found by the canonical-URL check added in the previous entry, on its
  first real use: the new row for South Sudan collided with the existing one,
  which comparing URLs verbatim would have missed only if the two had been
  spelled differently — and would have let through as two rows. Instead
  `validate.py` failed the run and named both lines.

  **Twenty countries remain outside, and every one is accounted for.** Ten have
  no central bank at all — Andorra, Kiribati, Liechtenstein, Marshall Islands,
  Micronesia, Monaco, Nauru, Palau, Panama, Tuvalu all use another country's
  currency, which the list of central banks states explicitly. Four are
  catalogued elsewhere and are a classification question rather than a gap:
  the Bundesbank, Banca d'Italia and the Federal Reserve sit under
  `Finanza, Economia & Business`, and **Banco de España under a *media*
  category**, `Europa Occidentale`. Those four rows are left where they are;
  moving a row is a different decision from adding one. The last six —
  Iran, Lebanon, North Korea, Sierra Leone, Yemen, Zimbabwe — have a URL that
  could not be verified from here: a Radware captcha on `rbz.co.zw`, a
  Cloudflare challenge on `bdl.gov.lb`, DNS failures on the rest, and nothing
  published at all for North Korea.

  Provenance splits three ways because the URLs did: `bis:2026-09` (4) from the
  BIS list of member central banks, `wikipedia.cb:2026-09` (6) from the
  external links of each bank's Wikipedia article, and empty for the two found
  by hand. No single directory covers this ground — BIS has 63 members and
  stops there, and the Wikipedia list of central banks carries names and
  currencies but no websites at all.

  One thing this batch did **not** fix, and is worth recording: three South
  Sudanese outlets — Eye Radio, Radio Tamazuj, Sudans Post — are also filed
  under `SD`. That is the same error in a different subsection, and belongs to
  whoever works the media rows next.

- **Five national chambers of commerce** — Azerbaijan, Bangladesh, Cambodia,
  Indonesia and South Korea — and the finding that this subsection is **not
  the enumerable register the growth plan assumed it was.**

  The plan grouped chambers of commerce with statistics offices and central
  banks as a category that "has by nature one entry per country", where "the
  expected number is known in advance, so completeness is measurable". For the
  first two that held: the UN Statistics Division publishes a directory, the
  BIS publishes one, and both could be read. **For chambers there is no such
  list reachable from here**, and four attempts is enough to say so rather
  than keep looking:

  | Directory | What it gives |
  |---|---|
  | ICC World Chambers Federation | member list rendered in JavaScript; no data in the HTML |
  | ICC national committees | same |
  | CACCI (Asia-Pacific) | member *names* in the page, but exactly one member URL in the whole document |
  | World Chambers Network | a search portal over 12,700 chambers, local and national mixed, not enumerable |
  | Wikipedia | 93 pages, mostly bilateral and city chambers, 18 country subcategories |

  So these five rows are hand additions and `Provenienza` stays **empty**:
  CACCI's map named the organisations, every URL was resolved and read
  separately, and calling that a batch would put a directory's name on work it
  did not do — which is the one thing the column must not be used for.

  Coverage moves from 102 of the 193 UN member states to 107. That is the
  honest yield of a subsection with no register behind it, and it says the
  remaining 86 will come one at a time rather than in an import.

  Two candidates were dropped for the usual reason: Timor-Leste's chamber sits
  behind a Cloudflare challenge and Papua New Guinea's domain does not resolve.
  Sweden was looked for and not added — `chamber.se` is gone, and
  `svenskhandel.se` is a trade federation, not the chamber.

  **`validate.py` caught a mistake of mine here, not a pre-existing one.**
  CACCI also names Mongolia's chamber, and I probed and verified it without
  first checking it against my own list of missing countries — where Mongolia
  is not, because `mongolchamber.mn` has been in the catalogue all along. The
  canonical-URL check added two entries ago failed the run and named both
  lines. It is the second duplicate it has caught in two batches; the first
  was a real data error, this one was carelessness, and the check does not
  care which.

- **Eleven official gazettes, and a row that was hiding a continent.** Coverage
  in `Gazzette Ufficiali & Legislazione` goes from **70 of the 193 UN member
  states to 102** — and 22 of those 32 came from widening one existing row.

  **Gazettes.Africa was filed under `Africa`.** Its own navigation names the
  24 countries whose gazettes it holds, so `Paese / Area` now lists them.
  The `Note` says plainly what the row is: an archive of where the issues can
  be read, **not the official publisher**. That distinction matters for how the
  coverage figure should be read, and it is the reason the note spells it out
  rather than letting a country code imply more than it should.

  The eleven added by hand are official publishers: Albania's QBZ, Armenia's
  ARLIS, Bahrain's Legislation Commission, Bosnia's Službeni glasnik, Georgia's
  Matsne, Iceland's Stjórnartíðindi, Moldova's Monitorul Oficial, Montenegro's
  Službeni list, Morocco's SGG, North Macedonia's Службен весник, and
  Uzbekistan's LEX.UZ.

  **This is the second bacino in a row with no register behind it**, and that
  is now a pattern rather than an accident. The plan credited all of bacino A
  with "completezza misurabile"; on the evidence, that holds for two of the
  four registers tested and fails for two:

  | Register | Directory | Held up? |
  |---|---|---|
  | Statistics offices | UN Statistics Division | yes |
  | Central banks | BIS, plus Wikipedia for the rest | yes |
  | Chambers of commerce | — | no: nothing enumerable is reachable |
  | Official gazettes | — | no: same |

  For gazettes the attempts were the Law Library of Congress *Guide to Law
  Online: Nations* (a LibGuides page whose country list is JavaScript), WIPO
  Lex and ILO NATLEX (both 404 on their directory paths), and a Wikipedia list
  that does not exist. What is reachable is regional: Gazettes.Africa for 24
  African countries, and nothing comparable elsewhere.

  So the eleven were found one at a time and `Provenienza` stays **empty** on
  all of them, as it did for the chambers. Four candidates were rejected for
  the usual reason and one for a subtler one: Tunisia's IORT serves 159 bytes,
  Vietnam's `congbao.chinhphu.vn` does not resolve, Algeria's `joradp.dz` is a
  998-byte frame stub, Kazakhstan's `adilet.zan.kz` serves a page whose visible
  text is the developer's own notes about meta tags — and **Jordan's entry was
  dropped because `pm.gov.jo` is the Prime Ministry, not the gazette.** A
  government site that answers `200` is still not the source it was meant to
  be.

- **24 data protection authorities**, taking `Autorità Data Protection &
  Privacy` from **42 of the 193 UN member states to 62** — plus Guernsey,
  Hong Kong, the Isle of Man and Jersey, which have authorities but are not
  member states and so do not move that count.

  This bacino behaves differently from the four before it, and the difference
  is worth naming because the growth plan has only one category for all of
  them. The **Global Privacy Assembly** publishes a list of 101 accredited
  members: it says authoritatively *which* authorities exist and what each is
  called, and links to none of them — every link on that page goes to an
  accreditation resolution in PDF. So the register exists and completeness is
  measurable, but the URLs are not in it. Three shapes now, not two:

  | Register | The list | The links |
  |---|---|---|
  | Statistics offices, central banks | yes | yes |
  | **Data protection authorities** | **yes** | **no** |
  | Chambers of commerce, gazettes | no | — |

  The regional networks do not close that gap: NADPA does not resolve, the
  Ibero-American RIPD returns 404 on its authorities page, and APPA's member
  list is a megabyte of JavaScript with no link in the HTML. The **EDPB** is
  the one exception — it publishes real URLs — and it was worth almost
  nothing here, because 25 of its 27 authorities were already catalogued.
  Only Liechtenstein was new. Europe was already done.

  So the 24 URLs were resolved and read one at a time, and `Provenienza` stays
  empty. **Armenia is why that matters**: the obvious candidate, `foi.am`,
  answers `200` and is the Freedom of Information Center of Armenia — an NGO,
  not the Personal Data Protection Agency the GPA list names. It is not in.

  Nine more are out for the usual reasons: Cloudflare challenges on Israel's
  and the Philippines' authorities, dead DNS for Gabon, Ghana, Georgia, Qatar
  and Tunisia, and pages too thin to identify anything for Senegal (457 bytes)
  and Uganda (541).

- **Two authorities were already catalogued, filed by their other mandate.**
  Chile's **Consejo para la Transparencia** sits under `AML, Sanzioni & PEP`
  and Colombia's **SIC** under `Antitrust & Concorrenza`. Neither filing is
  wrong — both bodies are genuinely multi-mandate — but neither is where a
  privacy lookup would find them, and the rows are left where they are because
  moving one is a different decision from adding one.

  Both slipped past the check I ran for exactly this: I searched existing rows
  for privacy words in the name, URL and note, and neither *Consejo para la
  Transparencia* nor *Superintendencia de Industria y Comercio* contains one.
  What caught them was the canonical-URL check, failing the run on the
  duplicate hosts — its third find in three batches. **Searching by name looks
  for sources you already know how to describe; searching by host does not.**

  Italy's Garante is the same shape, under `Italia`, and likewise untouched.

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

- **`scripts/validate.py` compares URLs by what they identify, not by how they
  are spelled**, and warns when one row's URL sits inside another's.

  The old check compared URLs verbatim apart from case and a trailing slash, so
  `http://x.org/news`, `https://www.x.org/news` and `https://x.org:443/news` —
  one page written three ways — read as three distinct rows. Scheme, `www.`, a
  default port and the trailing slash now all come off before comparing; the
  query string stays, because `?id=1` and `?id=2` are different pages. This
  finds nothing in the catalogue today, which is the answer to a question that
  had never actually been asked: an earlier entry here asserted an
  exact-domain check that `Fonti_OSINT.csv` did not have.

  The second rule is the one the growth plan asked for, and it could not be
  what that plan implied. 106 hosts appear on more than one row — `github.com`
  on 18, `gov.br` on 11 — so flagging a repeated host would have reported 106
  pairs of nothing and been ignored, exactly as a bare name-collision check
  would have been. What is worth a look is narrower: two rows on one host where
  **one URL is a path inside the other**. Measured, that finds 11 pairs, and
  about a third are one source entered twice under two names — `rnz.co.nz`
  twice for its Pacific desk, `europa.eu` twice for Eurobarometer — while the
  rest are genuinely separate desks of one outlet, like `bbc.com/news` and
  `bbc.com/news/world`.

  A third is too low to fail a build on and much too high to throw away, so
  `validate.py` grew **warnings**: printed, counted, and left to a person, with
  the exit code untouched. It is the first check here that does not claim more
  certainty than it has.
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

- `CONTRIBUTING.md`'s bulk-import section says two things it left implicit.
  A `Provenienza` stamp is legitimate whenever the rows came from one directory
  in one pass — `scripts/discover_candidates.py` stamps the directories it
  knows about, but it is not the only way a batch can arrive, and the previous
  wording read as though it were.

  And **a directory is a source of candidates, not of facts.** That is the
  lesson of `unsd:2026-09` above, and it is now stated where someone about to
  import will read it: the rows have to be fetched and read for the name the
  page gives itself *before* the batch is stamped. The sample check comes
  after, and cannot stand in for it — a sample drawn from rows nobody
  identified only measures how consistently they were not identified.

### Fixed

- **`CITATION.cff` said the catalogue held 5,098 sources when `v0.5.1` shipped
  5,108.** That release bumped `version` and `date-released` and left the count
  behind, so the citation metadata described a snapshot that never existed.
  The count is corrected to the figure `v0.5.1` actually had; all three fields
  move together at the next release.

  The number was right at every release up to `v0.5.0` and then drifted,
  because updating it is a hand step nobody wrote down. `CONTRIBUTING.md` now
  has a **Cutting a release** section listing the four files that carry numbers
  and the order to touch them, which is the part that stops it happening again
  — a lone correction would just be the same step missed next time.

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
