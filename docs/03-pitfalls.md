# 03 — Pitfalls, in the order they bit

> **中文摘要**
> 11 条实测坑，每条按「现象 → 根因 → 修法 → 怎么证明修对了」写；其中第 1、2、3 条属于「会静默给出错误数字」，第 7、8 条会骗过求解器让人以为拿到了证明。
> 最贵的两条：把 `sat`/`ref` 注解当完备索引（本案例 206/264 就是这样漏的）、扫表时只查原对而不查对偶对与转置（最后一对因此被误判为无解）。
> 每条都给出可执行的验证方式。

---

Each entry has the same four parts: **symptom** (what you see), **cause** (why),
**fix** (what to do), **check** (how to prove the fix worked). The check matters
more than the fix: every one of these failed silently at least once, producing a
number that looked right.

## 1. The RLE decode: odd means "implication holds", and value 8 is `unknown`

**Symptom.** Two different counts of "finitely refutable pairs on the 1062 side":
450 and 452. Both were reported at different times, by the same code base.

**Cause.** `finite_graph.json` stores the matrix as `rle_encoded_array`, a flat list
that **alternates value and run length** — `[v0, n0, v1, n1, …]`, 1,261,536 runs
whose lengths sum to 4694² = 22,033,636 — row-major over the laws. The nine values
are indices into the `ids` array at `scripts/generate_equation_explorer_graph.py`
lines 17–27, and value **8 is `unknown`**. The project's own consumer tests
`implications[i][j] in {1,3,5,7}` (line 74) — an implication is present iff the value
is **odd**. Code that tests "value nonzero" instead counts the 2 `unknown` cells as
refutations, giving 452.

**Fix.** Decode as `(value, runLength)`, treat odd values as "implication present",
and exclude 8 explicitly rather than relying on parity alone — a future value 9 would
slip through the parity test.

**Check.** `610 + 450 + 2 = 1062` must hold exactly. If your split sums to 1062 with
450 replaced by 452, you have counted the two `unknown` cells twice. The two open
cells are `(677, 255)` and `(2910, 47)`; print them and confirm.

## 2. `implications.bits.gz` is row-major LSB — the transpose orientation is not a tie

**Symptom.** 5.7 million violations of a property that should hold by construction,
with no single offending pair standing out.

**Cause.** Each line of the decompressed file is 587 bytes: 4694 bits, packed 8 to a
byte, **least significant bit first**, row-major over `i` then `j`. Reading `j` as
the outer index (i.e. transposing the interpretation) produces a matrix that is
*plausible* — it has the same number of set bits — but wrong almost everywhere.

**Fix.** Unpack with `(byte >> bit) & 1` where `bit = j % 8` and `byte = row[j // 8]`,
row = `i`; decoding this way gives the transpose of the matrix the other source
(`finite_graph.json`) carries.

**Check.** Cross-decode the same logical matrix from `finite_graph.json` and from
`implications.bits.gz` and require bit-for-bit equality. A count of violations that is
a large fraction of 22 million, rather than a handful, means an orientation error, not
a data error.

## 3. `Facts` annotations are not a complete index — this is the entire residual

**Symptom.** 264 pairs listed as having no witness in a corpus, when 31 published
tables separate all 264. 206 of the 264 are separated by a table whose own `Facts`
line never mentions them.

**Cause.** `full_entries` records `f|line|name|[sat]|[ref]`. The `sat` and `ref` lists
hold the facts that were *emitted* for that table — usually the pair it was built to
separate. They are **not** the set of laws the table satisfies, and Lean only proves
what is listed. An index keyed on those lists cannot see any pair that the table
was not built for.

**Fix.** Compute each table's satisfied set over all 4694 laws by evaluation. Do not
read it off the annotation. Keep the annotation as provenance only.

**Check.** For the 264 residual pairs, split by whether the chosen witness's
annotation mentions the pair: expect 58 annotated, **206 silent**
(`data/silent_witnesses.json`). If your index reports 0 silent witnesses, it is still
reading annotations.

## 4. A substitution gives you an implication, not an equivalence

**Symptom.** A claim that `E168` is equivalent to `E1487` and `E2164`, based on
having found substitutions, and then a pair counted as closed in both directions when
only one was justified.

