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

import csv
import pathlib
import tempfile
import unittest

import discover_candidates as dc
import validate as v


def run_validate(rows):
    """Validate a small catalogue and return the Report it produced.

    Goes through validate_osint() against a temporary CSV, so these tests
    exercise the real checks rather than a re-implementation of their rules.
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / "Fonti_OSINT.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(v.OSINT_COLUMNS)
            writer.writerows(rows)
        report = v.Report()
        original = v.OSINT_CSV
        v.OSINT_CSV = path
        try:
            v.validate_osint(report)
        finally:
            v.OSINT_CSV = original
    return report


def row(name, url, place="", sub="Globali & Internazionali"):
    return ["📰 Media & Testate Giornalistiche", sub,
            name, url, "", "", place, "", "nota", ""]


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


class DuplicateNames(unittest.TestCase):
    """A repeated `Fonte` is an error only when nothing distinguishes the rows."""

    def check(self, rows):
        # Report.errors holds (dataset, line, column, message)
        return [e for e in run_validate(rows).errors if e[2] == "Fonte"]

    row = staticmethod(row)

    def test_same_name_in_different_countries_is_allowed(self):
        # "National Bureau of Statistics" is Nigeria, Tanzania and Antigua.
        errors = self.check([
            self.row("National Bureau of Statistics", "https://a.example", "NG"),
            self.row("National Bureau of Statistics", "https://b.example", "TZ"),
            self.row("National Bureau of Statistics", "https://c.example", "AG"),
        ])
        self.assertEqual(errors, [])

    def test_same_name_and_same_country_is_an_error(self):
        errors = self.check([
            self.row("The Canadian Press", "https://a.example", "CA"),
            self.row("The Canadian Press", "https://b.example", "CA"),
        ])
        self.assertEqual(len(errors), 1)

    def test_same_name_with_a_missing_country_is_an_error(self):
        # The shape of every real duplicate found in the catalogue: a bulk
        # import added a row under an existing name without a country.
        errors = self.check([
            self.row("Reuters Fact Check", "https://a.example", "Globale"),
            self.row("Reuters Fact Check", "https://b.example", ""),
        ])
        self.assertEqual(len(errors), 1)

    def test_both_countries_missing_is_an_error(self):
        errors = self.check([
            self.row("Qualcosa", "https://a.example", ""),
            self.row("Qualcosa", "https://b.example", ""),
        ])
        self.assertEqual(len(errors), 1)

    def test_the_comparison_ignores_case_and_padding(self):
        errors = self.check([
            self.row("Il Post", "https://a.example", "IT"),
            self.row("  il post  ", "https://b.example", "IT"),
        ])
        self.assertEqual(len(errors), 1)

    def test_distinct_names_never_collide(self):
        errors = self.check([
            self.row("Il Post", "https://a.example", "IT"),
            self.row("Il Foglio", "https://b.example", "IT"),
        ])
        self.assertEqual(errors, [])

    def test_one_error_per_row_not_one_per_pair(self):
        # Three colliding rows report twice, not three times: each row is
        # reported once against the first match, so a large collision does not
        # bury the rest of the report.
        errors = self.check([
            self.row("Stessa", "https://a.example", "IT"),
            self.row("Stessa", "https://b.example", "IT"),
            self.row("Stessa", "https://c.example", "IT"),
        ])
        self.assertEqual(len(errors), 2)


class CanonicalUrls(unittest.TestCase):
    """One page written several ways is one page.

    The check used to compare URLs verbatim apart from case and a trailing
    slash, so a row could be added again under `http://` or with a `www.` and
    nothing would notice.
    """

    def test_scheme_www_port_and_trailing_slash_all_come_off(self):
        for value in ("https://www.example.org/news", "http://example.org/news",
                      "https://example.org/news/", "https://EXAMPLE.org/News",
                      "https://example.org:443/news"):
            with self.subTest(value=value):
                self.assertEqual(v.canonical_url(value), "example.org/news")

    def test_the_query_string_is_kept(self):
        # `?id=1` and `?id=2` are different pages, and several catalogued
        # sources are addressed that way.
        self.assertNotEqual(v.canonical_url("https://x.org/a?id=1"),
                            v.canonical_url("https://x.org/a?id=2"))

    def test_different_paths_stay_different(self):
        self.assertNotEqual(v.canonical_url("https://x.org/news"),
                            v.canonical_url("https://x.org/sport"))

    def test_a_subdomain_is_not_stripped(self):
        # Only `www.` comes off: `en.x.org` is a different site from `x.org`.
        self.assertNotEqual(v.canonical_url("https://en.x.org/"),
                            v.canonical_url("https://x.org/"))

    def test_host_and_path_are_split_consistently(self):
        self.assertEqual(v.url_host("https://www.example.org/news/world"), "example.org")
        self.assertEqual(v.url_path("https://www.example.org/news/world"), "/news/world")

    def test_a_homepage_has_an_empty_path(self):
        self.assertEqual(v.url_path("https://example.org/"), "")

    def test_the_same_page_written_twice_is_an_error(self):
        errors = [e for e in run_validate([
            row("Example", "https://www.example.org/news/"),
            row("Example Mirror", "http://example.org/news"),
        ]).errors if e[2] == "URL"]
        self.assertEqual(len(errors), 1)

    def test_two_real_pages_on_one_host_are_not(self):
        errors = [e for e in run_validate([
            row("Example News", "https://example.org/news"),
            row("Example Sport", "https://example.org/sport"),
        ]).errors if e[2] == "URL"]
        self.assertEqual(errors, [])


class NestedPaths(unittest.TestCase):
    """A URL inside another on the same host is a warning, never an error.

    Measured on the catalogue, the rule finds 11 pairs and about a third are
    one source entered twice; the rest are genuinely separate desks of one
    outlet. That precision is too low to fail a build on and too high to
    discard, so it prints and the run still passes.
    """

    def warnings(self, rows):
        return [w for w in run_validate(rows).warnings if w[2] == "URL"]

    def test_a_section_inside_another_is_flagged(self):
        self.assertEqual(len(self.warnings([
            row("Example News", "https://example.org/news"),
            row("Example World", "https://example.org/news/world"),
        ])), 1)

    def test_a_warning_does_not_become_an_error(self):
        report = run_validate([
            row("Example News", "https://example.org/news"),
            row("Example World", "https://example.org/news/world"),
        ])
        self.assertEqual(report.errors, [])
        self.assertTrue(report.summary())

    def test_sibling_paths_are_not_flagged(self):
        # `/news` and `/sport` are not nested, however alike they look.
        self.assertEqual(self.warnings([
            row("Example News", "https://example.org/news"),
            row("Example Sport", "https://example.org/sport"),
        ]), [])

    def test_a_shared_prefix_is_not_nesting(self):
        # `/news` is not a parent of `/newsletter`: only a full path segment
        # counts, or every outlet would flag against its own archive.
        self.assertEqual(self.warnings([
            row("Example News", "https://example.org/news"),
            row("Example Letter", "https://example.org/newsletter"),
        ]), [])

    def test_different_hosts_never_pair(self):
        self.assertEqual(self.warnings([
            row("A", "https://a.example/news"),
            row("B", "https://b.example/news/world"),
        ]), [])

    def test_a_homepage_is_not_a_parent_of_everything(self):
        # Otherwise every row on a host with a catalogued homepage would be
        # flagged against it, which is the noise this rule exists to avoid.
        self.assertEqual(self.warnings([
            row("Example", "https://example.org"),
            row("Example News", "https://example.org/news"),
        ]), [])

    def test_the_warning_is_reported_against_the_inner_row(self):
        warnings = self.warnings([
            row("Example World", "https://example.org/news/world"),
            row("Example News", "https://example.org/news"),
        ])
        # Report tuples are (dataset, line, column, message); the deeper URL is
        # on line 2, the broader one on line 3.
        self.assertEqual(warnings[0][1], 2)
        self.assertIn("line 3", warnings[0][3])


if __name__ == "__main__":
    unittest.main(verbosity=2)
