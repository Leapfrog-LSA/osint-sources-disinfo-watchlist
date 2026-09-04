#!/usr/bin/env python3
"""
Tests for scripts/validate.py, currently covering the `Provenienza` column.

Run locally:

    python scripts/test_validate.py

Or, with everything else:

    python -m unittest discover -s scripts -p "test_*.py"

`Provenienza` records which directory a row came from and in which batch. It
is the field that makes a batch measurable after the fact and removable in one
operation, so the rules around it are worth pinning down: a malformed stamp
silently breaks both, and an empty one has to keep meaning "not determined"
rather than becoming a guess.

No network, no filesystem writes. Standard library only.
"""

import unittest

import discover_candidates as dc
import validate as v


class ProvenanceFormat(unittest.TestCase):
    """`<list>:<YYYY-MM>`, or empty."""

    def test_accepts_a_well_formed_stamp(self):
        for value in ("ifcn:2026-08", "opensanctions:2026-12", "unsd:2027-01",
                      "gpa.members:2026-03", "first-org:2026-11"):
            with self.subTest(value=value):
                self.assertRegex(value, v.PROVENANCE)

    def test_rejects_a_stamp_without_a_batch(self):
        # The list alone cannot be scored or reversed: two runs a year apart
        # would be indistinguishable.
        self.assertIsNone(v.PROVENANCE.match("ifcn"))

    def test_rejects_an_impossible_month(self):
        self.assertIsNone(v.PROVENANCE.match("ifcn:2026-13"))
        self.assertIsNone(v.PROVENANCE.match("ifcn:2026-00"))

    def test_rejects_loose_date_shapes(self):
        for value in ("ifcn:26-08", "ifcn:2026-8", "ifcn:2026", "ifcn:2026-08-10"):
            with self.subTest(value=value):
                self.assertIsNone(v.PROVENANCE.match(value))

    def test_list_name_is_lowercase(self):
        # Case-insensitive matching would let 'IFCN:2026-08' and 'ifcn:2026-08'
        # split one batch into two.
        self.assertIsNone(v.PROVENANCE.match("IFCN:2026-08"))


class EmptyMeansUnknown(unittest.TestCase):
    """The rows that predate the column must stay honestly unlabelled."""

    def test_empty_is_not_matched_and_is_not_an_error(self):
        # validate.py only checks the pattern when the field is non-empty; the
        # pattern itself must not accept the empty string, or a typo that
        # strips to nothing would pass as a real stamp.
        self.assertIsNone(v.PROVENANCE.match(""))

    def test_whitespace_only_is_not_a_stamp(self):
        self.assertIsNone(v.PROVENANCE.match("   "))


class SchemaStaysInStep(unittest.TestCase):
    """The two scripts must agree on the columns, or discovery emits bad rows."""

    def test_validate_and_discovery_share_the_same_columns(self):
        self.assertEqual(v.OSINT_COLUMNS, dc.OSINT_COLUMNS)

    def test_provenienza_is_the_last_column(self):
        # Appended rather than inserted, so anything reading the file by
        # position keeps working.
        self.assertEqual(v.OSINT_COLUMNS[-1], "Provenienza")

    def test_every_discovery_source_declares_a_provenance_list(self):
        for name, config in dc.SOURCES.items():
            with self.subTest(source=name):
                self.assertIn("provenance", config)
                self.assertTrue(config["provenance"])

    def test_every_discovery_source_stamps_a_valid_batch(self):
        for name, config in dc.SOURCES.items():
            with self.subTest(source=name):
                self.assertRegex(dc.batch_id(config["provenance"]), v.PROVENANCE)

    def test_a_built_row_carries_every_column(self):
        row_keys = {
            "Macro-categoria", "Sottosezione", "Fonte", "URL", "RSS Feed",
            "Lingua", "Paese / Area", "Accesso", "Note", "Provenienza",
        }
        self.assertEqual(row_keys, set(dc.OSINT_COLUMNS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
