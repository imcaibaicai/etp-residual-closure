#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-index a corpus of finite magmas by what each table *satisfies*, not by
which pair it was generated for.

Motivation
----------
ETP's generated refutation files annotate each table with the facts that were
recorded for it (``Facts G [satisfied] [refuted]``). That annotation names the
pair(s) the table was built to separate. It does not name most of the pairs the
table also separates: one table routinely satisfies a hypothesis law and refutes
dozens of targets that were never listed.

Two further pieces of information are discarded on the same path:

* **transposes.** ``T^T`` is a different magma on the same carrier whose product
  swaps left and right. A table indexed only as printed loses every pair that
  only its transpose separates.
* **the full satisfied set.** The annotation is a record of emitted facts, not
  the set of laws the table satisfies. Computing the set directly changes which
  pairs a corpus is seen to cover.

This script computes, for every table in a corpus, the laws it satisfies and the
laws it refutes; adds each table's transpose to the corpus; and answers
separation queries from that index.

It is standard library only. Two independent evaluators are included and are
cross-checked against each other: a deliberately naive recursive one (the
reference) and a stack-machine one (the fast path). ``--selfcheck`` runs both.

Usage
-----
    python3 reverse_index.py --base </path/to/etp-refutations-all> \\
                             --targets </path/to/finite_uncovered.txt> \\
                             --out ./out

    python3 reverse_index.py --base ... --targets ... --selfcheck
    python3 reverse_index.py --base ... --targets ... --laws all --out ./out
    python3 reverse_index.py --base ... --targets ... --no-transpose

Inputs
------
--base
    A directory of ``.lean`` files containing ``finOpTable "[[...]]"`` literals,
    such as ``equational_theories/Generated/All4x4Tables``. Nested directories
    are scanned. Alternatively a directory (or file) holding ``Table [[...]]``
    lines in the ``data/etp/refutations*.txt`` format.
--targets
    A pair list: either ``set<TAB>from<TAB>to`` with ``#`` comments (the format
    of ``data/etp/finite_uncovered.txt``) or plain ``from<TAB>to``.
--equations
    ``equations.txt``, one law per line, line number = law number (1-based).
    Defaults to ``--base``/../data/etp/equations.txt when it exists.

Outputs
-------
``reverse_index.json``
    Per table: name, carrier, sha256 of the table, whether it is a transpose,
    the laws it satisfies, the laws it refutes. Plus the per-target-pair witness
    list and the corpus summary.
``witnesses.tsv``
    One record per table that serves as a witness, in the same format as
    ``data/etp/refutations*.txt``: ``Table [[...]]`` then ``Proves [...]``,
    blank line between records. ``Proves`` is the set of laws the table
    satisfies, complete over all 4694 laws when ``--laws all`` is used and
    declared incomplete in a header comment otherwise.
``summary.json``
    Aggregate counts only, small enough to diff.

Exit status is 0 on success. ``--strict`` makes it 1 if any target pair has no
witness.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import random
import re
import sys

OP = "\u25c7"  # the ETP binary operation symbol

# ---------------------------------------------------------------------------
# Laws: parsing
# ---------------------------------------------------------------------------


class Law:
    """One equation, parsed into two term trees.

    A term is ``("v", name)`` for a variable or ``("o", left, right)``.
    ``variables`` is the sorted tuple of variable names appearing anywhere,
    which is exactly the set the quantifier ranges over: a law mentioning only
    ``x`` and ``z`` is checked over ``carrier^2`` assignments, not
    ``carrier^4``.
    """

    __slots__ = ("text", "lhs", "rhs", "variables")

    def __init__(self, text: str):
        self.text = text.strip()
        lhs_text, rhs_text = self.text.split("=")
        self.lhs = _parse(lhs_text)
        self.rhs = _parse(rhs_text)
        names = set()
        _collect(self.lhs, names)
        _collect(self.rhs, names)
        self.variables = tuple(sorted(names))

    @property
    def arity(self) -> int:
        return len(self.variables)

    def __repr__(self) -> str:
        return f"Law({self.text!r})"


