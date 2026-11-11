#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download the two ETP graph artifacts, and decode the finite implication graph.

Why this is a script and not a vendored file
--------------------------------------------
``graph.json`` and ``finite_graph.json`` are 9.0 MB each. Only the result of
decoding them is small enough to belong in a repository, and only the decode
result is what this project uses. Downloading them on demand keeps the repository
cloneable and keeps the provenance honest: you get whatever the project currently
publishes, not a snapshot of unknown age.

Usage
-----
    export ETP_HOME=/path/to/etp

    # download (default: $ETP_HOME/graphs)
    python3 scripts/fetch_etp_data.py --out "$ETP_HOME/graphs"

    # decode the 1054 finitely refutable pairs
    python3 scripts/fetch_etp_data.py --out "$ETP_HOME/graphs" \
        --pairs-dir "$ETP_HOME/parsimagma/data/etp" \
        --decode --facts-out data/graph_facts.json

Decode rules (get these wrong and the numbers are wrong, silently)
-----------------------------------------------------------------
``finite_graph.json`` holds ``rle_encoded_array`` as a **flat list alternating
value and run length**: ``[v0, n0, v1, n1, ...]``, row-major over the 4694 laws.
The nine values are indices into the ``ids`` array at
``scripts/generate_equation_explorer_graph.py`` lines 17-27 of the ETP checkout:

    0 explicit_conjecture_false   1 explicit_conjecture_true
    2 explicit_proof_false        3 explicit_proof_true
    4 implicit_conjecture_false   5 implicit_conjecture_true
    6 implicit_proof_false        7 implicit_proof_true
    8 unknown

Entry ``(i, j)`` describes "does ``E_i`` imply ``E_j`` over finite magmas".
An implication is **present iff the value is odd** (the project's own consumer
tests ``in {1,3,5,7}``, line 74 of that script). Value 8 is ``unknown`` and is
neither present nor absent — treating "nonzero" as "refuted" turns the 2 open
cells into refutations and gives 452 finitely refutable on the 1062 side instead
of 450.

Verification built in
---------------------
After decoding, the script asserts the sums that must hold:

    610 + 450 + 2 = 1062        (the 1062-side list has 1062 rows)
    604 + 210 = 814             (the 814-side list has 814 rows)
    450 + 604 = 1054            (finitely refutable total)

