"""Tests for name_check.py — the rule a page must pass before it becomes a row.

Each refusal here is one a looser rule actually let through during an import.
No network requests.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import name_check as nc  # noqa: E402


class Acronyms(unittest.TestCase):
    def test_reads_an_acronym_in_brackets(self):
        self.assertEqual(nc.acronyms("Algerian National Institute of Industrial Property (INAPI)"),
                         ["INAPI"])

    def test_two_letters_are_not_an_acronym(self):
        # `(KG)` is printed on every page of every site under `.kg`.
        self.assertEqual(nc.acronyms("State Service of Intellectual Property (KG)"), [])

    def test_a_bracketed_word_is_not_an_acronym(self):
        self.assertEqual(nc.acronyms("Corporate Registry (Province of British Columbia)"), [])

    def test_mixed_case_acronym_counts(self):
        self.assertEqual(nc.acronyms("Jebel Ali Free Zone Authority (JAfza)"), ["JAfza"])


class Distinctive(unittest.TestCase):
    def test_drops_articles_and_prepositions(self):
        self.assertEqual(nc.distinctive("Chambre de Commerce et d'Industrie du Bénin"),
                         ["chambre", "commerce", "industrie", "benin"])

    def test_keeps_generic_nouns(self):
        # Dropping "national" and "office" would let this pass on "statistics".
        self.assertEqual(nc.distinctive("National Office of Statistics"),
                         ["national", "office", "statistics"])

    def test_folds_accents_and_case(self):
        self.assertEqual(nc.distinctive("Société GÉNÉRALE"), ["societe", "generale"])

    def test_a_bracketed_qualifier_stays_part_of_the_name(self):
        # Only an acronym comes off. `(Yukon)` is what tells this registry
        # from Alberta's.
        self.assertEqual(nc.distinctive("Corporate Registry (Yukon)"),
                         ["corporate", "registry", "yukon"])

    def test_letters_without_a_decomposition_are_folded(self):
        self.assertEqual(nc.distinctive("Główny Urząd"), ["glowny", "urzad"])
        self.assertEqual(nc.words("ODASI"), nc.words("Odası"))
        self.assertEqual(nc.words("København"), ["kobenhavn"])

    def test_a_soft_hyphen_does_not_split_a_word(self):
        self.assertEqual(nc.words("Bundes\u00adanzeiger"), ["bundesanzeiger"])

    def test_a_vowel_sign_does_not_split_a_word(self):
        # `\w` does not match an Indic vowel sign; splitting on it made
        # fragments that matched inside longer words.
        self.assertEqual(len(nc.words("कानूनी सहायता")), 2)

    def test_keeps_non_latin_words(self):
        self.assertEqual(nc.distinctive("Агенция по вписванията"),
                         ["агенция", "по", "вписванията"])


class StatesName(unittest.TestCase):
    def test_every_word_present_passes(self):
        page = "Welcome to the Securities and Exchange Commission of Ghana"
        self.assertEqual(nc.states_name("Securities and Exchange Commission Ghana", page), "words")

    def test_one_word_of_two_does_not_pass(self):
        # The first version of this rule accepted a single word, and passed
        # "Business News" on any site about business.
        self.assertEqual(nc.states_name("Business News", "Latest business headlines"), "")

    def test_words_match_across_accents_and_case(self):
        page = "JUNTA COMERCIAL DO PARANA — serviços"
        self.assertEqual(nc.states_name("Junta Comercial do Paraná", page), "words")

    def test_a_word_inside_another_does_not_count(self):
        # "court" is not stated by "courtesy".
        self.assertEqual(nc.states_name("Alderney Court", "Alderney courtesy desk"), "")

    def test_acronym_passes_as_a_word_in_the_same_capitals(self):
        self.assertEqual(nc.states_name("Servicio de Rentas Internas (SRI)", "Portal SRI en línea"),
                         "acronym")

    def test_acronym_in_other_capitals_does_not_pass(self):
        self.assertEqual(nc.states_name("Instituto X (SAR)", "el sar de la costa"), "")

    def test_acronym_inside_a_longer_word_does_not_pass(self):
        self.assertEqual(nc.states_name("Instituto X (SAR)", "SARDINIA tourism"), "")

    def test_name_as_the_domain_passes(self):
        self.assertEqual(nc.states_name("Fact Check Cyprus", "Home", "www.factcheckcyprus.org"),
                         "domain")

    def test_acronym_as_the_domain_passes(self):
        self.assertEqual(nc.states_name("Some Long Name (INAPI)", "Accueil", "inapi.gov.dz"),
                         "domain")

    def test_a_subdomain_is_not_the_domain(self):
        # `news.example.com` is a section of someone's site.
        self.assertEqual(nc.states_name("News", "Home", "news.example.com"), "")

    def test_an_ip_address_has_no_name(self):
        self.assertEqual(nc.states_name("168", "x", "192.168.100.200"), "")

    def test_another_bodys_page_does_not_pass_on_a_dropped_qualifier(self):
        page = "Alberta Corporate Registry — Service Alberta"
        self.assertEqual(nc.states_name("Corporate Registry (Yukon)", page), "")

    def test_a_longer_word_does_not_state_a_shorter_one(self):
        self.assertEqual(nc.states_name("कानून", "कानूनी सहायता"), "")

    def test_generic_labels_are_not_the_domain(self):
        self.assertEqual(nc.states_name("Gov", "Home", "www.gov.fk"), "")

    def test_empty_name_never_passes(self):
        self.assertEqual(nc.states_name("", "anything at all"), "")

    def test_a_name_in_another_language_is_not_confirmed(self):
        # Not confirmed is not the same as wrong: Jordan's Companies Control
        # Department says who it is, in Arabic. A person reads those.
        self.assertEqual(nc.states_name("Companies Control Department",
                                        "دائرة مراقبة الشركات"), "")

    def test_a_hijacked_domain_does_not_pass(self):
        # GLEIF's list gives rmi-mof.com for the Marshall Islands' Ministry of
        # Finance. In November 2026 it answered 200 with a gambling page.
        page = "Top 10 Game Bắn Cá Đổi Thưởng Uy Tín Nhất 2026"
        self.assertEqual(nc.states_name("Ministry of Finance", page, "rmi-mof.com"), "")

    def test_another_bodys_site_does_not_pass(self):
        # GANHRI's member list links Spain's Defensor del Pueblo to the Slovak
        # centre's site.
        page = "SNSLP – Slovenské národné stredisko pre ľudské práva"
        self.assertEqual(nc.states_name("Defensor del Pueblo", page, "www.snslp.sk"), "")


class VisibleText(unittest.TestCase):
    def test_scripts_and_styles_are_not_text(self):
        markup = "<p>Registro</p><script>var Mercantil = 1</script><style>.Central{}</style>"
        self.assertEqual(nc.visible_text(markup), "Registro")

    def test_alt_and_content_attributes_are_read(self):
        markup = '<img alt="Guernsey Registry"><meta name="description" content="Company search">'
        text = nc.visible_text(markup)
        self.assertIn("Guernsey Registry", text)
        self.assertIn("Company search", text)

    def test_an_apostrophe_does_not_end_a_quoted_attribute(self):
        # The name of a body whose name is its logo is only in the `alt`.
        markup = '<img alt="Chambre de Commerce et d\'Industrie du Bénin">'
        self.assertEqual(nc.states_name("Chambre de Commerce et d'Industrie du Bénin",
                                        nc.visible_text(markup)), "words")

    def test_commented_out_markup_is_not_text(self):
        # A reused template with the old owner's name commented out.
        markup = "<title>Casino 88</title><!-- <h1>Ministry of Finance</h1> -->"
        self.assertEqual(nc.states_name("Ministry of Finance", nc.visible_text(markup)), "")

    def test_an_attribute_inside_a_script_is_not_text(self):
        markup = '<script>el.title="Ministry of Finance";</script><p>Casino</p>'
        self.assertEqual(nc.visible_text(markup), "Casino")

    def test_a_data_attribute_is_not_shown_text(self):
        self.assertEqual(nc.visible_text('<div data-title="Ministry of Finance">x</div>'), "x")

    def test_entities_are_decoded(self):
        self.assertEqual(nc.visible_text("<h1>Commerce &amp; Industry</h1>"),
                         "Commerce & Industry")

    def test_decode_honours_a_declared_charset(self):
        body = '<meta charset="iso-8859-1"><title>Cámara</title>'.encode("iso-8859-1")
        self.assertIn("Cámara", nc.decode(body))

    def test_decode_falls_back_to_the_servers_charset(self):
        body = "<title>Cámara de Comercio</title>".encode("iso-8859-1")
        self.assertIn("Cámara", nc.decode(body, "iso-8859-1"))

    def test_decode_survives_a_codec_that_is_not_for_text(self):
        body = b'<meta charset="idna"><title>Registry</title>'
        self.assertIn("Registry", nc.decode(body))

    def test_decode_survives_an_unknown_charset(self):
        body = b'<meta charset="not-a-charset"><title>Registry</title>'
        self.assertIn("Registry", nc.decode(body))


if __name__ == "__main__":
    unittest.main()
