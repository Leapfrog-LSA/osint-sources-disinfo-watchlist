#!/usr/bin/env python3
"""
Count what the datasets hold, and check that the README says the same.

    python scripts/stats.py            # print the figures
    python scripts/stats.py --check    # fail if README.md disagrees
    python scripts/stats.py --check --release   # also check CITATION.cff

README.md states a total, twelve category counts, five coverage percentages,
the number of unstamped rows and the size of the watchlist. Until this script
existed nothing compared them with the CSVs: they were recomputed by hand at
each release, and `v0.5.1` shipped a CITATION.cff saying 5,098 rows when the
catalogue held 5,108.

`--check` runs on every push and pull request, so a change that adds rows has
to update the README in the same change. CITATION.cff describes a *release*,
so between releases it is allowed to lag; `--release` checks it too and is
what to run before tagging.

Standard library only — no dependencies to install.
"""

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OSINT_CSV = REPO / "Fonti_OSINT.csv"
DISINFO_CSV = REPO / "disinfo_sources_master.csv"
README = REPO / "README.md"
CITATION = REPO / "CITATION.cff"

COVERAGE_FIELDS = ["Note", "Paese / Area", "Lingua", "RSS Feed", "Accesso"]


def read(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def plain(category):
    """A category without its leading emoji: the form the README table uses."""
    return re.sub(r"^[^\w]+", "", category).strip()


def compute(osint, disinfo):
    total = len(osint)
    categories = Counter(plain(row["Macro-categoria"]) for row in osint)
    coverage = {
        field: round(100 * sum(1 for row in osint if row[field].strip()) / total)
        for field in COVERAGE_FIELDS
    } if total else {}
    batches = Counter(row["Provenienza"].strip() for row in osint)
    unstamped = batches.pop("", 0)
    return {
        "total": total,
        "categories": dict(categories),
        "coverage": coverage,
        "batches": dict(batches),
        "unstamped": unstamped,
        "watchlist": len(disinfo),
        "campaigns": dict(Counter(row["campaign"].strip() for row in disinfo)),
    }


def render(stats):
    lines = [f"Fonti_OSINT.csv — {stats['total']:,} rows", ""]
    for name, count in sorted(stats["categories"].items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"  {count:>6,}  {name}")
    lines += ["", "Filled:"]
    for field, share in stats["coverage"].items():
        lines.append(f"  {share:>5}%  {field}")
    lines += ["", f"Batches ({stats['unstamped']:,} rows unstamped):"]
    for name, count in sorted(stats["batches"].items()):
        lines.append(f"  {count:>6,}  {name}")
    lines += ["", f"disinfo_sources_master.csv — {stats['watchlist']:,} rows"]
    for name, count in sorted(stats["campaigns"].items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"  {count:>6,}  {name}")
    return "\n".join(lines)


def number(text):
    return int(text.replace(",", ""))


def check_readme(stats, readme):
    """Every way the README can disagree with the CSVs, as sentences."""
    problems = []

    match = re.search(r"^([\d,]+) sources across (\d+) macro-categories", readme, re.M)
    if not match:
        problems.append("README: no 'N sources across M macro-categories' line found")
    else:
        if number(match.group(1)) != stats["total"]:
            problems.append(f"README says {match.group(1)} sources; the catalogue holds "
                            f"{stats['total']:,}")
        if int(match.group(2)) != len(stats["categories"]):
            problems.append(f"README says {match.group(2)} macro-categories; the catalogue "
                            f"has {len(stats['categories'])}")

    listed = 0
    for name, count in stats["categories"].items():
        row = re.search(rf"^\| {re.escape(name)}(?: \([^|]*\))? \| ([\d,]+) \|$", readme, re.M)
        if not row:
            problems.append(f"README: category table has no row for {name!r}")
            continue
        listed += number(row.group(1))
        if number(row.group(1)) != count:
            problems.append(f"README says {row.group(1)} for {name!r}; the catalogue "
                            f"holds {count:,}")
    if not problems and listed != stats["total"]:
        problems.append(f"README: category rows sum to {listed:,}, not {stats['total']:,}")

    for field, share in stats["coverage"].items():
        row = re.search(rf"^\| `{re.escape(field)}` \| (\d+)% \|$", readme, re.M)
        if not row:
            problems.append(f"README: coverage table has no row for `{field}`")
        elif int(row.group(1)) != share:
            problems.append(f"README says `{field}` is {row.group(1)}% filled; it is {share}%")

    match = re.search(r"The ([\d,]+) unstamped rows", readme)
    if not match:
        problems.append("README: no 'The N unstamped rows' sentence found")
    elif number(match.group(1)) != stats["unstamped"]:
        problems.append(f"README says {match.group(1)} unstamped rows; there are "
                        f"{stats['unstamped']:,}")

    for batch in sorted(stats["batches"]):
        if f"`{batch}`" not in readme:
            problems.append(f"README never mentions the batch `{batch}`")

    match = re.search(r"^([\d,]+) documented disinformation domains", readme, re.M)
    if not match:
        problems.append("README: no 'N documented disinformation domains' line found")
    elif number(match.group(1)) != stats["watchlist"]:
        problems.append(f"README says {match.group(1)} watchlist entries; the file holds "
                        f"{stats['watchlist']:,}")
    return problems


def check_citation(stats, citation):
    problems = []
    flat = re.sub(r"\s+", " ", citation)
    match = re.search(r"catalogue of ([\d,]+) reliable", flat)
    if not match:
        problems.append("CITATION.cff: no 'catalogue of N reliable' in the abstract")
    elif number(match.group(1)) != stats["total"]:
        problems.append(f"CITATION.cff says {match.group(1)} sources; the catalogue holds "
                        f"{stats['total']:,}")
    match = re.search(r"watchlist of ([\d,]+) documented", flat)
    if not match:
        problems.append("CITATION.cff: no 'watchlist of N documented' in the abstract")
    elif number(match.group(1)) != stats["watchlist"]:
        problems.append(f"CITATION.cff says {match.group(1)} watchlist entries; the file "
                        f"holds {stats['watchlist']:,}")
    return problems


def main():
    parser = argparse.ArgumentParser(
        description="Count what the datasets hold, and check the README says the same.")
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero if README.md disagrees with the CSVs")
    parser.add_argument("--release", action="store_true",
                        help="with --check, also compare CITATION.cff")
    args = parser.parse_args()

    stats = compute(read(OSINT_CSV), read(DISINFO_CSV))
    if not args.check:
        print(render(stats))
        return 0

    problems = check_readme(stats, README.read_text(encoding="utf-8"))
    if args.release:
        problems += check_citation(stats, CITATION.read_text(encoding="utf-8"))
    if problems:
        for problem in problems:
            print(f"  {problem}")
        print(f"\nFAILED — {len(problems)} figure(s) out of date. "
              f"Run `python scripts/stats.py` for the current ones.")
        return 1
    print("OK — the README's figures match the CSVs."
          + (" CITATION.cff matches too." if args.release else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