def _tokens(text: str):
    out = []
    for ch in text:
        if ch.isspace():
            continue
        if ch in "()=" or ch == OP or ch.isalpha():
            out.append(ch)
        else:
            raise ValueError(f"unexpected character {ch!r} in law {text!r}")
    return out


def _parse(text: str):
    """Parse one side of a law.

    ``equations.txt`` prints parentheses only around composite subterms, so a
    bare ``x ◇ y ◇ z`` means ``x ◇ (y ◇ z)``: the operation is taken as
    right-associative here for exactly that reason.
    """
    toks = [c for c in text if not c.isspace()]
    pos = [0]

    def atom():
        if pos[0] >= len(toks):
            raise ValueError(f"unexpected end of law {text!r}")
        ch = toks[pos[0]]
        if ch == "(":
            pos[0] += 1
            inner = chain()
            if pos[0] >= len(toks) or toks[pos[0]] != ")":
                raise ValueError(f"unbalanced parentheses in {text!r}")
            pos[0] += 1
            return inner
        if ch.isalpha():
            pos[0] += 1
            return ("v", ch)
        raise ValueError(f"expected variable or '(' in {text!r}, got {ch!r}")

    def chain():
        left = atom()
        if pos[0] < len(toks) and toks[pos[0]] == OP:
            pos[0] += 1
            return ("o", left, chain())
        return left

    term = chain()
    if pos[0] != len(toks):
        raise ValueError(f"trailing tokens in {text!r}: {toks[pos[0]:]!r}")
    return term


def _collect(term, acc: set) -> None:
    stack = [term]
    while stack:
        t = stack.pop()
        if t[0] == "v":
            acc.add(t[1])
        else:
            stack.append(t[1])
            stack.append(t[2])


