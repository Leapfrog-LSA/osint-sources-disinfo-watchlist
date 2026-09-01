#!/usr/bin/env python3
"""
Regression tests for scripts/check_links.py.

Run locally:

    python scripts/test_check_links.py

Or, with everything else:

    python -m unittest discover -s scripts -p "test_*.py"

Most of these exist because of one incident. v0.5.0 removed 21 sources
from Fonti_OSINT.csv on this script's say-so; at least three were alive
and had to be restored, among them VERA Files, an IFCN verified
signatory. Three separate faults did it, and each has a test here named
after the source it killed. If one of those tests ever fails again, the
catalogue is about to lose a live source.

No network. Every case drives the pure classification functions with
canned responses, so the suite says the same thing on a laptop, on a CI
runner, and behind a proxy that eats half the internet — which matters
especially here, since misreading a degraded network as dead sources is
the exact bug under test.

Standard library only — no dependencies to install.
"""

import unittest

import check_links as cl


def response(status=200, body=b"", final_url="https://example.org/", headers=None):
    """One canned HTTP response, classified the way fetch_once would."""
    return cl.classify_response(status, headers or {}, body, final_url)


def page(text, size=60_000):
    """A page of roughly `size` bytes that contains `text`."""
    filler = b"<p>ordinary article content</p>" * (size // 31 + 1)
    return b"<html><body>" + text.encode("utf-8") + filler + b"</body></html>"


class RemovedWhileAlive(unittest.TestCase):
    """The three faults that removed live sources in v0.5.0."""

    def test_central_bank_of_the_gambia_connection_reset_is_not_death(self):
        # "Connection reset by peer" on every attempt used to mean `dead`.
        # It is a fact about the path between the runner and the host: the
        # bank's site was up the whole time.
        attempts = [cl.Attempt("conn_error", None, "connection failed: [Errno 104] Connection reset by peer")] * 3
        verdict = cl.summarize(attempts)
        self.assertEqual(verdict.bucket, "unreachable")
        self.assertNotIn(verdict.bucket, cl.REMOVAL_CANDIDATE_BUCKETS)

    def test_lanka_business_online_empty_body_is_not_parked(self):
        # A 200 with nothing in it used to be classified `parked`. The site
        # was serving 120 KB to an ordinary browser at the same moment.
        attempt = response(200, b"", "https://lankabusinessonline.com")
        self.assertEqual(attempt.category, "empty")
        verdict = cl.summarize([attempt] * 3)
        self.assertEqual(verdict.bucket, "empty")
        self.assertNotIn(verdict.bucket, cl.REMOVAL_CANDIDATE_BUCKETS)

    def test_vera_files_placeholder_string_is_not_a_parked_marker(self):
        # "future home of something quite cool" is the stock Apache/cPanel
        # placeholder. It is not a for-sale page, and it condemned a live
        # IFCN signatory.
        self.assertNotIn("future home of something quite cool", cl.PARKED_MARKERS)

    def test_vera_files_marker_text_on_a_real_page_is_still_alive(self):
        # Belt and braces: even if some marker matches, a page far too big
        # to be a placeholder is quoting it, not serving it.
        attempt = response(200, page("future home of something quite cool"), "https://verafiles.org")
        self.assertEqual(attempt.category, "success")

    def test_a_quoted_for_sale_phrase_does_not_condemn_an_article(self):
        attempt = response(200, page("this domain is for sale"), "https://news.example.org/")
        self.assertEqual(attempt.category, "success")


class ParkedStillCaught(unittest.TestCase):
    """The fixes must not blind the checker to genuinely dead domains."""

    def test_marker_on_a_placeholder_sized_page_is_parked(self):
        attempt = response(200, b"<html><body>Buy this domain</body></html>", "https://gone.example/")
        self.assertEqual(attempt.category, "parked")
        self.assertIn(cl.summarize([attempt] * 3).bucket, cl.REMOVAL_CANDIDATE_BUCKETS)

    def test_redirect_to_a_parking_service_is_parked_whatever_the_body(self):
        # The strong signal stands alone: this is how Luxembourg Times and
        # ReportUSA Albania were correctly removed.
        attempt = response(
            200, page("perfectly innocent looking text"),
            "https://www.hugedomains.com/domain_profile.cfm?d=luxembourgtimes.com",
        )
        self.assertEqual(attempt.category, "parked")

    def test_parking_host_matches_on_subdomains_only_at_a_label_boundary(self):
        self.assertEqual(cl._parking_host("https://www.sedo.com/x"), "www.sedo.com")
        self.assertIsNone(cl._parking_host("https://notsedo.com/x"))
        self.assertIsNone(cl._parking_host("https://sedo.com.example.org/x"))

    def test_near_empty_page_is_not_silently_treated_as_alive(self):
        attempt = response(200, b"<html></html>", "https://stub.example/")
        self.assertEqual(attempt.category, "empty")


class StatusClassification(unittest.TestCase):
    """Only the server saying "gone" counts as gone."""

    def test_404_and_410_are_gone(self):
        for status in (404, 410):
            with self.subTest(status=status):
                verdict = cl.summarize([response(status, b"nope", "https://x.example/")] * 3)
                self.assertEqual(verdict.bucket, "gone")
                self.assertIn(verdict.bucket, cl.REMOVAL_CANDIDATE_BUCKETS)

    def test_server_errors_are_not_gone(self):
        verdict = cl.summarize([response(500, b"boom", "https://x.example/")] * 3)
        self.assertEqual(verdict.bucket, "http_error")
        self.assertNotIn(verdict.bucket, cl.REMOVAL_CANDIDATE_BUCKETS)

    def test_anti_bot_codes_are_blocked_not_gone(self):
        for status in sorted(cl.BLOCKED_STATUS):
            with self.subTest(status=status):
                verdict = cl.summarize([response(status, b"denied", "https://x.example/")] * 3)
                self.assertEqual(verdict.bucket, "blocked")
                self.assertNotIn(verdict.bucket, cl.REMOVAL_CANDIDATE_BUCKETS)

    def test_a_mix_of_gone_and_anything_else_is_not_gone(self):
        attempts = [
            response(404, b"nope", "https://x.example/"),
            cl.Attempt("conn_error", None, "connection failed"),
            response(404, b"nope", "https://x.example/"),
        ]
        self.assertNotEqual(cl.summarize(attempts).bucket, "gone")

    def test_one_success_clears_the_url_entirely(self):
        attempts = [
            cl.Attempt("conn_error", None, "connection failed"),
            response(200, page("real content"), "https://x.example/"),
        ]
        self.assertIsNone(cl.summarize(attempts))


class BucketConfiguration(unittest.TestCase):
    """The report's own wiring, which is easy to break silently."""

    def test_only_gone_and_parked_may_cause_a_removal(self):
        self.assertEqual(cl.REMOVAL_CANDIDATE_BUCKETS, {"gone", "parked"})

    def test_network_conditions_are_never_removal_candidates(self):
        for bucket in ("unreachable", "blocked", "empty", "timeout", "tls_error", "http_error", "other"):
            with self.subTest(bucket=bucket):
                self.assertNotIn(bucket, cl.REMOVAL_CANDIDATE_BUCKETS)

    def test_every_bucket_is_ordered_and_titled(self):
        self.assertEqual(sorted(cl.BUCKET_ORDER), sorted(cl.BUCKET_TITLES))
        self.assertLessEqual(cl.REMOVAL_CANDIDATE_BUCKETS, set(cl.BUCKET_ORDER))

    def test_summarize_only_returns_known_buckets(self):
        categories = [
            "gone", "parked", "empty", "blocked", "http_error",
            "dns_error", "conn_error", "timeout", "ssl_error", "other_error",
        ]
        for category in categories:
            with self.subTest(category=category):
                verdict = cl.summarize([cl.Attempt(category, None, "x")] * 3)
                self.assertIn(verdict.bucket, cl.BUCKET_TITLES)


class ControlProbe(unittest.TestCase):
    """A run that cannot reach the web may not condemn anything."""

    def setUp(self):
        self._real_fetch = cl.fetch_once
        self.addCleanup(setattr, cl, "fetch_once", self._real_fetch)

    def _stub(self, categories):
        replies = iter(categories)
        cl.fetch_once = lambda url, ua, timeout: cl.Attempt(next(replies), None, f"stub {url}")

    def test_all_reference_sites_reachable_is_healthy(self):
        self._stub(["success"] * len(cl.CONTROL_URLS))
        healthy, reached, _ = cl.run_control_probe()
        self.assertTrue(healthy)
        self.assertEqual(reached, len(cl.CONTROL_URLS))

    def test_one_reachable_site_is_not_enough(self):
        self._stub(["success"] + ["conn_error"] * (len(cl.CONTROL_URLS) - 1))
        healthy, reached, _ = cl.run_control_probe()
        self.assertFalse(healthy)
        self.assertEqual(reached, 1)

    def test_nothing_reachable_is_degraded(self):
        self._stub(["conn_error"] * len(cl.CONTROL_URLS))
        healthy, _, _ = cl.run_control_probe()
        self.assertFalse(healthy)


class DegradedRunReport(unittest.TestCase):
    """The v0.5.0-stopper: a broken network offers no removal candidates."""

    def setUp(self):
        self.buckets = {
            "gone": [("https://a.example/", cl.Verdict("gone", "HTTP 404"))],
            "parked": [("https://b.example/", cl.Verdict("parked", "parked"))],
            "unreachable": [("https://c.example/", cl.Verdict("unreachable", "reset"))],
        }
        self.by_url = {u: [] for u in ("https://a.example/", "https://b.example/", "https://c.example/")}

    def test_degraded_run_names_no_removal_candidates(self):
        report = cl.render_report(self.by_url, self.buckets, False, 0, ["- stub"])
        self.assertIn("not valid for removals", report)
        self.assertIn("Removal candidates: none this run", report)

    def test_healthy_run_counts_only_gone_and_parked(self):
        report = cl.render_report(self.by_url, self.buckets, True, 3, [])
        self.assertIn("2 of 3 findings are removal candidates", report)
        self.assertNotIn("not valid for removals", report)

    def test_findings_are_still_reported_when_degraded(self):
        # Suppressing the candidacy must not suppress the record.
        report = cl.render_report(self.by_url, self.buckets, False, 0, ["- stub"])
        for url in self.by_url:
            self.assertIn(url, report)


class SharedVerificationIsDocumented(unittest.TestCase):
    """discover_candidates.py rejecting a source is not a second opinion."""

    def test_discovery_still_routes_through_check_url(self):
        import discover_candidates as dc

        # If this ever stops being true the note in verify_candidate() and
        # the rule in CONTRIBUTING.md need revisiting — but until then, a
        # rejection there must not be cited as corroboration of one here.
        self.assertIn("check_url", dc.verify_candidate.__code__.co_names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
