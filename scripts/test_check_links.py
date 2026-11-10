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


class FeedBodies(unittest.TestCase):
    """A feed is a feed when it parses as one *and* carries an entry."""

    FEED = (b'<?xml version="1.0"?><rss version="2.0"><channel>'
            b"<title>Example</title><item><title>a</title></item></channel></rss>")
    EMPTY = (b'<?xml version="1.0"?><rss version="2.0"><channel>'
             b"<title>Comentarios en:</title></channel></rss>")
    ATOM = (b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">'
            b"<entry><title>a</title></entry></feed>")

    def test_a_feed_with_entries_is_a_feed(self):
        self.assertTrue(cl.feed_like(self.FEED))
        self.assertTrue(cl.feed_like(self.ATOM))

    def test_an_empty_feed_is_not(self):
        # El Espectador's stale cell redirects to the site's default
        # WordPress *comments* feed: valid XML, right content type, nothing
        # in it. Accepting "parses as a feed" would keep that cell forever.
        self.assertFalse(cl.feed_like(self.EMPTY))

    def test_a_web_page_is_not(self):
        self.assertFalse(cl.feed_like(b"<!doctype html><html><body>hi</body></html>"))


class LandingClassification(unittest.TestCase):
    """Which redirects mean something, and which are noise."""

    def test_cosmetic_redirects_are_not_findings(self):
        for stored, final in (
            ("https://example.org/news", "https://www.example.org/news"),
            ("http://example.org/news", "https://example.org/news"),
            ("https://example.org/news", "https://example.org/news/"),
            ("https://example.org/news", "https://example.org/news/index.html"),
            ("https://example.org:443/news", "https://example.org/news"),
            ("https://example.org/news", "https://example.org/en/news"),
            ("https://example.org/news", "https://fr.example.org/news"),
            ("https://example.org/news", "https://example.org/news/world"),
        ):
            with self.subTest(final=final):
                self.assertEqual(cl.landing_kind(stored, final), "")

    def test_a_different_site_is_a_finding(self):
        # The Tanzania chamber's domain lapsed and now redirects to an
        # online-gambling site, answering 200 the whole way.
        self.assertEqual(
            cl.landing_kind("http://tccia.com/", "https://cintatogelaman.com/"),
            "host")

    def test_a_different_section_is_a_finding(self):
        # RNZ's catalogued Pacific address redirected to another section for
        # months while every status check called it healthy.
        self.assertEqual(
            cl.landing_kind("https://www.rnz.co.nz/international/pacific-news",
                            "https://www.rnz.co.nz/news/pacific"),
            "path")

    def test_a_deep_page_falling_back_to_the_home_page_is_a_finding(self):
        self.assertEqual(
            cl.landing_kind("https://example.org/citypress", "https://example.org/"),
            "home")

    def test_no_landing_recorded_is_not_a_finding(self):
        self.assertEqual(cl.landing_kind("https://example.org/news", ""), "")


class LandingFindings(unittest.TestCase):
    """Successes that are nonetheless wrong."""

    def by_url(self, url, column):
        return {url: [cl.Ref("Fonti_OSINT.csv", 2, "Example", column)]}

    def ok(self, final="", feedish=False):
        return cl.Attempt("success", 200, "HTTP 200", final, feedish)

    def test_a_feed_cell_serving_a_page_is_flagged(self):
        url = "https://example.org/feed/"
        found = cl.landing_findings(self.by_url(url, "RSS Feed"),
                                    {url: self.ok(url, feedish=False)})
        self.assertEqual([u for u, _ in found["feed"]], [url])

    def test_a_working_feed_is_not_flagged(self):
        url = "https://example.org/feed/"
        found = cl.landing_findings(self.by_url(url, "RSS Feed"),
                                    {url: self.ok(url, feedish=True)})
        self.assertEqual(found, {})

    def test_a_url_cell_is_judged_on_where_it_landed_not_on_feeds(self):
        url = "https://example.org/section"
        found = cl.landing_findings(self.by_url(url, "URL"),
                                    {url: self.ok("https://elsewhere.example/")})
        self.assertEqual([u for u, _ in found["host"]], [url])

    def test_a_url_that_stayed_put_is_not_flagged(self):
        url = "https://example.org/section"
        found = cl.landing_findings(self.by_url(url, "URL"), {url: self.ok(url)})
        self.assertEqual(found, {})

    def test_no_landing_bucket_is_ever_a_removal_candidate(self):
        # A page that moved is a stale cell, not a dead source. If these ever
        # become removal candidates, v0.5.0 is about to happen again with a
        # new cause.
        self.assertFalse(set(cl.LANDING_ORDER) & cl.REMOVAL_CANDIDATE_BUCKETS)

    def test_the_report_says_they_are_not_removal_candidates(self):
        url = "https://example.org/section"
        by_url = self.by_url(url, "URL")
        landings = cl.landing_findings(by_url, {url: self.ok("https://elsewhere.example/")})
        report = cl.render_report(by_url, {}, True, 3, [], landings)
        self.assertIn("None of them is a removal candidate", report)
        self.assertIn("https://elsewhere.example/", report)