**Cause.** If `σ` substitutes terms for variables, then `σ(L)` is a *consequence* of
`L`. That is one direction. Nothing about a substitution tells you the reverse.

**Fix.** Four substitutions relate the family:

| Substitution into `E168` | Instance |
|---|---|
| `z → z ◇ z` | `E1486` |
| `z → z ◇ w` | `E1487` |
| `y → y ◇ z`, `z → w` | `E2164` |
| `y → y ◇ y` | `E2126` |

For the equivalence claim, look up the reverse direction in ETP's implication graph
(`E168 ⟺ E1487 ⟺ E2164` holds there, both bits set). Cite the graph for the reverse
direction; cite your substitution for the forward direction. Never let one stand in
for the other.

**Check.** For every equivalence you claim, show two directed bits from the graph, or
two explicit substitutions. A single substitution plus an adjacency in a diagram is
not evidence.

## 5. Sweeping for a pair must also check the dual pair and the transpose

**Symptom.** A pair declared to have no witness anywhere in 946 tables, after a
complete sweep. It had a witness. A whole extra workstream (CNF encoding and
enumeration up to `n = 8`) was started on the strength of that negative.

**Cause.** Three different readings of "table `M` separates `(a, b)`" are all valid
and all needed:

1. `M ⊨ E_a` and `M ⊭ E_b` — the direct reading;
2. `M ⊨ E_{a*}` and `M ⊭ E_{b*}` — the same table works for the **dual pair**;
3. `Mᵀ ⊨ E_a` and `Mᵀ ⊭ E_b` — the **transpose** of the table works.

The earlier sweep only did (1). Since `sig(Mᵀ)[i] = sig(M)[dual(i)]`, reading (3) is
free once the dual map is loaded, and reading (2) is the same bit vector.

**Fix.** Query all three readings in one pass. Offline, `sig(Mᵀ)[i] = sig(M)[dual(i)]`
makes (3) a permutation of (1), and the rebuild of a coverage matrix must include
every transpose as an instance.

**Check.** `(2712, 2452)` is the witness-parity test: it must come out covered, and
its witness must be the transpose of `Refutation934` with refuting assignment
`{x:19, y:2, z:5}`. If your sweep says it is uncovered, reading (3) is missing.

## 6. Solver encoding is worth 300×; the timeout flag is not reliable

**Symptom.** `n = 7` ran 600 s and returned `unknown`; a different encoding of the
same problem returned `unsat` in 3.5 s.

**Cause.** Two things. The array encoding (`K` + a chained `Store` + `Select`) gives
the solver almost nothing to propagate on; one-hot booleans do. And
`s.set("timeout", …)` does not reliably interrupt large instances, so a "timed out"
or `unknown` result says nothing about difficulty.

**Fix.**

| Encoding | `n = 7` |
|---|---|
| Z3 array theory (`K` + `Store` chain + `Select`) | 600 s, `unknown` |
| Z3 one-hot boolean | 1.8 s |
| one-hot + canonical form "values in first-occurrence order" | 3.5 s `unsat` (was 120 s `unknown`) |
| CNF + cadical | at `n = 8` worse than Z3 with symmetry breaking |

Use one-hot. Break symmetry by requiring the table's values to appear in order of
first occurrence. Enforce the time limit **externally** (subprocess timeout), not
with the solver's own parameter.

**Check.** Run the same instance twice with two encodings and compare verdicts, not
timings. If one says `unsat` and the other `unknown`, the `unknown` one is
uninformative — `unknown` is not a proof of anything.

## 7. "There exists a position where the two sides differ" is not `∨_k (L[k] ∧ R[k])`

**Symptom.** Z3 returned `sat` for a constraint that should have been impossible, and
the assignment it produced did not actually refute the target.

**Cause.** The obligation is "there exists an assignment such that the two sides are
**different**": `∨_k (L[k] ≠ R[k])`, i.e. `∨_k (L[k] ∧ ¬R[k]) ∨ (¬L[k] ∧ R[k])`. What
was written was `∨_k (L[k] ∧ R[k])` — "there is a position where both sides are
true", which is trivially satisfiable and has nothing to do with refutation.

**Fix.** Encode disequality explicitly. With one-hot booleans, impose
`L[k] ≠ R[k]` for at least one `k` by a disjunction over `k` of
`(L[k] ∧ ¬R[k]) ∨ (¬L[k] ∧ R[k])`.

