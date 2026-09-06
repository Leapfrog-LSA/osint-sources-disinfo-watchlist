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

ISO2 = re.compile(r"^[A-Z]{2}$")
LANG_TOKEN = re.compile(r"^[A-Z]{2,3}$")          # ISO 639-1, or 639-3 where no 2-letter code exists
SUBDIVISION = re.compile(r"^[A-Z]{2}-[\w\-À-ÿ]+$")  # ISO 3166-2 style, e.g. IT-Lombardia, GB-SCT
DATE = re.compile(r"^\d{4}(-\d{2}-\d{2})?$")


# --------------------------------------------------------------------------

class Report:
    def __init__(self):
        self.errors = []

    def error(self, dataset, line, column, message):
        self.errors.append((dataset, line, column, message))

    def summary(self):
        if not self.errors:
            return True
        by_dataset = {}
        for dataset, line, column, message in self.errors:
            by_dataset.setdefault(dataset, []).append((line, column, message))
        for dataset, items in by_dataset.items():
            print(f"\n{dataset} — {len(items)} problem(s):")
            for line, column, message in items[:100]:
                print(f"  line {line}, column '{column}': {message}")
            if len(items) > 100:
                print(f"  ... and {len(items) - 100} more")
        print(f"\nFAILED — {len(self.errors)} problem(s) total.")
        return False


def valid_url(value):
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


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
                key = url.lower().rstrip("/")
                if key in seen_urls:
                    report.error(dataset, line, "URL",
                                 f"duplicate of line {seen_urls[key]}: {url!r}")
                else:
                    seen_urls[key] = line

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
        print(f"OK — {OSINT_CSV.name}: {osint_rows} rows, "
              f"{DISINFO_CSV.name}: {disinfo_rows} rows. No problems found.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
