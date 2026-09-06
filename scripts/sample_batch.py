#!/usr/bin/env python3
"""
Draw the review sample for one batch of imported sources.

Run locally:

    python scripts/sample_batch.py --batch ifcn:2026-08
    python scripts/sample_batch.py --batch unsd:2026-10 --size 60

A batch is every row sharing a `Provenienza` value. Below a few hundred rows
you can read a batch end to end; past that you cannot, and the catalogue is
meant to roughly double. This script is the replacement for reading every row:
draw a sample, review it by hand, and accept or reject the batch as a whole.

Two properties make that honest rather than a formality.

**The sample is a function of the batch, not of when you ask for it.** The seed
comes from the batch id, so the same batch always yields the same rows. Nobody
can re-roll until the draw looks clean, and a reviewer can reproduce exactly
what another reviewer saw.

**A batch is rejected whole, not repaired row by row.** If the sample turns up
a bad row, the directory that produced it is the problem, and the rows you did
not look at came from the same place. Fixing the ones you happened to see would
leave the rest and give false confidence — the same mistake as `v0.5.0`, where
a check was believed because its output looked plausible.

What "bad" means here is deliberately narrow, and matches the rules already in
CONTRIBUTING.md: the URL does not identify the source it claims to be, the row
is a duplicate of one already present, or a field carries a value nobody
verified. A source you would not have chosen is not a defect.

Standard library only — no dependencies to install.
"""

import argparse
import csv
import hashlib
import random
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OSINT_CSV = REPO / "Fonti_OSINT.csv"

DEFAULT_SIZE = 60

# Accept only on a clean sample. By the rule of three, zero defects in 60 rows
# puts the true defect rate under about 5% with 95% confidence; a single defect
# already weakens that to roughly 8%, and — more to the point — every defect
# found so far in this catalogue was one a reviewer would refuse outright: a
# wedding planner under a news outlet's name, a corporate site under the name
# of its fact-checking arm. There is no sensible number of those to tolerate.
MAX_DEFECTS = 0


def batch_seed(batch):
    """A stable seed for a batch id, so the draw cannot be re-rolled."""
    return int(hashlib.sha256(batch.encode("utf-8")).hexdigest()[:16], 16)


def load_batch(batch, path=None):
    # An empty id is not a batch. Without this guard it would match every
    # unstamped row — the thousands that predate the column, whose origin is
    # unknown — and present them as one import to sign off on.
    if not batch or not batch.strip():
        return []
    batch = batch.strip()
    path = path or OSINT_CSV
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if rows and "Provenienza" not in rows[0]:
        raise SystemExit(
            f"{path.name} has no `Provenienza` column — nothing to sample by."
        )
    return [(i + 2, r) for i, r in enumerate(rows) if r["Provenienza"].strip() == batch]


def draw(rows, size, batch):
    """`size` rows from `rows`, chosen reproducibly, in file order."""
    if len(rows) <= size:
        return list(rows)
    rng = random.Random(batch_seed(batch))
    return sorted(rng.sample(rows, size), key=lambda pair: pair[0])


def known_batches(path=None):
    path = path or OSINT_CSV
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return Counter(r["Provenienza"].strip() for r in rows if r.get("Provenienza", "").strip())


def render(batch, total, sample):
    lines = [
        f"Batch {batch} — {total} rows, reviewing {len(sample)}",
        "",
    ]
    if len(sample) == total:
        lines.append("The batch is smaller than the sample size, so this is all of it.")
    else:
        covered = 100 * len(sample) / total
        lines.append(
            f"A reproducible draw of {covered:.0f}% of the batch. The same batch id "
            f"always yields these same rows."
        )
    lines += [
        "",
        f"Accept the batch only if every row below is sound "
        f"(threshold: {MAX_DEFECTS} defect{'s' if MAX_DEFECTS != 1 else ''}).",
        "A defect is: the URL does not identify the source it claims to be, the row",
        "duplicates one already in the catalogue, or a field carries an unverified",
        "value. A source you would not have picked is not a defect.",
        "",
        "If you find one, reject the whole batch — the rows you did not read came",
        "from the same directory.",
        "",
        "-" * 78,
    ]
    for line, row in sample:
        lines.append(f"line {line}  {row['Fonte']}")
        lines.append(f"  {row['URL']}")
        meta = " · ".join(filter(None, [
            row["Macro-categoria"], row["Sottosezione"],
            f"lingua {row['Lingua']}" if row["Lingua"] else "",
            f"paese {row['Paese / Area']}" if row["Paese / Area"] else "",
        ]))
        lines.append(f"  {meta}")
        if row["Note"]:
            lines.append(f"  {row['Note']}")
        lines.append("")
    lines.append("-" * 78)
    lines.append(
        f"Reviewed {len(sample)} of {total}. Any defect rejects "
        f"{batch} in full; record the outcome in the pull request."
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Draw the review sample for one batch of imported sources.")
    parser.add_argument("--batch", help="Provenienza value, e.g. ifcn:2026-08")
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE,
                        help=f"rows to review (default {DEFAULT_SIZE})")
    parser.add_argument("--list", action="store_true",
                        help="list the batches present in the catalogue and exit")
    args = parser.parse_args()

    if args.list or not args.batch:
        batches = known_batches()
        if not batches:
            print("No batch is stamped in Fonti_OSINT.csv yet.")
            return 0
        print("Batches in the catalogue:\n")
        for name, count in sorted(batches.items()):
            print(f"  {name:<28} {count:>5} rows")
        if not args.batch:
            print("\nPass --batch <id> to draw its review sample.")
        return 0

    rows = load_batch(args.batch)
    if not rows:
        print(f"No rows carry Provenienza {args.batch!r}.", file=sys.stderr)
        print("Run with --list to see the batches present.", file=sys.stderr)
        return 1

    print(render(args.batch, len(rows), draw(rows, args.size, args.batch)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