If any of those fails, it exits non-zero instead of writing a plausible file.
"""

from __future__ import annotations

import argparse
import bisect
import json
import os
import sys
import urllib.request

N_LAWS = 4694

BASE_URL = "https://teorth.github.io/equational_theories/implications"
ARTIFACTS = {
    "graph.json": BASE_URL + "/graph.json",
    "finite_graph.json": BASE_URL + "/finite_graph.json",
}

# the two pair lists that partition the sites
SITE_LISTS = {
    "hard": "hard_core.txt",          # 1062 side: Vampire left these undecided
    "sat": "saturation_refuted.txt",  # 814 side
}


def download(url: str, dest: str, force: bool) -> str:
    if os.path.exists(dest) and not force:
        print(f"exists  {dest} ({os.path.getsize(dest)} bytes) — use --force to re-download")
        return dest
    print(f"fetch   {url}")
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    tmp = dest + ".part"
    with urllib.request.urlopen(url, timeout=120) as resp, open(tmp, "wb") as fh:
        fh.write(resp.read())
    os.replace(tmp, dest)
    print(f"wrote   {dest} ({os.path.getsize(dest)} bytes)")
    return dest


def read_pairs(path: str) -> list[tuple[int, int]]:
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.replace(",", " ").split()
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                out.append((int(parts[0]), int(parts[1])))
    return out


class RleMatrix:
    """Row-major RLE over the laws, with an O(log runs) single-cell lookup."""

    def __init__(self, flat: list[int]):
        if len(flat) % 2:
            raise ValueError("rle_encoded_array must alternate value, run length")
        self.values = flat[0::2]
        self.starts = []
        pos = 0
        for run in flat[1::2]:
            self.starts.append(pos)
            pos += run
        self.total = pos
        if self.total != N_LAWS * N_LAWS:
            raise ValueError(
                f"rle expands to {self.total} cells, expected {N_LAWS ** 2}")

    def get(self, i: int, j: int) -> int:
        pos = (i - 1) * N_LAWS + (j - 1)
        return self.values[bisect.bisect_right(self.starts, pos) - 1]


def decode(graphs_dir: str, pairs_dir: str, facts_out: str) -> int:
    path = os.path.join(graphs_dir, "finite_graph.json")
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    mat = RleMatrix(doc["rle_encoded_array"])

    lists = {}
    for site, name in SITE_LISTS.items():
        p = os.path.join(pairs_dir, name)
        if not os.path.isfile(p):
            print(f"error: missing pair list {p}", file=sys.stderr)
            return 2
        lists[site] = read_pairs(p)

    buckets = {"hard_finite": [], "hard_infinite": [], "hard_open": [],
               "sat_finite": [], "sat_infinite": []}
    for site, pairs in lists.items():
        for a, b in pairs:
            v = mat.get(a, b)
            if v == 8:
                key = f"{site}_open"
                buckets.setdefault(key, []).append([a, b])
            elif v % 2:
                buckets[f"{site}_infinite"].append([a, b])
            else:
                buckets[f"{site}_finite"].append([a, b])

    result = {k: sorted(v) for k, v in buckets.items() if v}
    h, s = lists["hard"], lists["sat"]
    counts = {
        "hard_rows": len(h),
        "hard": f"{len(result.get('hard_infinite', []))} infinite-only + "
                f"{len(result.get('hard_finite', []))} finitely refutable + "
                f"{len(result.get('hard_open', []))} open",
        "sat_rows": len(s),
        "sat": f"{len(result.get('sat_finite', []))} finitely refutable + "
               f"{len(result.get('sat_infinite', []))} no finite countermodel",
        "finitely_refutable": len(result.get("hard_finite", []))
                              + len(result.get("sat_finite", [])),
        "open_cells": result.get("hard_open", []) + result.get("sat_open", []),
    }

    checks = [
        ("610 + 450 + 2 = 1062",
         len(result.get("hard_infinite", [])) == 610
         and len(result.get("hard_finite", [])) == 450
         and len(result.get("hard_open", [])) == 2),
        ("604 + 210 = 814",
         len(result.get("sat_finite", [])) == 604
         and len(result.get("sat_infinite", [])) == 210),
        ("450 + 604 = 1054", counts["finitely_refutable"] == 1054),
        ("open cells are (677,255) and (2910,47)",
         sorted(map(tuple, counts["open_cells"])) == [(677, 255), (2910, 47)]),
    ]

    print(f"1062 side: {counts['hard']}")
    print(f"814 side:  {counts['sat']}")
    print(f"finitely refutable total: {counts['finitely_refutable']}")
    print(f"open cells: {counts['open_cells']}")
    bad = 0
    for label, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {label}")
        bad += not ok
    if bad:
        print(f"decode FAILED {bad} check(s); nothing written", file=sys.stderr)
        return 1

    payload = {
        "source": {
            "graph": "finite_graph.json (ETP published artifact)",
            "decode": "rle_encoded_array is flat [value, runLen, ...]; entry (i,j) "
                      "is an implication iff the value is odd; value 8 = unknown",
            "sites": {k: v for k, v in SITE_LISTS.items()},
        },
        "counts": counts,
        **result,
    }
    with open(facts_out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    print(f"wrote {facts_out}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.environ.get("ETP_HOME", "."),
                    help="directory for graph.json / finite_graph.json")
    ap.add_argument("--url", action="append", default=[], metavar="NAME=URL",
                    help="override an artifact URL (repeatable)")
    ap.add_argument("--force", action="store_true", help="re-download even if present")
    ap.add_argument("--decode", action="store_true",
                    help="decode finite_graph.json into the 1054-pair split")
    ap.add_argument("--pairs-dir", default=None,
                    help="directory holding hard_core.txt and saturation_refuted.txt "
                         "(default: $ETP_HOME/parsimagma/data/etp)")
    ap.add_argument("--facts-out", default="data/graph_facts.json")
    args = ap.parse_args(argv)

    urls = dict(ARTIFACTS)
    for item in args.url:
        name, _, url = item.partition("=")
        if not url:
            print(f"error: --url wants NAME=URL, got {item!r}", file=sys.stderr)
            return 2
        urls[name] = url

    out = os.path.abspath(args.out)
    for name, url in urls.items():
        try:
            download(url, os.path.join(out, name), args.force)
        except Exception as exc:                      # noqa: BLE001 - report, do not raise
            print(f"error: could not fetch {url}: {exc}", file=sys.stderr)
            return 2

    if not args.decode:
        return 0

    pairs_dir = args.pairs_dir or os.path.join(
        os.environ.get("ETP_HOME", ""), "parsimagma", "data", "etp")
    return decode(out, pairs_dir, args.facts_out)


if __name__ == "__main__":
    sys.exit(main())
