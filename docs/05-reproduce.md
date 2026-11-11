# 05 — Reproduce

> **中文摘要**
> 从零到 264/264 的全部命令，每步给出「必须出现的数字」作为校验点；`$ETP_HOME`、`$WORKSPACE`、`$LEAN_HOME` 三个占位符的含义见下表。
> 主路径只需 Python 3 标准库，最快一条命令 2.3 秒出 264/264；Lean 编译是可选的独立证据，约 7 分钟。
> 任何一步的数字对不上，就说明上游那步错了——按顺序往回查，不要跳步。

---

## 0. Placeholders used in this repository

Every absolute path in this repository is written with a placeholder. Set them once
per shell.

| Placeholder | Meaning | Typical value |
|---|---|---|
| `$ETP_HOME` | the directory that holds the cloned upstream checkouts | `~/etp` |
| `$ETP_HOME/equational_theories` | clone of `teorth/equational_theories` (tables, equations, graph scripts) | `~/etp/equational_theories` |
| `$ETP_HOME/parsimagma` | clone of `carlok/parsimagma` (residual list, duals, equations.txt) | `~/etp/parsimagma` |
| `$ETP_HOME/graphs` | where `fetch_etp_data.py` puts `graph.json` and `finite_graph.json` | `~/etp/graphs` |
| `$ETP_HOME/etp-refutations-all` | a flat directory holding the 1171 generated `.lean` files | `~/etp/etp-refutations-all` |
| `$WORKSPACE` | a scratch directory for outputs of these scripts; nothing here is committed | `~/work` |
| `$LEAN_HOME` | a Lean 4.29.1 toolchain root (only needed for the Lean stage) | `~/lean` |

Set them:

```bash
export ETP_HOME="$HOME/etp"
export WORKSPACE="$HOME/work"
export LEAN_HOME="$HOME/lean"
export PYTHONUTF8=1          # Windows only, and it matters: see docs/03-pitfalls.md §10
```

## 1. Sources

```bash
git clone --depth 1 https://github.com/teorth/equational_theories "$ETP_HOME/equational_theories"
git clone --depth 1 https://github.com/carlok/parsimagma        "$ETP_HOME/parsimagma"
mkdir -p "$ETP_HOME/etp-refutations-all"
cp "$ETP_HOME"/equational_theories/equational_theories/Generated/All4x4Tables/*.lean \
   "$ETP_HOME/etp-refutations-all/"
```

**Checkpoint.** `ls "$ETP_HOME/etp-refutations-all" | wc -l` → **1171**.

`parsimagma`'s `finite_uncovered.txt` has since been regenerated. The 264-pair
version used here is preserved as [`updated_finite_uncovered.txt`](../submission/updated_finite_uncovered.txt)
and described in [`funnel-classification.json`](../reports/funnel-classification.json);
to reproduce the exact numbers you need that revision. Everything downstream reports
how many pairs it found, so a different revision shows up immediately as a different
count rather than a silent wrong answer.

## 2. The headline result: 264 of 264

```bash
python3 scripts/reverse_index.py \
  --base      "$ETP_HOME/etp-refutations-all" \
  --targets   "$ETP_HOME/parsimagma/data/etp/finite_uncovered.txt" \
  --equations "$ETP_HOME/parsimagma/data/etp/equations.txt" \
  --out "$WORKSPACE/out" --selfcheck
```

**Expected, line for line:**

```
laws: 4694
targets: 264 pairs
law universe: 131 laws (arity [1, 2, 3, 4])
corpus: 946 tables loaded, 225 files skipped
corpus with transposes: 1892 tables
selfcheck: 200 (table, law) samples, 0 disagreements
covered: 264/264 target pairs (100.0%)
  of which 240 have a non-transposed witness and 24 need a transpose
```

**Checkpoints.** 946 (not 1171 — the other 225 have no table literal); 131 laws;
1892 = 946 × 2; selfcheck 0 disagreements; 240 + 24 = 264.

Variants and what each proves:

| Flag | Expected | What it demonstrates |
|---|---|---|
| `--no-transpose` | `covered: 240/264` | the transpose recovers exactly the 24 transpose-only pairs |
| `--laws all` | 63 s, same 264/264 | the result does not depend on using only the target laws |
| `--strict` | exit 0 | suitable as a CI gate: exit 1 the moment any pair loses its witness |
| `--max-tables 100` | fewer covered | sanity check that the loader really caps, not a silent full run |

## 3. Coverage arithmetic: 916 / 940 / 790 / 676 / 114

The 940, 676 and 114 are recomputed from the corpus and the graph:

```bash
python3 scripts/fetch_etp_data.py --out "$ETP_HOME/graphs"          # downloads both graphs
python3 scripts/fetch_etp_data.py --out "$ETP_HOME/graphs" --decode # writes the split
```

