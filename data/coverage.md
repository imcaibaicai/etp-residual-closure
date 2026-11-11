# Coverage: 790 → 1054 of 1054 finitely refutable pairs

All figures below are recomputed from the sources named next to them. Nothing is
copied from the numbers in `README.md` or `docs/`; where a number can only be
inferred rather than measured, it says so.

## 1. The denominator: 1054

| Site | Pairs | Source |
|---|---|---|
| Implications Vampire left undecided | 1062 | `data/etp/hard_core.txt` (1062 data rows) |
| of which require an infinite model | 610 | `finite_graph.json` records the pair as an implication |
| of which have a finite counterexample | 450 | `finite_graph.json` records it as refuted for all finite magmas |
| of which the ETP left open | 2 | `finite_graph.json` value `unknown`, only cells 2 of 22,033,636 |
| The two open pairs | `(677,255)`, `(2910,47)` | same decode |
| Saturation-refuted pairs | 814 | `data/etp/saturation_refuted.txt` |
| of which have a finite counterexample | 604 | `finite_graph.json` |
| of which have no finite countermodel | 210 | 814 − 604 |
| **Finitely refutable total** | **1054** | 450 + 604 |

The 450 and the 604 are also the two figures `parsimagma` reports in `README.md`
and `docs/infinite-only-exact.md`; the recomputation here is what confirms them
under the decode below.

Decoding note that changes the answer: `rle_encoded_array` is a list of
`(value, runLength)` pairs, and the nine values are the indices of
`explicit_conjecture_false`, `explicit_conjecture_true`, `explicit_proof_false`,
`explicit_proof_true`, `implicit_conjecture_false`, `implicit_conjecture_true`,
`implicit_proof_false`, `implicit_proof_true`, `unknown`
(`scripts/generate_equation_explorer_graph.py` lines 17–27), with an implication
present iff the value is odd (line 74). Treating "value nonzero" as "refuted"
yields 452 instead of 450 on the 1062 side, because the two `unknown` cells are
then miscounted; excluding value 8 is what makes the split 610 + 450 + 2 = 1062.

## 2. Coverage before and after

| Corpus | Finitely refutable pairs covered | Note |
|---|---|---|
| `parsimagma` corpus (as reported) | 790 / 1054 (75.0%) | 411 of 450 and 379 of 604, `README.md` and `docs/infinite-only-exact.md` |
| ETP published tables, direct indexing only | 916 / 1054 (86.9%) | measured, `coverage_upstream_direct.json` |
| ETP published tables + transposes | 940 / 1054 (89.2%) | measured, `coverage_sets.json` |
| `parsimagma` corpus ∪ this package | 1054 / 1054 | 790 + 264 with no overlap, see §3 |

Transposes contribute 24 pairs net: 916 → 940 overall, and 240 → 264 on the
residual.

## 3. The three-number relation

Let `FR` be the 1054 finitely refutable pairs, `C_etp` the 940 witnessed by the
946 published ETP tables plus their transposes, and `C_car` the 790 witnessed by
the `parsimagma` corpus.

`C_car = 790` is `parsimagma`'s own figure, not a measurement made here: it is
the sum of the two numbers in the maintainer's own `#1474` comment of 2026-08-28,
whose two ASCII breakdown tables report "witnessed by my corpus **411**" of the
1062 side and "witnessed by my corpus **379**" of the 814 side. The two totals
also appear in `README.md` ("the corpus witnesses 411 of the 450") and
`docs/infinite-only-exact.md`.

| Quantity | Value | How obtained |
|---|---|---|
| `C_etp` | 940 | measured: 946 tables + transposes vs `FR` |
| `C_car` | 790 | reported by `parsimagma`: 411 + 379 (`#1474`, 2026-08-28) |
| `C_etp ∩ C_car` | **676** | measured: `C_etp` minus the 264 |
| `C_car \ C_etp` | **114** | measured: `FR \ C_etp`, equal to `790 − 676` |
| `C_etp \ C_car` | 264 | the residual, all of it inside `C_etp` |
| Check | `264 ⊆ C_etp` holds | every residual pair has a witness among the published tables |
| Check | `1054 − 790 = 264` | agrees with the residual list's own row count |

The 114 pairs are listed in `coverage_arithmetic.json`
(`carlok_only_pairs`): 98 on the 1062 side, 16 on the 814 side. Neither corpus
contains them; the ETP tables refute each of them, but no single published table
satisfies the hypothesis and refutes the target.

So the two corpora are incomplete in different places, and their union is the
whole set. The repair is not a stronger search.

## 4. Why the residual was invisible: 206 of 264

For each residual pair, the witness table either does or does not annotate that
pair in its own `Facts` line (`full_entries`, 1119 `f` records in
`finite_graph.json`).

| Witness situation | Pairs | Source |
|---|---|---|
| Witness table's `Facts` lists this pair | 58 | `silent_witnesses.json` |
| Witness table's `Facts` never lists this pair | **206** | same |
| Total | 264 | `data/etp/finite_uncovered.txt` |

206 of 264 pairs are separated by a table that is already published, whose
annotation simply does not mention them. An index keyed on the annotated pair
cannot see them.

## 5. Where the tables come from

| Item | Value | Source |
|---|---|---|
| `.lean` files under the generated directory | 1171 | `$ETP_HOME/etp-refutations-all` |
| files with a parseable `finOpTable "[[" literal` | 946 | 225 files have none (`ManuallyProved`, `FiniteImplicationSearch`, …) |
| distinct carrier sizes among the 946 | 2 … 65 | 14 tables at 9, 5 at 11, 4 at 21, 2 at 36, 1 at 65 |
| tables needed to witness all 264 pairs | 31 | `witnesses_264.json` |
| pairs witnessed by `Refutation899` alone (carrier 9) | 137 | same |
| next two: `Refutation924` (21), `Refutation923` (21) | 38, 35 | same |

The 9-element table answers 137 of the 264 questions; the top three answer 210.

## 6. Transposes

24 of the 264 pairs have no non-transposed witness. They are:

```
(2054,255) (2054,2644) (2054,2847) (2054,3456) (2091,2098) (2126,3456)
(2126,3457) (2126,3511) (2126,3512) (2126,3513) (2497,1832) (2531,1313)
(2531,4435) (2650,3253) (2712,2449) (2712,2452) (2712,3065) (2712,3519)
(2712,4128) (3069,307) (3069,3253) (3069,3456) (3076,307) (3076,3253)
```

18 of the 24 are on the 1062 side, which is why that side's residual resisted a
direct sweep. Adding transposes costs one table per published table and 30
seconds of CPU over the whole corpus.