**Check.** Take every `sat` model the solver returns and evaluate it with an
independent brute-force evaluator. If the model does not refute the target as a plain
table lookup, the encoding is wrong — do not debug the solver.

## 8. "Block this table" must be one clause, not `n²` of them

**Symptom.** An exhaustive enumeration of 9-element magmas reported `unsat` after
only 3 tables had been generated.

**Cause.** Blocking a specific table means "this exact assignment of `n²` cells must
not recur": one clause over the `n²` literals, negating the whole conjunction. What
was written was `n²` *separate* clauses, each forbidding one cell's value. The
conjunction of those says every cell differs from its reference value — i.e. the next
model must be entrywise different from the last, which is a far stronger constraint
and makes the search space collapse.

**Fix.** Blocking clause: `¬(x_00 = a_00 ∧ x_01 = a_01 ∧ … )`, one clause. The
entrywise-different version is a *different* constraint and is legitimate only when
you actually want a table differing everywhere.

**Check.** After enumerating `k` tables, confirm all `k` are pairwise distinct as
tables (not merely entrywise different), and that the count of models grows as
expected on a tiny case where you can count by hand (`n = 2` has 16 magmas).

## 9. PowerShell 5.1 writes a BOM and Lean rejects the file

**Symptom.** Lean reports `1:0: error: expected token` on a file that looks fine.

**Cause.** `Out-File -Encoding utf8` and `Set-Content -Encoding UTF8` in Windows
PowerShell 5.1 write UTF-8 **with BOM**. A BOM before `import` is not a token.

**Fix.** Write bytes, not text-through-a-cmdlet:

```powershell
[System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))
```

Same rule for every text file in this repository. `scripts/selfcheck.py` fails the
build on any BOM, so the rule is enforced rather than remembered.

**Check.** `python3 scripts/selfcheck.py --root .` reports `[ok] encoding`. To
diagnose a single file, read its first three bytes: `EF BB BF` is the BOM.

## 10. Redirecting Python output through PowerShell destroys non-ASCII

**Symptom.** Law texts containing `◇` arrive as mojibake or raise
`UnicodeEncodeError: 'gbk' codec can't encode character '\u25e8'`.

**Cause.** Windows PowerShell's redirection uses UTF-16LE by default, and the console
code page is GBK for non-ASCII Windows installs. Any pipeline that has PowerShell in
the middle re-encodes the stream.

**Fix.** Let Python write the file itself (`open(..., encoding="utf-8")`), or set
`PYTHONUTF8=1` and capture the stream inside Python rather than piping it through
PowerShell. This repository's scripts all write their own outputs.

**Check.** Grep the produced file for `◇` and for the replacement character `\ufffd`:
`python3 -c "print(open('out.txt', encoding='utf-8').read().count('◇'))"` must be
non-zero when laws are involved, and `\ufffd` must be zero.

## 11. `lake env lean` fails on a fresh checkout: `unknown module prefix`

**Symptom.** `import equational_theories.Equations.All` fails at module resolution,
even though the dependency packages (mathlib, batteries, …) are present.

**Cause.** A fresh checkout carries the *dependencies'* oleans but not the project's
own. `equational_theories` was never built, so its module prefix does not exist.

**Fix.** Build exactly the modules the witness files import, before compiling them:

```
lake build equational_theories.Equations.All
lake build equational_theories.FactsSyntax equational_theories.MemoFinOp \
           equational_theories.DecideBang
lake env lean lean/Witness_Refutation899.lean
```

That is 580 + 5 jobs, about four minutes — a targeted build, not a full `lake build`.

**Check.** The first `lake env lean` invocation on a witness file must exit 0 and take
9–22 s (dominated by `decideFin!`). If it fails at module resolution, the targeted
build did not run. `scripts/check_lean_compile.py` records exit code and wall time per
file so a partial fix is visible.

## 12. Two smaller ones worth one line each

**Empty directory names in `git`.** A directory containing only ignored files
silently does not exist after clone. Every directory in this repository has at least
one tracked file for that reason.

**Locked files on Windows.** A `.json` still open in an editor or a preview pane makes
an atomic rewrite fail with a sharing violation. Write to a temp file and replace, or
close the handle; do not conclude the disk is corrupted.
