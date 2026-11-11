# 02 — The pipeline, stage by stage

> **中文摘要**
> 一条可复现的流水线：取源（ETP 表 + carlok 清单 + 两份图产物）→ 解码 RLE 图（1054 = 450 + 604）→ 解析 946/1171 张表 → 算 4694 位签名并补转置 → 反向查询覆盖率（916 / 940 / 790 / 676 / 114）→ 三路求值器逐对验证 → 生成 Lean 并单独编译 → 打包与脱敏。
> 每阶段都写明「它产出什么数字」和「这个数字怎么被下一阶段用掉」，任何一步数不出来就说明上游错了。
> 全流程只用 Python 标准库；Lean 编译是可选的独立证据，不参与数学结论。

---

## Overview

```
sources ──► decode ──► corpus ──► signatures ──► coverage ──► witnesses ──► verify ──► package
   │           │         │            │             │            │           │          │
 1171 lean   1054 FR   946 tables   4694 bits    916/940/790   264 pairs    3 evals   CHECKSUMS
 2 graphs   610/450/2   + 1892 w/T     per table  676/114        31 tables   0 conflict 31 lean
```

Every stage states what number it produces and how the next stage consumes it. If
a stage cannot produce its number, an upstream stage is wrong — that is the
invariant to check when resuming after an interruption.

## Stage 1 — Sources

| Item | Where it comes from | Size |
|---|---|---|
| Generated refutation files | `equational_theories/Generated/All4x4Tables/*.lean` in `teorth/equational_theories` | 1171 files, 6.1 MB |
| Law texts | `equational_theories/Equations/equations.txt`, 4694 lines, line number = law number | small |
| The 264-pair residual | `carlok/parsimagma`, `data/etp/finite_uncovered.txt` (previous revision) | 39 + 225 rows |
| Dual map | `carlok/parsimagma`, `data/etp/duals.json` | 2305 explicit pairs |
| Finite implication graph | ETP's published `finite_graph.json` | 9.0 MB |
| Full graph | ETP's published `graph.json` | 9.0 MB |

[`../scripts/fetch_etp_data.py`](../scripts/fetch_etp_data.py) downloads both graph
artifacts and decodes them; what the decode produces is committed as
[`../data/graph_facts.json`](../data/graph_facts.json).

## Stage 2 — Decode the finite implication graph

`finite_graph.json` stores the matrix as `rle_encoded_array`: a flat list of
`(value, runLength)` pairs, row-major. The nine values are the indices of the `ids`
array at `scripts/generate_equation_explorer_graph.py` lines 17–27:

```
0 explicit_conjecture_false   1 explicit_conjecture_true
2 explicit_proof_false        3 explicit_proof_true
4 implicit_conjecture_false   5 implicit_conjecture_true
6 implicit_proof_false        7 implicit_proof_true
8 unknown
```

An implication is **present** iff the value is odd (line 74 of the same script,
`implications[i][j] in {1,3,5,7}`). Value 8 is `unknown` and must be excluded.

Output of this stage, on the 1062 side and the 814 side:

| Site | Pairs | Split |
|---|---|---|
| 1062 side (Vampire undecided) | 1062 | 610 infinite-only + 450 finitely refutable + 2 open |
| 814 side (saturation-refuted) | 814 | 604 finitely refutable + 210 with no finite countermodel |
| **finitely refutable total** | **1054** | 450 + 604 |

The 2 open cells are `(677, 255)` and `(2910, 47)`. Check:
`610 + 450 + 2 = 1062`.

Note the size of the whole matrix: 22,033,636 cells. The 2 open ones are the only
cells the project left undecided.

## Stage 3 — Build the corpus

Parse every generated file for a `finOpTable "[[...]]"` literal with a regular
expression; parse the JSON payload into a square integer matrix.

| Result | Count |
|---|---|
| `.lean` files under the generated directory | 1171 |
| files with a parseable table literal | **946** |
| files skipped | 225 |
| why skipped | they do not write a table literal: `ManuallyProved`, `FiniteImplicationSearch`, and other shapes |
| distinct carrier sizes | 2 … 65 |

The 225 skipped files are a known gap: they may hold further usable tables that the
regex does not see. Nobody has gone through them by hand.

Also load the target pairs and resolve each law number to its text from
`equations.txt`. The 264 pairs name **131 distinct laws**, of arity 1 to 4.

## Stage 4 — Signatures, transposes, duals

For each table compute `sig(M)` over the law universe: 131 laws for the fast path,
all 4694 for the complete path. Add `sig(Mᵀ)` by bit permutation through the dual
map (see [`01-method.md`](01-method.md) §2), never by re-sweeping.

| Quantity | Value |
|---|---|
| tables after transposes | 1892 |
| laws in the fast path | 131 |
| laws in the complete path | 4694 |
| fast path time | 2.3 s |
| complete path time | 63 s |
| selfcheck samples (stack machine vs naive recursion) | 200, 0 disagreements |

