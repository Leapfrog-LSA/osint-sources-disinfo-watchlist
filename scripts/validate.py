#!/usr/bin/env python3
"""
Validate the datasets in this repository.

Run locally before opening a pull request:

    python scripts/validate.py

Exits non-zero if any dataset breaks the conventions documented in
README.md and CONTRIBUTING.md. Reports every problem found, not just
the first one, so a contributor can fix them in one pass.

Standard library only — no dependencies to install.
"""

import csv
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent

OSINT_CSV = REPO / "Fonti_OSINT.csv"
DISINFO_CSV = REPO / "disinfo_sources_master.csv"

# --------------------------------------------------------------------------
# Controlled vocabularies
# --------------------------------------------------------------------------

OSINT_COLUMNS = [
    "Macro-categoria", "Sottosezione", "Fonte", "URL",
    "RSS Feed", "Lingua", "Paese / Area", "Accesso", "Note", "Provenienza",
]

# `Provenienza` records which directory a row came from and in which batch, as
# `<list>:<YYYY-MM>` — e.g. `ifcn:2026-08`. It exists so a batch can be
# measured and, if it turns out to be bad, removed in one operation instead of
# being re-read row by row.
#
# Empty means "not determined", the same as every other optional field here:
# the rows that predate the field were curated by hand over time and their
# origin is genuinely unknown. Filling them with a guess would defeat the point
# of having the column.
PROVENANCE = re.compile(r"^[a-z0-9][a-z0-9._-]*:\d{4}-(0[1-9]|1[0-2])$")

DISINFO_COLUMNS = [
    "domain", "impersonated_outlet", "authentic_domain", "country", "tld",
    "first_seen", "campaign", "attribution", "source", "evidence_level",
    "cats_flag", "notes",
]

MACRO_CATEGORIES = {
    "📰 Media & Testate Giornalistiche",
    "🧩 Settori Specifici",
    "🔓 Open Data & Trasparenza",
    "📊 Statistiche & Dati Macroeconomici",
    "🏢 Registri Aziendali & Corporate Intelligence",
    "🔐 Cybersecurity & Digital OSINT",
    "🎓 Geopolitica & Intelligence",
    "📡 Social Media & Media Monitoring",
    "⚖️ Sanzioni, PEP & Compliance",
    "🌿 Sostenibilità & ESG",
    "🕊️ Diritti Umani & Giudiziario",
    "✅ Fact-Checking & Disinformazione",
}

# Supranational / regional scopes accepted in `Paese / Area` where no single
# ISO 3166-1 country applies (e.g. a pan-African outlet).
REGIONS = {
    "Globale", "Europa", "Africa", "Asia", "Americhe", "Pacifico",
    "Pan-Africa", "Pan-Asia", "Pan-Arab", "LatAm", "MENA", "Caraibi",
    "Balcani", "Caucaso", "Nordics", "CEE", "Golfo", "NATO", "BRICS",
    "Asia Centrale", "Asia-Pacifico", "SE Asia",
    "Africa Occ.", "Africa Or.", "Nord America", "America Centrale",
    "EU+EEA", "INTL",
}

ACCESS_TYPES = {
    "Gratuito", "Pubblico", "Freemium", "A pagamento",
    "Open Source", "Commerciale", "Community", "Premium",
    "Enterprise", "Self-hosted", "Waitlist",
}

EVIDENCE_LEVELS = {"forensic", "journalistic", "judicial", "debunker"}

CATS_FLAGS = {
    "disinformation_clone", "fake_news_portal", "fake_news_site",
    "satire_recognizable", "suspect_source", "suspected",
}