**Expected decode output:**

```
1062 side: 610 infinite-only + 450 finitely refutable + 2 open
814 side:  604 finitely refutable + 210 no finite countermodel
finitely refutable total: 1054
open cells: (677,255) (2910,47)
```

**Checkpoints.** `610 + 450 + 2 = 1062`; `604 + 210 = 814`; `450 + 604 = 1054`.
If your 1062-side finitely-refutable count is 452 instead of 450, you counted the two
`unknown` cells — see [`03-pitfalls.md`](03-pitfalls.md) §1.

The 790 figure is **not** reproduced by anything here: it is `parsimagma`'s own
reported number (411 + 379). What this repository checks is the arithmetic around it:
`940 − 264 = 676`, `790 − 676 = 114`, `940 + 790 − 676 = 1054`. Those three must hold
against the pair lists in [`coverage_arithmetic.json`](../data/coverage_arithmetic.json).

## 4. Witness records

```bash
python3 scripts/build_witnesses.py
```

This reads the reverse-index output, re-verifies every pair with three evaluators,
and writes `data/witnesses_264.json` plus `data/verification_264.json`.

**Expected** (`data/verification_264.json`):

```
pairs 264 | agreement_true 264 | transpose_witnesses 24
distinct_tables 31 | conflicts 0
leads_histogram: substitution_bridge 104, published_facts_index 83,
                 published_table_sweep 65, corpus_full_sweep 7,
                 ext_parameters 4, dual_transpose 1
```

**Checkpoints.** `104 + 83 + 65 + 7 + 4 + 1 = 264`; `conflicts` is an empty list, not a
zero count with entries suppressed; `distinct_tables 31`.

## 5. Lean files and their compile record

```bash
python3 scripts/gen_lean.py                      # writes lean/*.lean from data/
python3 scripts/check_lean_structure.py          # text-level check, 31 files
```

**Expected structure check:** `files 31, passed 31, failed 0`.

Compiling requires the ETP project's own modules built once:

```bash
cd "$ETP_HOME/equational_theories"
lake build equational_theories.Equations.All
lake build equational_theories.FactsSyntax equational_theories.MemoFinOp \
           equational_theories.DecideBang
python3 "$OLDPWD/scripts/check_lean_compile.py" \
  --project "$ETP_HOME/equational_theories" \
  --lean-dir "$OLDPWD/lean" \
  --out "$OLDPWD/data/lean_compile_check.json" \
  --lake "$LEAN_HOME/bin/lake"
```

**Expected** (`data/lean_compile_check.json`):

```
toolchain leanprover/lean4:v4.29.1
total 31 | passed 31 | failed 0 | total_seconds 423.4   (an earlier run of the same set: 383.9)
per file: exit 0, 10 to 22 s across the two runs, dominated by decideFin!
```

**Checkpoints.** 31 files; every `exit` is 0; every `first_error` is `null`; total time
between 300 s and 500 s on a laptop-class machine.

**What this does not show:** this is not `lake build`, not CI, not review. See
[`06-boundaries.md`](06-boundaries.md).

## 6. Self-checks on the repository itself

```bash
python3 scripts/scan_sensitive.py --root . --selftest   # patterns fire on synthetic probes
python3 scripts/scan_sensitive.py --root .              # no local paths, names, institutions
python3 scripts/selfcheck.py --root .                   # BOM, links, checksums
```

**Expected:** `SELFTEST: PASS`, `HITS: 0 (clean)`, `SELFCHECK: PASS`.

The scanner reads no deny file: identifiers are passed as `--deny "a,b"` on the
command line, so nothing sensitive is ever written to disk. If you fork this and add
your own checks, keep that property.

## 7. Rebuilding the Lean files must not change them

A useful invariant when you touch the generator: regenerating from the same
`data/witnesses_264.json` must reproduce the committed `lean/*.lean` byte for byte
apart from the timestamp-free header. In this repository that was verified by hashing
the bodies (everything from the `/-! The magma definition -/` marker onward) before and
after a regeneration: 31 files, 0 differences.

## 8. If a number disagrees

Work backwards; do not adjust the expected number.

| Symptom | Look at |
|---|---|
| 946 becomes a different count | the table regex; a changed upstream file layout |
| 264 becomes 240 | transposes not added (`--no-transpose` accidentally on) |
| 264 becomes fewer, `--strict` fails | the residual revision changed after `parsimagma` regenerated it |
| 1054 becomes 1052 or 1056 | the RLE decode (`unknown` handling) |
| coverage sums do not reconcile | double-counted pairs; check 676 and 114 are disjoint |
| Lean: `unknown module prefix` | the targeted `lake build` did not run (pitfall §11) |
| Lean: `expected token` at `1:0` | a BOM in the file (pitfall §9) |
