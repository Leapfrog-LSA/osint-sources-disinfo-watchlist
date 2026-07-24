# OSINT Sources & Disinformation Watchlist

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Release](https://img.shields.io/github/v/release/Leapfrog-LSA/osint-sources-disinfo-watchlist)](https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/releases)
[![Stars](https://img.shields.io/github/stars/Leapfrog-LSA/osint-sources-disinfo-watchlist)](https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/stargazers)
[![Issues](https://img.shields.io/github/issues/Leapfrog-LSA/osint-sources-disinfo-watchlist)](https://github.com/Leapfrog-LSA/osint-sources-disinfo-watchlist/issues)

Two companion CSV datasets for open-source intelligence (OSINT) and due-diligence work:

- **`Fonti_OSINT_v.0.1.csv`** — a curated catalogue of reliable, ongoing sources (media, open data, corporate registries, sanctions/PEP lists, cybersecurity intel, etc.)
- **`disinfo_sources_master.csv`** — a watchlist of documented disinformation domains, impersonation clones, and fake-news networks

They are kept in the same repo because they're produced and maintained together as part of the same research workflow, but they serve opposite purposes: one is a "trust these" list, the other is a "watch out for these" list.

## `Fonti_OSINT_v.0.1.csv`

4,974 sources across 12 macro-categories:

| Category | Sources |
|---|---:|
| Media & Testate Giornalistiche | 2,103 |
| Settori Specifici (AI/dev tools, finance, sector-specific) | 1,200 |
| Open Data & Trasparenza | 472 |
| Statistiche & Dati Macroeconomici | 372 |
| Registri Aziendali & Corporate Intelligence | 250 |
| Cybersecurity & Digital OSINT | 170 |
| Geopolitica & Intelligence | 151 |
| Social Media & Media Monitoring | 79 |
| Sanzioni, PEP & Compliance | 67 |
| Sostenibilità & ESG | 46 |
| Diritti Umani & Giudiziario | 34 |
| Fact-Checking & Disinformazione | 30 |

**Columns:** `Macro-categoria`, `Sottosezione`, `Fonte`, `URL`, `RSS Feed`, `Lingua`, `Paese / Area`, `Accesso`, `Note`

## `disinfo_sources_master.csv`

114 documented disinformation domains, two main clusters:

- **Doppelganger campaign** (51 entries) — Russian state-linked infrastructure (SDA/Structura/ANO Dialog) cloning major outlets: Bild, Der Spiegel, Süddeutsche Zeitung, Der Tagesspiegel, T-Online, Welt, FAZ, Neues Deutschland, The Guardian, Mail Online, Reuters, Fox News, ANSA, and others. Sourced from Qurium (2022) and DFRLab (2024).
- **Italian fake-news / satire network** (~60 entries) — typo-squats, hoax sites, and declared satire, sourced from BUTAC/Bufalopedia.

**Columns:** `domain`, `impersonated_outlet`, `authentic_domain`, `country`, `tld`, `first_seen`, `campaign`, `attribution`, `source`, `evidence_level`, `cats_flag`, `notes`

## License

Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) — see [`LICENSE`](LICENSE). You may use, adapt, and redistribute the datasets, including commercially, as long as you credit Leapfrog-LSA / LAWARA AI.