# Place names as the `Note` column spells them, mapped to the country whose
# code the row should carry. This list is written here rather than learned from
# the catalogue on purpose: a wrong code that appears three times teaches a
# learned dictionary to expect it, which is exactly how "Sud Sudan" would have
# taught itself to mean `SD`.
#
# Only names that a `Note` actually leads with are worth carrying. Subdivisions
# are included because two of the wrong codes found so far were subdivisions
# read as countries: `BZ` for Alto Adige is Belize, and `MX` for New Mexico is
# Mexico.
PLACE_COUNTRY = {
    # Countries
    "afghanistan": "AF", "albania": "AL", "algeria": "DZ", "andorra": "AD",
    "angola": "AO", "arabia saudita": "SA", "argentina": "AR", "armenia": "AM",
    "australia": "AU", "austria": "AT", "azerbaigian": "AZ", "bahamas": "BS",
    "bahrein": "BH", "bangladesh": "BD", "barbados": "BB", "belgio": "BE",
    "belize": "BZ", "benin": "BJ", "bhutan": "BT", "bielorussia": "BY",
    "bolivia": "BO", "bosnia": "BA", "bosnia ed erzegovina": "BA",
    "botswana": "BW", "brasile": "BR", "brunei": "BN", "bulgaria": "BG",
    "burkina faso": "BF", "burundi": "BI", "cambogia": "KH", "camerun": "CM",
    "canada": "CA", "capo verde": "CV", "ciad": "TD", "cile": "CL",
    "cina": "CN", "cipro": "CY", "colombia": "CO", "comore": "KM",
    "corea": "KR", "corea del sud": "KR", "corea del nord": "KP",
    "costa d'avorio": "CI", "costa rica": "CR", "croazia": "HR", "cuba": "CU",
    "danimarca": "DK", "ecuador": "EC", "egitto": "EG", "el salvador": "SV",
    "emirati arabi uniti": "AE", "eritrea": "ER", "estonia": "EE",
    "eswatini": "SZ", "etiopia": "ET", "figi": "FJ", "filippine": "PH",
    "finlandia": "FI", "francia": "FR", "gabon": "GA", "gambia": "GM",
    "georgia": "GE", "germania": "DE", "ghana": "GH", "giamaica": "JM",
    "giappone": "JP", "gibuti": "DJ", "giordania": "JO", "grecia": "GR",
    "guatemala": "GT", "guinea": "GN", "guinea equatoriale": "GQ",
    "guinea-bissau": "GW", "guyana": "GY", "haiti": "HT", "honduras": "HN",
    "hong kong": "HK", "india": "IN", "indonesia": "ID", "iran": "IR",
    "iraq": "IQ", "irlanda": "IE", "islanda": "IS", "israele": "IL",
    "italia": "IT", "kazakistan": "KZ", "kenya": "KE", "kirghizistan": "KG",
    "kosovo": "XK", "kuwait": "KW", "laos": "LA", "lesotho": "LS",
    "lettonia": "LV", "libano": "LB", "liberia": "LR", "libia": "LY",
    "lituania": "LT", "lussemburgo": "LU", "macao": "MO",
    "macedonia del nord": "MK", "madagascar": "MG", "malawi": "MW",
    "malaysia": "MY", "maldive": "MV", "mali": "ML", "malta": "MT",
    "marocco": "MA", "mauritania": "MR", "mauritius": "MU", "messico": "MX",
    "moldavia": "MD", "monaco": "MC", "mongolia": "MN", "montenegro": "ME",
    "mozambico": "MZ", "myanmar": "MM", "namibia": "NA", "nepal": "NP",
    "nicaragua": "NI", "niger": "NE", "nigeria": "NG", "norvegia": "NO",
    "nuova zelanda": "NZ", "oman": "OM", "paesi bassi": "NL", "pakistan": "PK",
    "palestina": "PS", "panama": "PA", "papua nuova guinea": "PG",
    "paraguay": "PY", "perù": "PE", "polonia": "PL", "porto rico": "PR",
    "portogallo": "PT", "qatar": "QA", "rd congo": "CD", "regno unito": "GB",
    "rep. ceca": "CZ", "rep. dominicana": "DO", "romania": "RO", "ruanda": "RW",
    "russia": "RU", "senegal": "SN", "serbia": "RS", "seychelles": "SC",
    "sierra leone": "SL", "singapore": "SG", "siria": "SY", "slovacchia": "SK",
    "slovenia": "SI", "somalia": "SO", "spagna": "ES", "sri lanka": "LK",
    "sud sudan": "SS", "sudafrica": "ZA", "sudan": "SD", "suriname": "SR",
    "svezia": "SE", "svizzera": "CH", "tagikistan": "TJ", "taiwan": "TW",
    "tanzania": "TZ", "thailandia": "TH", "togo": "TG", "trinidad": "TT",
    "tunisia": "TN", "turchia": "TR", "turkmenistan": "TM", "ucraina": "UA",
    "uganda": "UG", "ungheria": "HU", "uruguay": "UY", "uzbekistan": "UZ",
    "vaticano": "VA", "venezuela": "VE", "vietnam": "VN", "yemen": "YE",
    "zambia": "ZM", "zimbabwe": "ZW",
    # Regions and states, which is where two of the wrong codes hid. Cities are
    # deliberately absent: a note that opens with a city is giving a location,
    # not claiming a country, and `Berlino` on an EU think tank is not a
    # mistake about Germany.
    "abruzzo": "IT", "alto adige": "IT", "basilicata": "IT", "calabria": "IT",
    "liguria": "IT", "sicilia": "IT", "toscana": "IT",
    "andalusia": "ES", "canarie": "ES", "catalogna": "ES", "galizia": "ES",
    "paesi baschi": "ES", "comunità valenciana": "ES",
    "baden-württemberg": "DE", "baviera": "DE", "sassonia": "DE",
    "occitania": "FR", "paca": "FR",
    "scozia": "GB", "irlanda del nord": "GB", "galles": "GB",
    "california": "US", "connecticut": "US", "florida": "US", "michigan": "US",
    "minnesota": "US", "montana": "US", "new mexico": "US",
    "north carolina": "US", "ohio": "US", "oklahoma": "US", "oregon": "US",
    "pennsylvania": "US", "south carolina": "US", "texas": "US",
    "virginia": "US", "wisconsin": "US", "wyoming": "US",
    "gujarat": "IN", "karnataka": "IN", "kashmir": "IN", "kerala": "IN",
    "maharashtra": "IN", "tamil nadu": "IN",
}