## Stage 5 — Coverage arithmetic

This is the stage that turns the result into a statement about *both* corpora
rather than about one.

| Quantity | Value | How |
|---|---|---|
| `C_etp`, direct indexing | 916 / 1054 | measured |
| `C_etp`, with transposes | **940 / 1054** | measured |
| `C_car` (parsimagma's corpus) | **790 / 1054** | **their reported number** (411 + 379) |
| `C_etp ∩ C_car` | 676 | `940 − 264` |
| `C_car \ C_etp` | 114 | `790 − 676`, enumerated in `coverage_arithmetic.json` |
| `C_etp \ C_car` | 264 | the residual |
| union | 1054 / 1054 | `940 + 790 − 676` |

Two checks that catch an arithmetic slip immediately:

- `264 ⊆ C_etp` — every residual pair has a witness among the published tables;
- `1054 − 790 = 264` — agrees with the row count of the residual list.

The 114 pairs that no published table separates are listed explicitly. They are the
argument for merging the corpora rather than replacing one with the other.

## Stage 6 — Witness selection

For each pair, collect all tables that separate it, then pick a canonical one with a
deterministic sort:

1. prefer a non-transposed table (cheaper to reproduce);
2. then smaller carrier;
3. then table name.

Record for every pair: the pair, the site (1062 or 814 side), both law texts, the
witness table, carrier, transpose flag, sha256 of the table, the refuting
assignment, the number of alternative witnesses, and which evaluators agreed.

| Result | Value |
|---|---|
| pairs with a witness | 264 |
| from a non-transposed table | 240 |
| requiring a transpose | 24 |
| distinct tables used | 31 |
| pairs closed by `Refutation899` alone | 137 |
| pairs closed by the top three tables | 210 |

## Stage 7 — Verification

Three evaluators, no shared code path:

| # | Evaluator | Where |
|---|---|---|
| 1 | stack machine over a compiled instruction list (`FastLaw`) | `scripts/reverse_index.py` |
| 2 | naive recursion on the term tree (`refutes_naive`) | same file |
| 3 | independent library written for a different task | `scripts/etp_magma_lib.py` |

The check is stronger than "both say yes": all three must agree on **satisfaction**,
on **refutation**, and on the **witnessing assignment** — the same map from variables
to elements. A disagreement exits non-zero and stops the build.

| Result | Value |
|---|---|
| pairs where all three agree | 264 |
| conflicts | 0 |
| independent regression of evaluator 3 against corpus files | 3,874,236 (table, law) judgments in 5 groups, 0 disagreements |

## Stage 8 — Lean generation and compile check

Generate one file per witness table in the shape of ETP's own `Generated` family:

```lean
def «Refutation899» : Magma (Fin 9) where op := finOpTable "[[...]]"
@[equational_result]
theorem «facts Refutation899» : ∃ (G : Type) (_ : Magma G) (_ : Finite G),
    Facts G [168, 1486, ...] [3462, ...] := ⟨Fin 9, «Refutation899», …, by decideFin!⟩
```

The `Facts` lists are computed from `witnesses_264.json`, not copied from the
upstream annotation.

| Result | Value |
|---|---|
| files | 31 |
| compiled with `lake env lean`, Lean 4.29.1 | 31 of 31 passed; 384 s and 423 s on two independent runs (about 6.5 to 7 minutes) |
| structure checked independently | 31 passed, 0 failed |

Compilation is a **separate** evidence line from the mathematics. The mathematics is
settled by stages 6–7 in Python: a table that satisfies the hypothesis and refutes
the target *is* a counterexample, and that is a finite computation. The Lean files
show the same statements can be stated in the project's own idiom and typecheck.

## Stage 9 — Package and gate

| Step | What it produces |
|---|---|
| sort and canonicalise all JSON | stable diffs, reviewable numbers |
| sanitize absolute paths to `$ETP_HOME` / `$WORKSPACE` | no machine layout in a public repository |
| `scripts/scan_sensitive.py --root .` | exit 1 on any local path, name, or institution |
| `scripts/selfcheck.py --root .` | no BOM, every relative link resolves, checksums match |
| `CHECKSUMS.txt` | sha256 of every file, self-verified |

## Where the pipeline can silently go wrong

Each of these produced a wrong answer at some point; each is in
[`03-pitfalls.md`](03-pitfalls.md) with the fix:

- the RLE decode counting `unknown` as a refutation (450 becomes 452);
- `implications.bits.gz` read in the wrong orientation (5.7 million violations);
- treating the `Facts` annotation as a complete index (this is the whole residual);
- adding transposes without the dual permutation (24 pairs lost);
- sweeping only the original pair, not the dual pair (1 pair lost, one wasted workstream);
- a substitution found but the reverse direction assumed (turns an implication into an equivalence).