class DiscoveryContractUnchanged(unittest.TestCase):
    """check_url() keeps its single-value contract for its other caller."""

    def test_landing_is_opt_in(self):
        # scripts/discover_candidates.py does `verdict = cl.check_url(url)`
        # and compares it to None. Returning a tuple by default would make
        # every candidate look rejected.
        import inspect

        signature = inspect.signature(cl.check_url)
        self.assertIs(signature.parameters["with_landing"].default, False)


class RecurringIssue(unittest.TestCase):
    """The month-to-month record goes to one issue, found by its title.

    The October and November 2026 runs commented on #41 instead of #3: the
    script took the newest open issue labelled `link-check`, and #41 — the
    redirect list — carried the label too.
    """

    def test_found_by_title_not_by_being_the_newest_labelled_issue(self):
        issues = [
            {"number": 41, "title": "208 catalogued URLs no longer point where they resolve"},
            {"number": 3, "title": cl.ISSUE_TITLE},
        ]
        self.assertEqual(cl.pick_issue(issues)["number"], 3)

    def test_a_pull_request_never_qualifies(self):
        issues = [{"number": 9, "title": cl.ISSUE_TITLE, "pull_request": {}}]
        self.assertIsNone(cl.pick_issue(issues))

    def test_no_match_means_a_new_issue(self):
        self.assertIsNone(cl.pick_issue([{"number": 41, "title": "something else"}]))

    def test_with_two_the_older_one_keeps_the_history(self):
        issues = [{"number": 50, "title": cl.ISSUE_TITLE},
                  {"number": 3, "title": cl.ISSUE_TITLE}]
        self.assertEqual(cl.pick_issue(issues)["number"], 3)


class PostingGoesToTheRecurringIssue(unittest.TestCase):
    """End to end against a fake GitHub API: where the parts land, in order."""

    def setUp(self):
        self.calls = []
        self.real = cl.api_request

        def fake(method, path, token, payload=None):
            self.calls.append((method, path, payload))
            if method == "GET":
                return self.listing
            if path.endswith("/issues"):
                return {"number": 77}
            return {}
        cl.api_request = fake

    def tearDown(self):
        cl.api_request = self.real

    def test_parts_go_to_the_titled_issue_in_order_not_to_41(self):
        self.listing = [
            {"number": 41, "title": "208 catalogued URLs no longer point where they resolve"},
            {"number": 3, "title": cl.ISSUE_TITLE},
        ]
        cl.post_to_github("o/r", "t", ["part one", "part two"])
        posts = [(path, payload["body"]) for method, path, payload in self.calls
                 if method == "POST"]
        self.assertEqual(posts, [("/repos/o/r/issues/3/comments", "part one"),
                                 ("/repos/o/r/issues/3/comments", "part two")])

    def test_without_the_issue_one_is_opened_and_the_parts_follow(self):
        self.listing = [{"number": 41, "title": "something else"}]
        cl.post_to_github("o/r", "t", ["only part"])
        posts = [(path, payload) for method, path, payload in self.calls if method == "POST"]
        self.assertEqual(posts[0][0], "/repos/o/r/issues")
        self.assertEqual(posts[0][1]["title"], cl.ISSUE_TITLE)
        self.assertEqual(posts[1], ("/repos/o/r/issues/77/comments", {"body": "only part"}))

class PostsOnlyFromActions(unittest.TestCase):
    """A token in the environment is not a reason to post.

    A local smoke test on 10 November 2026 posted a test report to #3
    because the machine had GITHUB_TOKEN set for other tools.
    """

    FULL = {"GITHUB_ACTIONS": "true", "GITHUB_TOKEN": "t", "GITHUB_REPOSITORY": "o/r"}

    def test_actions_with_token_and_repository_posts(self):
        self.assertTrue(cl.should_post(self.FULL))

    def test_a_token_on_a_developer_machine_does_not(self):
        local = {k: v for k, v in self.FULL.items() if k != "GITHUB_ACTIONS"}
        self.assertFalse(cl.should_post(local))

    def test_actions_without_a_token_does_not(self):
        self.assertFalse(cl.should_post({"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": "o/r"}))