ISO2 = re.compile(r"^[A-Z]{2}$")
LANG_TOKEN = re.compile(r"^[A-Z]{2,3}$")          # ISO 639-1, or 639-3 where no 2-letter code exists
SUBDIVISION = re.compile(r"^[A-Z]{2}-[\w\-À-ÿ]+$")  # ISO 3166-2 style, e.g. IT-Lombardia, GB-SCT
DATE = re.compile(r"^\d{4}(-\d{2}-\d{2})?$")


# --------------------------------------------------------------------------

class Report:
    """Errors fail the run; warnings are printed and do not.

    A check earns the right to fail CI by being precise. The one warning here
    flags pairs a person should look at, and on the catalogue as it stands it
    is right about a third of the time — useful to see, wrong to block on.
    """

    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, dataset, line, column, message):
        self.errors.append((dataset, line, column, message))

    def warn(self, dataset, line, column, message):
        self.warnings.append((dataset, line, column, message))

    @staticmethod
    def _print_group(items, label):
        by_dataset = {}
        for dataset, line, column, message in items:
            by_dataset.setdefault(dataset, []).append((line, column, message))
        for dataset, rows in by_dataset.items():
            print(f"\n{dataset} — {len(rows)} {label}:")
            for line, column, message in rows[:100]:
                print(f"  line {line}, column '{column}': {message}")
            if len(rows) > 100:
                print(f"  ... and {len(rows) - 100} more")

    def summary(self):
        if self.warnings:
            self._print_group(self.warnings, "thing(s) worth a look")
        if not self.errors:
            return True
        self._print_group(self.errors, "problem(s)")
        print(f"\nFAILED — {len(self.errors)} problem(s) total.")
        return False


