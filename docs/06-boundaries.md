# 06 — Boundaries: what is not proved

> **中文摘要**
> 本文列出不能声称的东西：没跑全量 `lake build`、没跑 CI、没经维护者审查；Lean 文件只是按项目惯用写法写出的、逐个编译通过的陈述，不是被接受的贡献。
> 数学上本项目**不产生新定理**——ETP 早已知道这 264 对存在有限反例，本仓库提供的是「从已公开的表里把它们找出来」的索引与见证。
> 另有三条严格边界：仿射扩张的结构性否定只到 `k=2, p∈{2,3}`（实测 30/30）；946/1171 的解析率意味着可能还有可用种子；790 是 carlok 自报数，不是我们测的。

---

Read this before quoting any number from this repository.

## 1. Nothing here is a new theorem about magmas

ETP had **already proved** that these 264 pairs have finite counterexamples. That is
what the residual list is: pairs whose finite refutation is known, and for which the
construction corpus had nothing. So the mathematical content of this repository is:

- an explicit **witness table plus a refuting assignment** for each of the 264 pairs;
- a **diagnosis** that the witnesses were already published, and why the index missed them;
- an **indexing method** that finds them.

It is not a new result about equational theories, and it does not extend the frontier
of what is known. Framing it as "264 new counterexamples" would be wrong: they are
264 *located* counterexamples, of a kind already known to exist. The value is in the
location and in the method.

## 2. The Lean evidence stops well short of "formalised"

| Claim | Status |
|---|---|
| 31 witness files compile individually under Lean 4.29.1 via `lake env lean` | **measured**: 31/31, 423.4 s total, per-file exit codes recorded |
| A full `lake build` of the ETP project was run | **no** |
| The project's CI was run | **no** |
| A maintainer reviewed these files | **no** |
| These files were submitted, accepted, or merged into ETP | **no** |
| The 264 implications are formalised as ETP theorems | **no** — the 31 files are generated in the project's `Generated` idiom; acceptance is a maintainer decision and has not been requested |

Compilation means the statements typecheck and the `Facts` terms are discharged by
`decideFin!`. It does not mean the project wants them, and it does not mean the
`Facts` lists are the ones a maintainer would choose.

## 3. The mathematics is settled outside Lean

Every conclusion rests on finite computation in Python: a table that satisfies the
hypothesis and refutes the target at a specific assignment. Three independent
evaluators agree on all 264, including the assignment. Lean adds a second,
independent *representation* of the same facts — not an additional proof obligation
for the claim that these are counterexamples.

So when describing the evidence, say "witness tables verified by three evaluators,
and 31 of them also typecheck as Lean files in the project's idiom". Do not say
"formally verified".

## 4. The structural negative result on affine extensions is small-parameter only

The affine family `x ◇ y = a·x + b·y + c` over a finite field was searched for
extensions of two models. What was measured:

| Parameter range | Coverage |
|---|---|
| `k = 2` (two-step), `p ∈ {2, 3}` | 30 of 30 configurations searched |
| `k ≥ 3` | **not searched** |

So the correct statement is: "`k = 1` has a theorem; `k = 2` is a strong empirical
result over the searched configurations; `k ≥ 3` is open." Writing "for all `k`" is
not supported by anything in this repository.

## 5. `finite_uncovered.txt` is a stale snapshot, and the 264 is a historical count

The residual list was generated at a point in time:

- 16 of the 39 pairs it lists on the 1062 side are already closed by `src/ext.rs`
  (see `carlok/parsimagma`, `docs/the-39.md` lines 147–162);
- the file was never regenerated afterwards.

So the 264 mixes pairs that two different mechanisms already handle. This does not
weaken the result — all 264 do have witnesses in the published tables — but the
number 264 is a property of a historical file, not of the current state of that
project. Any "264 closed" claim must carry "as of the revision that listed 264".

## 6. The parse rate is 946 of 1171, and the gap is unexplored

225 generated `.lean` files do not write a `finOpTable "[[...]]"` literal: they use
`ManuallyProved`, `FiniteImplicationSearch`, or other shapes. Those files may contain
further usable tables. Nobody went through them by hand.

Consequence: "946 tables" is a description of what the regex sees, not of all tables
that exist in the project. The witness set of 31 is minimal **relative to the parsed
corpus**, not provably minimal overall.

## 7. One of the coverage numbers is not ours

| Number | Provenance |
|---|---|
| 916, 940, 676, 114, 1054 | measured here |
| **790** | **`parsimagma`'s own reported figure** (411 of 450 plus 379 of 604), from its `README.md`, `docs/infinite-only-exact.md`, and the maintainer's 2026-08-28 comment on issue #1474 |

The 790 was not re-measured, because doing so would require running that project's
pipeline. What this repository does check is the arithmetic around it: `940 − 264 =
676`, `790 − 676 = 114`, `940 + 790 − 676 = 1054`. If their number changes, the
union claim changes with it.

## 8. The condition (S) characterisation is an explanation, not a theorem

The analysis describes three equivalent laws as equivalent to a single condition
(operation surjective, and `Im(R_x) ◇ Im(L_x) = {x}` for every `x`). That
characterisation explains the shape of the witness. It was **not** machine-checked
and no proof is included. Cite it as analysis, never as a proved equivalence.

The equivalence claims among the laws themselves (`E168 ⟺ E1487 ⟺ E2164`) rest on
both directed bits being present in ETP's implication graph, which is a citation of
their data, not a proof by us.

## 9. Parsing conventions are an assumption

The evaluators parse `equations.txt` **right-associatively**, because the file prints
parentheses only around composite subterms: `x ◇ y ◇ z` means `x ◇ (y ◇ z)`. Every
number here depends on that convention. A tool that parses left-associatively gets a
different set of laws, and its counts will not match these — and neither will be
"wrong" in isolation; one of them just is not ETP's convention.

## 10. What is runtime-dependent

The 2.3 s and 63 s figures are single-machine wall times and will vary. The 423.4 s
Lean compile total likewise. Treat all timings as order-of-magnitude, and the counts
as exact.

## 11. What would have to happen to become an ETP contribution

Not attempted here, and it is not a small step. See
[`07-for-etp-maintainers.md`](07-for-etp-maintainers.md). In short: an author-side
formalisation in the project's own layout, a full build, CI, and a maintainer
deciding that a reverse-index dump of 264 pairs belongs in the library. The last
condition is the hard one, and it is a judgement call about what the project wants to
contain — not a mathematical question.