def load_equations(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return [line.rstrip("\n") for line in fh]


# ---------------------------------------------------------------------------
# Evaluator A: naive recursion (the reference implementation)
# ---------------------------------------------------------------------------


def eval_naive(term, table, assignment):
    """Evaluate ``term`` by direct recursion on the term tree."""
    if term[0] == "v":
        return assignment[term[1]]
    left = eval_naive(term[1], table, assignment)
    right = eval_naive(term[2], table, assignment)
    return table[left][right]


def refutes_naive(table, law):
    """Return a counterexample assignment, or None if the law holds."""
    names = law.variables
    n = len(table)
    for values in itertools.product(range(n), repeat=len(names)):
        assignment = dict(zip(names, values))
        if eval_naive(law.lhs, table, assignment) != eval_naive(law.rhs, table, assignment):
            return assignment
    return None


# ---------------------------------------------------------------------------
# Evaluator B: stack machine (the fast path)
# ---------------------------------------------------------------------------


def compile_term(term, index):
    """Compile a term to stack instructions.

    ``(0, k)`` pushes the value of the k-th variable; ``(1, 0)`` pops ``b`` then
    ``a`` and pushes ``a ◇ b``. Post-order emission keeps the operand order.
    """
    prog = []
    stack = [term]
    while stack:
        node = stack.pop()
        if node == "op":
            prog.append((1, 0))
        elif node[0] == "v":
            prog.append((0, index[node[1]]))
        else:
            stack.append("op")
            stack.append(node[2])
            stack.append(node[1])
    return prog


def run_program(prog, flat, n, values):
    stack = []
    for kind, arg in prog:
        if kind == 0:
            stack.append(values[arg])
        else:
            b = stack.pop()
            a = stack.pop()
            stack.append(flat[a * n + b])
    return stack[0]


class FastLaw:
    """A law with both sides compiled to stack programs, ready to sweep."""

    __slots__ = ("law", "pl", "pr", "names", "arity")

    def __init__(self, law: Law):
        index = {name: k for k, name in enumerate(law.variables)}
        self.law = law
        self.pl = compile_term(law.lhs, index)
        self.pr = compile_term(law.rhs, index)
        self.names = law.variables
        self.arity = len(self.names)

    def counterexample(self, flat, n):
        """Return a counterexample assignment as a dict, or None."""
        pl, pr = self.pl, self.pr
        for values in itertools.product(range(n), repeat=self.arity):
            if run_program(pl, flat, n, values) != run_program(pr, flat, n, values):
                return dict(zip(self.names, values))
        return None


# ---------------------------------------------------------------------------
# Magmas
# ---------------------------------------------------------------------------


class Magma:
    """An n x n multiplication table, ``table[x][y] == x ◇ y``, values 0..n-1."""

    __slots__ = ("name", "table", "flat", "n", "is_transpose")

    def __init__(self, name, table, is_transpose=False):
        n = len(table)
        if n == 0 or any(len(row) != n for row in table):
            raise ValueError(f"{name}: table is not square")
        flat = []
        for row in table:
            for v in row:
                v = int(v)
                if not 0 <= v < n:
                    raise ValueError(f"{name}: entry {v} outside 0..{n - 1}")
                flat.append(v)
        self.name = name
        self.table = [[int(v) for v in row] for row in table]
        self.flat = tuple(flat)
        self.n = n
        self.is_transpose = is_transpose

    def transposed(self):
        return Magma(self.name + "#T", [list(row) for row in zip(*self.table)], True)

    def sha256(self) -> str:
        payload = json.dumps(self.table, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    def satisfies(self, law: FastLaw):
        return law.counterexample(self.flat, self.n) is None

    def counterexample(self, law: FastLaw):
        return law.counterexample(self.flat, self.n)


# ---------------------------------------------------------------------------
# Corpus loading
# ---------------------------------------------------------------------------

_LEAN_LITERAL = re.compile(r'finOpTable\s+"(\[\[.*?\]\])"', re.S)
_TABLE_LINE = re.compile(r"^\s*Table\s+(\[\[.*\]\])\s*$")


def load_corpus(base: str):
    """Load every table under ``base``.

    ``.lean`` files are read with the ``finOpTable "..."`` literal that
    ``Generated/All4x4Tables`` uses; ``.txt`` files are read in the
    ``Table [[...]]`` line format of ``data/etp/refutations*.txt``. Files that
    parse to neither are counted, not silently dropped.
    """
    magmas = []
    skipped = []
    for root, _dirs, files in os.walk(base):
        for name in sorted(files):
            path = os.path.join(root, name)
            rel = os.path.relpath(path, base).replace("\\", "/")
            if name.endswith(".lean"):
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                match = _LEAN_LITERAL.search(text)
                if not match:
                    skipped.append(rel)
                    continue
                tables = [json.loads(match.group(1))]
            elif name.endswith(".txt"):
                tables = []
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        m = _TABLE_LINE.match(line)
                        if m:
                            tables.append(json.loads(m.group(1)))
                if not tables:
                    skipped.append(rel)
                    continue
            else:
                continue
            for k, table in enumerate(tables):
                tag = rel if len(tables) == 1 else f"{rel}#{k + 1}"
                try:
                    magmas.append(Magma(tag, table))
                except ValueError as exc:
                    skipped.append(f"{tag}: {exc}")
    return magmas, skipped


def load_targets(path: str):
    """Read a pair list. Returns [(set_label, from, to)].

    Accepts the header line ``# set<TAB>from<TAB>to`` used by
    ``finite_uncovered.txt`` and plain ``from<TAB>to`` lines. Comment lines
    starting with ``#`` are dropped.
    """
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            parts = re.split(r"\t+", text)
            if len(parts) >= 3 and not parts[0].strip().isdigit():
                label, a, b = parts[0], int(parts[1]), int(parts[2])
            elif len(parts) >= 2:
                label, a, b = "", int(parts[0]), int(parts[1])
            else:
                continue
            out.append((label, a, b))
    return out


# ---------------------------------------------------------------------------
# The index
# ---------------------------------------------------------------------------


def build_index(magmas, fast_laws, law_filter=None):
    """Compute the satisfied set of every magma over the given laws.

    Returns ``{law_id: [magma, ...]}`` for satisfied laws only. Laws that a
    magma refutes are its complement within ``law_filter``; storing the
    satisfied side keeps the structure small (a table satisfies far fewer laws
    than it refutes) and the separation query is a set test on the satisfied
    side.
    """
    satisfied = {}
    for magma in magmas:
        acq = set()
        for law_id in law_filter:
            if magma.satisfies(fast_laws[law_id]):
                acq.add(law_id)
        satisfied[magma.name] = acq
    return satisfied


def find_witnesses(satisfied, magmas, pairs):
    """For each target pair, every magma that satisfies ``from`` and refutes ``to``."""
    by_name = {m.name: m for m in magmas}
    hits = {}
    for label, a, b in pairs:
        found = []
        for name, acq in satisfied.items():
            if a in acq and b not in acq:
                found.append(name)
        if found:
            hits[(a, b)] = sorted(found, key=lambda nm: (by_name[nm].n, nm))
    return hits


# ---------------------------------------------------------------------------
# Self check
# ---------------------------------------------------------------------------


def selfcheck(magmas, fast_laws, law_ids, samples=200, seed=20261110):
    """Cross-check the fast evaluator against the naive one.

    Every law in ``law_ids`` is checked on a deterministic pseudo-random sample
    of magmas; a disagreement on satisfaction *or* on the first counterexample
    assignment is fatal, because either one means one of the two evaluators is
    wrong and every witness produced by it is suspect.
    """
    rng = random.Random(seed)
    checked = 0
    disagreements = []
    law_list = sorted(law_ids)
    for _ in range(samples):
        magma = magmas[rng.randrange(len(magmas))]
        law_id = law_list[rng.randrange(len(law_list))]
        fast = fast_laws[law_id]
        fast_cex = fast.counterexample(magma.flat, magma.n)
        naive_cex = refutes_naive(magma.table, fast.law)
        if (fast_cex is None) != (naive_cex is None):
            disagreements.append((magma.name, law_id, "satisfaction", fast_cex, naive_cex))
        checked += 1
    return checked, disagreements


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_tsv(path, pairs, hits, by_name, satisfied, complete_proves):
    """Write witnesses in the ``data/etp/refutations*.txt`` format.

    The format is one record per table, ``Table [[...]]`` then
    ``Proves [...]``, separated by a blank line, exactly as
    ``data/etp/refutations2x2.txt`` is written. ``Proves`` is the set of laws
    the table satisfies; a table's refuted set is its complement in the law
    universe, which is why an incomplete universe must be declared in the
    header rather than left implicit.
    """
    written = set()
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        if not complete_proves:
            fh.write("# Proves lists below are complete only within the law universe "
                     "used for indexing,\n# not with respect to all 4694 laws. "
                     "Re-run with --laws all for complete lists.\n\n")
        for label, a, b in pairs:
            for name in hits.get((a, b), []):
                if name in written:
                    continue
                written.add(name)
                m = by_name[name]
                fh.write(f"Table {json.dumps(m.table)}\n")
                fh.write(f"Proves {json.dumps(sorted(satisfied[name]))}\n\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--base", required=True, help="corpus directory (lean or table txt)")
    parser.add_argument("--targets", required=True, help="pair list file")
    parser.add_argument("--equations", default=None, help="equations.txt (line = law number)")
    parser.add_argument("--out", default=None, help="output directory (default: ./reverse_index_out)")
    parser.add_argument("--laws", choices=["targets", "all"], default="targets",
                        help="law universe: only the laws named by --targets (default), or all 4694")
    parser.add_argument("--no-transpose", action="store_true", help="do not add transposes")
    parser.add_argument("--selfcheck", action="store_true", help="cross-check the two evaluators")
    parser.add_argument("--strict", action="store_true", help="exit 1 if a target pair has no witness")
    parser.add_argument("--max-tables", type=int, default=0, help="cap tables loaded (0 = all)")
    args = parser.parse_args(argv)

    equations = args.equations
    if equations is None:
        base_abs = os.path.abspath(args.base)
        for candidate in (
            os.path.join(base_abs, "data", "etp", "equations.txt"),
            os.path.join(base_abs, "..", "data", "etp", "equations.txt"),
            os.path.join(base_abs, "..", "parsimagma", "data", "etp", "equations.txt"),
            os.path.join(base_abs, "..", "..", "data", "etp", "equations.txt"),
        ):
            if os.path.exists(candidate):
                equations = candidate
                break
        if equations is None:
            sys.exit("--equations is required: equations.txt was not found near --base")
    law_texts = load_equations(equations)
    print(f"laws: {len(law_texts)} from {equations}")

    pairs = load_targets(args.targets)
    print(f"targets: {len(pairs)} pairs from {args.targets}")

    if args.laws == "all":
        law_ids = set(range(1, len(law_texts) + 1))
    else:
        law_ids = {a for _l, a, _b in pairs} | {b for _l, _a, b in pairs}
    fast_laws = {i: FastLaw(Law(law_texts[i - 1])) for i in law_ids}
    print(f"law universe: {len(law_ids)} laws "
          f"(arity {sorted({fl.arity for fl in fast_laws.values()})})")

    magmas, skipped = load_corpus(args.base)
    if args.max_tables:
        magmas = magmas[: args.max_tables]
    print(f"corpus: {len(magmas)} tables loaded, {len(skipped)} files skipped")

    corpus = list(magmas)
    if not args.no_transpose:
        corpus += [m.transposed() for m in magmas]
        print(f"corpus with transposes: {len(corpus)} tables")

    if args.selfcheck:
        checked, bad = selfcheck(corpus, fast_laws, law_ids)
        print(f"selfcheck: {checked} (table, law) samples, {len(bad)} disagreements")
        for row in bad[:5]:
            print("  disagreement:", row)
        if bad:
            sys.exit(2)

    satisfied = build_index(corpus, fast_laws, sorted(law_ids))
    hits = find_witnesses(satisfied, corpus, pairs)
    by_name = {m.name: m for m in corpus}

    covered = len(hits)
    target_pairs = {(a, b) for _l, a, b in pairs}
    print(f"covered: {covered}/{len(target_pairs)} target pairs "
          f"({100.0 * covered / max(1, len(target_pairs)):.1f}%)")

    direct_only = sum(1 for p, names in hits.items()
                      if any(not by_name[n].is_transpose for n in names))
    transpose_needed = covered - direct_only
    print(f"  of which {direct_only} have a non-transposed witness "
          f"and {transpose_needed} need a transpose")

    out = args.out or os.path.join(os.getcwd(), "reverse_index_out")
    os.makedirs(out, exist_ok=True)

    payload = {
        "generator": "reverse_index.py",
        "base": os.path.abspath(args.base),
        "equations": os.path.abspath(equations),
        "targets_file": os.path.abspath(args.targets),
        "law_universe": args.laws,
        "laws_considered": sorted(law_ids),
        "tables_loaded": len(magmas),
        "tables_with_transposes": len(corpus),
        "files_skipped": skipped,
        "tables": [
            {
                "name": m.name,
                "carrier": m.n,
                "is_transpose": m.is_transpose,
                "sha256": m.sha256(),
                "satisfies": sorted(satisfied[m.name]),
            }
            for m in corpus
        ],
        "witnesses": {
            f"{a}_{b}": {
                "from": a,
                "to": b,
                "label": next((l for l, x, y in pairs if (x, y) == (a, b)), ""),
                "tables": [
                    {
                        "name": n,
                        "carrier": by_name[n].n,
                        "is_transpose": by_name[n].is_transpose,
                        "sha256": by_name[n].sha256(),
                        "refutation_assignment": by_name[n].counterexample(fast_laws[b]),
                    }
                    for n in hits[(a, b)]
                ],
            }
            for a, b in sorted(hits)
        },
        "summary": {
            "target_pairs": len(target_pairs),
            "covered": covered,
            "uncovered": sorted([list(p) for p in target_pairs - set(hits)]),
            "direct_witness": direct_only,
            "transpose_only": transpose_needed,
        },
    }
    index_path = os.path.join(out, "reverse_index.json")
    with open(index_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1, sort_keys=False)
    write_tsv(os.path.join(out, "witnesses.tsv"), pairs, hits, by_name, satisfied,
              complete_proves=(args.laws == "all"))
    with open(os.path.join(out, "summary.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload["summary"], fh, ensure_ascii=False, indent=1)
    print(f"wrote {index_path}")
    print(f"wrote {os.path.join(out, 'witnesses.tsv')}")
    print(f"wrote {os.path.join(out, 'summary.json')}")

    if args.strict and covered != len(target_pairs):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