def valid_url(value):
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def canonical_url(value):
    """A URL reduced to what identifies the resource.

    `http://x.org/news`, `https://www.x.org/news/` and `https://x.org:443/news`
    are one page written three ways. The old check compared URLs verbatim apart
    from case and a trailing slash, so it saw three distinct rows. Scheme,
    `www.`, a default port and that trailing slash all come off here; the query
    string stays, because `?id=1` and `?id=2` are different pages.
    """
    parsed = urlparse(value.strip())
    host = parsed.netloc.lower().rsplit("@", 1)[-1]
    for port in (":80", ":443"):
        if host.endswith(port):
            host = host[: -len(port)]
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/").lower()
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{host}{path}{query}"


def url_host(value):
    """The registrable host, without `www.` or a port."""
    return canonical_url(value).split("/")[0]


def url_path(value):
    """The canonical path, or "" for a homepage."""
    canonical = canonical_url(value)
    _, _, rest = canonical.partition("/")
    return f"/{rest}" if rest else ""


def valid_place(token):
    """A single `Paese / Area` token: country, subdivision, or region."""
    return bool(ISO2.match(token)) or bool(SUBDIVISION.match(token)) or token in REGIONS


def read_csv(path, expected_columns, report, dataset):
    if not path.exists():
        report.error(dataset, 0, "-", f"file not found: {path.name}")
        return None
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        report.error(dataset, 0, "-", "file is empty")
        return None
    actual = list(rows[0].keys())
    if actual != expected_columns:
        report.error(dataset, 1, "-",
                     f"header mismatch\n    expected: {expected_columns}\n    found:    {actual}")
        return None
    return rows


def validate_osint(report):
    dataset = OSINT_CSV.name
    rows = read_csv(OSINT_CSV, OSINT_COLUMNS, report, dataset)
    if rows is None:
        return

    seen_urls = {}
    seen_names = {}
    by_host = {}

    for index, row in enumerate(rows):
        line = index + 2  # +1 for header, +1 for 1-based numbering

        if any(value is None for value in row.values()):
            report.error(dataset, line, "-", "wrong number of fields")
            continue

        for column in ("Macro-categoria", "Sottosezione", "Fonte", "URL"):
            if not row[column].strip():
                report.error(dataset, line, column, "required field is empty")

        macro = row["Macro-categoria"].strip()
        if macro and macro not in MACRO_CATEGORIES:
            report.error(dataset, line, "Macro-categoria", f"unknown category {macro!r}")

        url = row["URL"].strip()
        if url:
            if not valid_url(url):
                report.error(dataset, line, "URL", f"not a valid http(s) URL: {url!r}")
            else:
                key = canonical_url(url)
                if key in seen_urls:
                    report.error(dataset, line, "URL",
                                 f"duplicate of line {seen_urls[key]}: {url!r} is the "
                                 f"same page, written differently")
                else:
                    seen_urls[key] = line
                by_host.setdefault(url_host(url), []).append(
                    (line, row["Fonte"].strip(), url_path(url), url))

        feed = row["RSS Feed"].strip()
        if feed and not valid_url(feed):
            report.error(dataset, line, "RSS Feed", f"not a valid http(s) URL: {feed!r}")

        lingua = row["Lingua"].strip()
        if lingua:
            for token in (part.strip() for part in lingua.split("/")):
                if token != "Multi" and not LANG_TOKEN.match(token):
                    report.error(dataset, line, "Lingua",
                                 f"{token!r} is not an uppercase ISO 639 code or 'Multi'")

        place = row["Paese / Area"].strip()
        if place:
            for token in (part.strip() for part in place.split("/")):
                if not valid_place(token):
                    report.error(dataset, line, "Paese / Area",
                                 f"{token!r} is not an ISO 3166 code, a subdivision, "
                                 f"or a documented region")

        access = row["Accesso"].strip()
        if access and access not in ACCESS_TYPES:
            report.error(dataset, line, "Accesso",
                         f"{access!r} is not in the controlled vocabulary "
                         f"({', '.join(sorted(ACCESS_TYPES))})")

        # Two rows may legitimately share a `Fonte`: "National Bureau of
        # Statistics" is Nigeria, Tanzania and Antigua, and "The Sun" is a
        # British tabloid and a Nigerian daily. What separates those from a
        # genuine duplicate is the country — so a repeated name is only an
        # error when the rows do not distinguish themselves by one.
        #
        # On the catalogue as it stands this flags 5 of 22 repeated names, and
        # all five were real: a bulk import had added an organisation's
        # corporate site under the name of its fact-checking arm, while the
        # actual fact-check page was already catalogued. The other 17 are
        # statistical offices and namesake newspapers in different countries.
        name = row["Fonte"].strip().lower()
        place = row["Paese / Area"].strip()
        if name:
            for prev_line, prev_place in seen_names.get(name, ()):
                if not place or not prev_place or place == prev_place:
                    where = f"both {place!r}" if place and place == prev_place else "no country to tell them apart"
                    report.error(dataset, line, "Fonte",
                                 f"{row['Fonte'].strip()!r} also on line {prev_line} — "
                                 f"{where}. Same organisation? Merge them. Different "
                                 f"ones? Give each its `Paese / Area`, or a name that "
                                 f"distinguishes them")
                    break
            seen_names.setdefault(name, []).append((line, place))

        provenance = row["Provenienza"].strip()
        if provenance and not PROVENANCE.match(provenance):
            report.error(dataset, line, "Provenienza",
                         f"{provenance!r} is not `<list>:<YYYY-MM>` "
                         f"(e.g. 'ifcn:2026-08'); leave it empty if unknown")

        warn_place_disagrees(row, line, report, dataset)

    warn_nested_paths(by_host, report, dataset)


