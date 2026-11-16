"""Tests for stats.py — the check that README.md's figures match the CSVs.

No network requests, and no dependence on the real datasets.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stats  # noqa: E402


def source(category, **fields):
    row = {"Macro-categoria": category, "Sottosezione": "x", "Fonte": "x", "URL": "https://x",
           "RSS Feed": "", "Lingua": "", "Paese / Area": "", "Accesso": "", "Note": "",
           "Provenienza": ""}
    row.update(fields)
    return row


OSINT = [
    source("📰 Media & Testate Giornalistiche", Note="a", Lingua="EN"),
    source("📰 Media & Testate Giornalistiche", Note="b"),
    source("⚖️ Sanzioni, PEP & Compliance", Note="c", Provenienza="egmont:2026-11"),
    source("⚖️ Sanzioni, PEP & Compliance", Note="d", Provenienza="egmont:2026-11"),
]
DISINFO = [{"campaign": "Doppelganger"}, {"campaign": "Doppelganger"}, {"campaign": "satira"}]

README = """
4 sources across 2 macro-categories:

| Category | Sources |
|---|---:|
| Media & Testate Giornalistiche | 2 |
| Sanzioni, PEP & Compliance (lists) | 2 |

`egmont:2026-11`

The 2 unstamped rows are older.

| `Note` | 100% |
| `Paese / Area` | 0% |
| `Lingua` | 25% |
| `RSS Feed` | 0% |
| `Accesso` | 0% |

3 documented disinformation domains and platform accounts
"""


class Compute(unittest.TestCase):
    def setUp(self):
        self.stats = stats.compute(OSINT, DISINFO)

    def test_counts_rows_and_categories_without_emoji(self):
        self.assertEqual(self.stats["total"], 4)
        self.assertEqual(self.stats["categories"],
                         {"Media & Testate Giornalistiche": 2, "Sanzioni, PEP & Compliance": 2})

    def test_coverage_is_a_rounded_percentage(self):
        self.assertEqual(self.stats["coverage"]["Note"], 100)
        self.assertEqual(self.stats["coverage"]["Lingua"], 25)

    def test_unstamped_rows_are_not_a_batch(self):
        self.assertEqual(self.stats["unstamped"], 2)
        self.assertEqual(self.stats["batches"], {"egmont:2026-11": 2})

    def test_watchlist_is_counted(self):
        self.assertEqual(self.stats["watchlist"], 3)
        self.assertEqual(self.stats["campaigns"]["Doppelganger"], 2)


class CheckReadme(unittest.TestCase):
    def setUp(self):
        self.stats = stats.compute(OSINT, DISINFO)

    def test_a_matching_readme_passes(self):
        self.assertEqual(stats.check_readme(self.stats, README), [])

    def test_a_stale_total_is_reported(self):
        problems = stats.check_readme(self.stats, README.replace("4 sources", "5 sources"))
        self.assertTrue(any("5 sources" in p for p in problems))

    def test_thousands_separators_are_read(self):
        osint = OSINT * 300
        readme = (README.replace("4 sources", "1,200 sources")
                  .replace("| 2 |", "| 600 |").replace("The 2 unstamped", "The 600 unstamped"))
        self.assertEqual(stats.check_readme(stats.compute(osint, DISINFO), readme), [])

    def test_a_stale_category_count_is_reported(self):
        readme = README.replace("| Media & Testate Giornalistiche | 2 |",
                                "| Media & Testate Giornalistiche | 9 |")
        problems = stats.check_readme(self.stats, readme)
        self.assertTrue(any("Media & Testate Giornalistiche" in p for p in problems))

    def test_a_missing_category_row_is_reported(self):
        readme = README.replace("| Sanzioni, PEP & Compliance (lists) | 2 |\n", "")
        problems = stats.check_readme(self.stats, readme)
        self.assertTrue(any("no row for 'Sanzioni, PEP & Compliance'" in p for p in problems))

    def test_a_stale_coverage_figure_is_reported(self):
        problems = stats.check_readme(self.stats, README.replace("| 25% |", "| 30% |"))
        self.assertTrue(any("`Lingua`" in p for p in problems))

    def test_a_stale_unstamped_count_is_reported(self):
        problems = stats.check_readme(self.stats, README.replace("The 2 unstamped", "The 7 unstamped"))
        self.assertTrue(any("unstamped" in p for p in problems))

    def test_an_undocumented_batch_is_reported(self):
        problems = stats.check_readme(self.stats, README.replace("`egmont:2026-11`", ""))
        self.assertTrue(any("egmont:2026-11" in p for p in problems))

    def test_a_stale_watchlist_count_is_reported(self):
        problems = stats.check_readme(self.stats, README.replace("3 documented", "9 documented"))
        self.assertTrue(any("watchlist" in p for p in problems))


class CheckCitation(unittest.TestCase):
    CITATION = ("abstract: >-\n  Fonti_OSINT is a curated catalogue of 4 reliable,\n"
                "  ongoing sources. disinfo_sources_master is a watchlist\n  of 3 documented domains.\n")

    def setUp(self):
        self.stats = stats.compute(OSINT, DISINFO)

    def test_a_matching_citation_passes(self):
        self.assertEqual(stats.check_citation(self.stats, self.CITATION), [])

    def test_a_count_split_across_lines_is_still_read(self):
        wrapped = self.CITATION.replace("watchlist\n  of 3", "watchlist of\n  3")
        self.assertEqual(stats.check_citation(self.stats, wrapped), [])

    def test_the_v0_5_1_mistake_is_caught(self):
        # `v0.5.1` bumped `version` and left the abstract's row count behind.
        problems = stats.check_citation(self.stats, self.CITATION.replace("of 4 reliable", "of 3 reliable"))
        self.assertEqual(len(problems), 1)


class RealFiles(unittest.TestCase):
    def test_the_readme_matches_the_datasets(self):
        current = stats.compute(stats.read(stats.OSINT_CSV), stats.read(stats.DISINFO_CSV))
        self.assertEqual(stats.check_readme(current, stats.README.read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
