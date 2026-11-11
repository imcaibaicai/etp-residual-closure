# PR: index the corpus by satisfied set, and add transposes

Targets the 264 pairs in `data/etp/finite_uncovered.txt`. Every one of them has a
witness among ETP's published tables; 31 tables close all 264. The change is in
the corpus and in the query, not in any solver.

`finite_uncovered.txt` is a generated artifact, so this PR regenerates it from
the code path rather than replacing the file by hand.

## What changes

| Path | Change | Why |
|---|---|---|
| `data/etp/refutations_etp.txt` (new) | the 946 parseable tables from ETP's `Generated/All4x4Tables`, in the existing `Table [[...]]` / `Proves [...]` format, with a `PROVENANCE.txt` entry | the corpus does not currently contain them; they are where all 264 witnesses live |
| `src/corpus.rs` | `pub fn etp_tables_corpus(...)`, one instance per table plus one per transpose | one table routinely answers dozens of pairs; the transposes answer 24 more |
| `src/sig.rs` | `Signature::dual_permuted(&self, duals: &DualMap) -> Signature` | the signature of `Mᵀ` is a bit permutation of the signature of `M`, so no re-sweep is needed |
| `src/coverage.rs` | `CoverageMatrix::dischargers(pair)` and `CoverageMatrix::uncovered()` | the reverse direction — which instances discharge this pair — is the query that was missing, not a new index |
| `src/bin/pm.rs` | `pm reverse-index` subcommand; `pm coverage` gains the two-site report | regeneration path for `finite_uncovered.txt` |
| `data/etp/finite_uncovered.txt` | regenerated, empty | all 264 are covered |

## Why the reverse index is a query and not a data structure

`Signature` is already the index: a 4694-bit vector, and `M` separates `E_i`
from `E_j` exactly when `sig[i] && !sig[j]`. `CoverageMatrix::build` already
walks corpus × targets with `separates`. What was missing is the opposite
direction — given a pair, which instances discharge it — and that is a scan over
signatures, not a second index. The 264 pairs were invisible because the
instances that discharge them were not in the corpus and because the pair list
was consumed one pair at a time.

## Why transposes are almost free

`E_i` holds in `Mᵀ` exactly when its dual `E_i*` holds in `M`. So

```
sig(Mᵀ)[i] == sig(M)[dual(i)]
```

and `data/etp/duals.json` already carries the involution (2305 explicit pairs,
covering 4610 of the 4694 laws; the remaining 84 are self-dual). One bit
permutation per instance instead of one table sweep.

Checked on `Refutation899` (9 elements) and `Refutation934` (24): the permuted
signature equals the directly swept signature of the transpose, set for set. The
identity follows from the definition of the dual law, so it should hold for every
table; the two sweeps are only a control on the implementation.

## Expected numbers after the change

Against ETP's finite implication graph, 1054 finitely refutable pairs (450 on the
1062 side, 604 on the 814 side):

| | pairs |
|---|---|
| ETP tables, direct | 916 / 1054 |
| ETP tables + transposes | **940 / 1054** |
| current corpus | 790 / 1054 |
| both | 676 |
| tables only | 264 |
| current corpus only | 114 |
| union | **1054 / 1054** |

The 114 pairs that no published table separates stay uncovered by the ETP tables,
which is the argument for merging both corpora rather than switching to one.

## How to verify

```bash
cargo test --release
cargo run --release --bin pm -- reverse-index
```

Tests to add:

1. `corpus::tests::etp_tables_load` — the vendored file yields 946 instances and
   946 transposes; every signature has the same bit count as the law set.
2. `sig::tests::dual_permutation_matches_sweep` — for `Refutation899` and
   `Refutation934`, `sig(M).dual_permuted(duals) == sig(Mᵀ)` computed by sweep.
3. `coverage::tests::residual_is_covered` — all 264 pairs of the previous
   `finite_uncovered.txt` have a discharger in the extended corpus.
4. `coverage::tests::union_totals` — 940, 790, 676, 114, 1054 against the graph
   in `data/etp/`.

Independent cross-check outside Rust: `submission/reverse_index.py` in the
accompanying package reproduces 264/264 with two evaluators of its own, and every
witness has been re-verified by a third implementation
(`data/verification_264.json`).

## Not in this PR

- No file added to ETP's `Generated/` tree, and no claim that any was. Separately, the
  31 witness tables were written in that project's idiom and each compiles
  individually under Lean 4.29.1 via `lake env lean` — 31 of 31, about 6.5 to 7 minutes for the set (384 s and 423 s on two runs), per-file
  record in `data/lean_compile_check.json` — after a targeted build of the modules they
  import. That is not a full `lake build` and not a CI run; adding them upstream would
  require both, plus maintainer review.
- No change to any solver or family in `src/`. The numbers move because the
  corpus and the query change.
- No edit to `docs/the-39.md`. Its 39-pair analysis stands; 16 of those pairs are
  closed by `src/ext.rs` and are also separated by published tables now that the
  tables are in the corpus.