def note_place(note):
    """The place name a `Note` leads with, if it leads with one.

    Notes in this catalogue open with the place and then say what the source
    is: `Sud Sudan — radio/news Juba`. Only that leading phrase is read, so
    `Guinea` inside `Papua Nuova Guinea` is not mistaken for Guinea, and
    `Sudan` inside `Sud Sudan` is not mistaken for Sudan.
    """
    head = re.split(r"[—–·|(;]", note, 1)[0].strip()
    if not 1 <= len(head.split()) <= 3 or len(head) < 4:
        return ""
    return head.casefold()


def warn_place_disagrees(row, line, report, dataset):
    """Flag a row whose `Note` names one country and whose code says another.

    Every wrong country code found so far has been a *valid* ISO code, so
    `valid_place` accepts all of them and always will: `SD` for South Sudan,
    `BZ` (Belize) for Alto Adige, `BE` (Belgium) for Belarus — a language code
    copied into the wrong column — and `MX` for New Mexico. Nothing in the row
    is malformed. The only thing that disagrees is the prose next to it.

    This is a warning rather than an error because the catalogue deliberately
    files some sources by subject instead of by publisher: 38 North is a US
    think tank writing about North Korea, DVB is Oslo-based and writes about
    Burma. Those are the shape this check cannot tell from a mistake, and on
    the catalogue as it stands they are most of what it prints.
    """
    place = row["Paese / Area"].strip()
    want = PLACE_COUNTRY.get(note_place(row["Note"]))
    if not place or not want:
        return
    codes = {token.strip() for token in place.split("/")}
    if want in codes or want in {code.split("-")[0] for code in codes}:
        return
    report.warn(dataset, line, "Paese / Area",
                f"{place!r}, but the note opens with "
                f"{note_place(row['Note'])!r}, which is {want}. A source "
                f"filed by subject rather than by publisher, or the wrong "
                f"country?")


