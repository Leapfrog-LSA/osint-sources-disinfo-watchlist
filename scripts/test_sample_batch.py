#!/usr/bin/env python3
"""
Tests for scripts/sample_batch.py.

Run locally:

    python scripts/test_sample_batch.py

Or, with everything else:

    python -m unittest discover -s scripts -p "test_*.py"

The sampler is what replaces reading every imported row once batches get too
big to read. Two of its properties are load-bearing rather than cosmetic, and
both are pinned down here:

  - the draw is a function of the batch id alone, so nobody can re-roll it
    until the sample looks clean, and two reviewers see the same rows;
  - a batch smaller than the sample size is returned whole, so a small import
    is never accepted on a partial read.

No network, no writes to the repository. Standard library only.
"""

import csv
import pathlib
import tempfile
import unittest

import sample_batch as sb


def catalogue(rows):
    """Write a temporary Fonti_OSINT.csv and return its path."""
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".csv", delete=False, newline="", encoding="utf-8")
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow([
        "Macro-categoria", "Sottosezione", "Fonte", "URL", "RSS Feed",
        "Lingua", "Paese / Area", "Accesso", "Note", "Provenienza",
    ])
    for name, url, prov in rows:
        writer.writerow(["📰 Media & Testate Giornalistiche", "Globali & Internazionali",
                         name, url, "", "", "", "", "nota", prov])
    handle.close()
    return pathlib.Path(handle.name)


class ReproducibleDraw(unittest.TestCase):
    """The sample must not be re-rollable."""

    def setUp(self):
        self.rows = [(i, {"Fonte": f"F{i}"}) for i in range(2, 202)]

    def test_the_same_batch_always_draws_the_same_rows(self):
        first = sb.draw(self.rows, 60, "unsd:2026-10")
        second = sb.draw(self.rows, 60, "unsd:2026-10")
        self.assertEqual(first, second)

    def test_a_different_batch_draws_a_different_sample(self):
        a = sb.draw(self.rows, 60, "unsd:2026-10")
        b = sb.draw(self.rows, 60, "gijn:2026-10")
        self.assertNotEqual(a, b)

    def test_the_seed_depends_only_on_the_batch_id(self):
        self.assertEqual(sb.batch_seed("ifcn:2026-08"), sb.batch_seed("ifcn:2026-08"))
        self.assertNotEqual(sb.batch_seed("ifcn:2026-08"), sb.batch_seed("ifcn:2026-09"))

    def test_the_sample_is_returned_in_file_order(self):
        sample = sb.draw(self.rows, 60, "unsd:2026-10")
        self.assertEqual([n for n, _ in sample], sorted(n for n, _ in sample))

    def test_the_sample_has_no_repeats(self):
        sample = sb.draw(self.rows, 60, "unsd:2026-10")
        self.assertEqual(len(sample), len({n for n, _ in sample}))


class SmallBatches(unittest.TestCase):
    """Below the sample size, the whole batch is reviewed."""

    def test_a_batch_smaller_than_the_sample_is_returned_whole(self):
        rows = [(i, {"Fonte": f"F{i}"}) for i in range(2, 9)]   # 7 rows
        self.assertEqual(sb.draw(rows, 60, "ifcn:2026-09"), rows)

    def test_a_batch_exactly_the_sample_size_is_returned_whole(self):
        rows = [(i, {"Fonte": f"F{i}"}) for i in range(2, 62)]  # 60 rows
        self.assertEqual(sb.draw(rows, 60, "x:2026-01"), rows)

    def test_one_row_over_is_sampled(self):
        rows = [(i, {"Fonte": f"F{i}"}) for i in range(2, 63)]  # 61 rows
        self.assertEqual(len(sb.draw(rows, 60, "x:2026-01")), 60)


class SelectingABatch(unittest.TestCase):
    """Rows are selected by their exact `Provenienza`."""

    def setUp(self):
        self.path = catalogue([
            ("A", "https://a.example", "ifcn:2026-08"),
            ("B", "https://b.example", "ifcn:2026-08"),
            ("C", "https://c.example", "ifcn:2026-09"),
            ("D", "https://d.example", ""),
        ])
        self.addCleanup(self.path.unlink)

    def test_only_the_named_batch_is_loaded(self):
        rows = sb.load_batch("ifcn:2026-08", self.path)
        self.assertEqual([r["Fonte"] for _, r in rows], ["A", "B"])

    def test_a_neighbouring_batch_is_not_included(self):
        rows = sb.load_batch("ifcn:2026-09", self.path)
        self.assertEqual([r["Fonte"] for _, r in rows], ["C"])

    def test_unstamped_rows_belong_to_no_batch(self):
        # The 4,986 rows that predate the column must never be swept into one.
        self.assertEqual(sb.load_batch("", self.path), [])

    def test_line_numbers_match_the_file(self):
        rows = sb.load_batch("ifcn:2026-09", self.path)
        self.assertEqual(rows[0][0], 4)  # header is line 1, C is the third row

    def test_known_batches_counts_each_one(self):
        self.assertEqual(
            sb.known_batches(self.path),
            {"ifcn:2026-08": 2, "ifcn:2026-09": 1},
        )


class AcceptanceThreshold(unittest.TestCase):
    def test_the_threshold_is_zero_defects(self):
        # Stated in the output the reviewer reads, so it cannot drift silently
        # from the rule written in CONTRIBUTING.md.
        self.assertEqual(sb.MAX_DEFECTS, 0)

    def test_the_rendered_report_states_the_threshold_and_the_batch(self):
        rows = [(2, {"Fonte": "A", "URL": "https://a.example",
                     "Macro-categoria": "M", "Sottosezione": "S",
                     "Lingua": "", "Paese / Area": "", "Note": ""})]
        text = sb.render("ifcn:2026-08", 1, rows)
        self.assertIn("ifcn:2026-08", text)
        self.assertIn("0 defect", text)
        self.assertIn("reject the whole batch", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