class CommentKeepsEverythingAnyoneActsOn(unittest.TestCase):
    """A run the size of November 2026's reaches the issue whole.

    That run had 59 removal candidates and 989 anti-bot findings. Cut at the
    size limit wherever it fell, the comment ended inside the anti-bot list
    and the redirect section never appeared. A first fix — shorten the
    inconclusive lists until it fits — still did not fit once entries had
    realistic lengths: candidates and landings alone came to 67,615
    characters. So the comment is split between entries instead.
    """

    def setUp(self):
        self.by_url, self.buckets, self.landings = {}, {}, {}

        def add(kind, n, detail, store):
            for i in range(n):
                url = f"https://www.{kind}-{i}.example.gov.xx/en/section/page-{i}"
                self.by_url[url] = [cl.Ref("Fonti_OSINT.csv", 1000 + i,
                                           f"Realistic Source Name Number {i}", "RSS Feed")]
                store.setdefault(kind, []).append((url, cl.Verdict(kind, detail)))

        three = "; ".join(f"attempt {i}: HTTP 403, matched anti-bot marker 'just a moment...'"
                          for i in (1, 2, 3))
        november = {"gone": 57, "parked": 2, "unreachable": 92, "blocked": 989,
                    "empty": 2, "http_error": 22, "timeout": 60, "tls_error": 104,
                    "other": 9}
        for bucket, n in november.items():
            add(bucket, n, three, self.buckets)
        for kind, n in {"feed": 16, "home": 30, "host": 149, "path": 43}.items():
            add(kind, n, "HTTP 200, landed on https://www.somewhere-else.example.com/a/b",
                self.landings)
        report = cl.render_report(self.by_url, self.buckets, True, 3, [], self.landings,
                                  cl.COMMENT_LIST_LIMIT, "the job summary")
        self.parts = cl.split_for_github(report)

    def test_every_part_fits(self):
        for part in self.parts:
            self.assertLessEqual(len(part), cl.GITHUB_BODY_LIMIT)

    def test_every_removal_candidate_and_every_landing_arrives(self):
        posted = "\n".join(self.parts)
        for bucket in cl.REMOVAL_CANDIDATE_BUCKETS:
            for url, _ in self.buckets[bucket]:
                self.assertIn(url, posted)
        for entries in self.landings.values():
            for url, _ in entries:
                self.assertIn(url, posted)

    def test_no_entry_is_split_across_two_comments(self):
        for part in self.parts:
            lines = part.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("- `"):
                    self.assertTrue(i + 1 < len(lines) and lines[i + 1].startswith("  "),
                                    f"entry without its detail: {line[:60]}")

    def test_continuations_say_what_they_continue(self):
        self.assertGreater(len(self.parts), 1)
        for i, part in enumerate(self.parts[1:], start=2):
            self.assertIn(f"continued ({i}/{len(self.parts)})", part.split("\n", 1)[0])

    def test_landings_come_before_the_inconclusive_findings(self):
        posted = "\n".join(self.parts)
        self.assertLess(posted.index("## Answered, but not where"),
                        posted.index("## Inconclusive"))

    def test_what_was_left_out_is_counted_and_pointed_to(self):
        posted = "\n".join(self.parts)
        hidden = len(self.buckets["blocked"]) - cl.COMMENT_LIST_LIMIT
        self.assertIn(f"- … and {hidden} more, listed in full in the job summary.", posted)

    def test_the_full_report_still_lists_everything_and_fits_the_summary(self):
        full = cl.render_report(self.by_url, self.buckets, True, 3, [], self.landings)
        for url, _ in self.buckets["blocked"]:
            self.assertIn(url, full)
        self.assertNotIn("… and", full)
        self.assertLessEqual(len(full), cl.STEP_SUMMARY_LIMIT)

    def test_a_small_run_is_one_comment_unchanged(self):
        small = {"blocked": self.buckets["blocked"][:3], "gone": self.buckets["gone"][:2]}
        report = cl.render_report(self.by_url, small, True, 3, [], None,
                                  cl.COMMENT_LIST_LIMIT, "the job summary")
        self.assertEqual(cl.split_for_github(report), [report])

    def test_truncation_respects_its_limit(self):
        self.assertLessEqual(len(cl.truncate_for_github("x" * 70_000)), cl.GITHUB_BODY_LIMIT)
        self.assertLessEqual(len(cl.fit_report(self.by_url, self.buckets, True, 3, [],
                                               self.landings, 2_000, "x")), 2_000)


class AttemptsAreDescribedOnce(unittest.TestCase):
    """Three identical failures are one fact, said once."""

    def attempt(self, detail):
        return cl.Attempt("gone", 404, detail)

    def test_identical_attempts_collapse(self):
        same = [self.attempt("HTTP 404 — gone")] * 3
        self.assertEqual(cl.describe_attempts(same), "3 attempts: HTTP 404 — gone")

    def test_differing_attempts_are_each_kept(self):
        mixed = [self.attempt("HTTP 404"), self.attempt("HTTP 503")]
        self.assertEqual(cl.describe_attempts(mixed), "attempt 1: HTTP 404; attempt 2: HTTP 503")

    def test_a_single_attempt_reads_as_before(self):
        self.assertEqual(cl.describe_attempts([self.attempt("HTTP 404")]), "attempt 1: HTTP 404")

if __name__ == "__main__":
    unittest.main(verbosity=2)