def warn_nested_paths(by_host, report, dataset):
    """Flag one row whose URL sits inside another's on the same host.

    A repeated host is almost always fine — 106 hosts appear on more than one
    row, and `github.com`, `gov.br` and `ec.europa.eu` account for much of it.
    Flagging every one of them would report 106 pairs of nothing and be
    ignored, the same way a bare name-collision check would have been.

    What is worth a second look is narrower: two rows on one host where one
    URL is a path *inside* the other. Most are still legitimate — `bbc.com/news`
    and `bbc.com/news/world` are different desks — but this is the shape a real
    near-duplicate takes, and on the catalogue as it stands it finds 11 pairs,
    of which about a third are two rows for one thing under two names.

    A third is too low to fail a build on and far too high to throw away, so
    these are warnings: printed, counted, and left to a person.
    """
    for host, entries in sorted(by_host.items()):
        if len(entries) < 2:
            continue
        for i, first in enumerate(entries):
            for second in entries[i + 1:]:
                if not first[2] or not second[2]:
                    continue
                inner, outer = sorted((first, second), key=lambda e: len(e[2]))
                if not outer[2].startswith(f"{inner[2]}/"):
                    continue
                report.warn(dataset, outer[0], "URL",
                            f"{outer[3]!r} sits inside line {inner[0]}'s "
                            f"{inner[3]!r} on {host}. Two sections of one site, "
                            f"or one source entered twice?")


def validate_disinfo(report):
    dataset = DISINFO_CSV.name
    rows = read_csv(DISINFO_CSV, DISINFO_COLUMNS, report, dataset)
    if rows is None:
        return

    seen_domains = {}

    for index, row in enumerate(rows):
        line = index + 2

        if any(value is None for value in row.values()):
            report.error(dataset, line, "-", "wrong number of fields")
            continue

        for column in ("domain", "campaign", "source", "evidence_level", "cats_flag"):
            if not row[column].strip():
                report.error(dataset, line, column, "required field is empty")

        domain = row["domain"].strip().lower()
        if domain and domain != "n/a":
            if domain in seen_domains:
                report.error(dataset, line, "domain",
                             f"duplicate of line {seen_domains[domain]}: {domain!r}")
            else:
                seen_domains[domain] = line

        for token in (part.strip() for part in row["evidence_level"].split("+")):
            if token and token not in EVIDENCE_LEVELS:
                report.error(dataset, line, "evidence_level",
                             f"{token!r} is not one of {', '.join(sorted(EVIDENCE_LEVELS))}")

        flag = row["cats_flag"].strip()
        if flag and flag not in CATS_FLAGS:
            report.error(dataset, line, "cats_flag",
                         f"{flag!r} is not one of {', '.join(sorted(CATS_FLAGS))}")

        country = row["country"].strip()
        if country:
            for token in (part.strip() for part in country.split("/")):
                if not valid_place(token):
                    report.error(dataset, line, "country",
                                 f"{token!r} is not an ISO 3166 code or a documented region")

        first_seen = row["first_seen"].strip()
        if first_seen and not DATE.match(first_seen):
            report.error(dataset, line, "first_seen",
                         f"{first_seen!r} is not YYYY or YYYY-MM-DD")


def main():
    report = Report()
    validate_osint(report)
    validate_disinfo(report)

    if report.summary():
        osint_rows = sum(1 for _ in csv.DictReader(OSINT_CSV.open(encoding="utf-8")))
        disinfo_rows = sum(1 for _ in csv.DictReader(DISINFO_CSV.open(encoding="utf-8")))
        note = ("No problems found." if not report.warnings else
                f"No problems found; {len(report.warnings)} warning(s) above, "
                f"which do not fail this check.")
        print(f"OK — {OSINT_CSV.name}: {osint_rows} rows, "
              f"{DISINFO_CSV.name}: {disinfo_rows} rows. {note}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
