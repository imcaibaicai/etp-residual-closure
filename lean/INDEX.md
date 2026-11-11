# Lean witness files, one per table

All 31 files compile. Each was run through `lake env lean` against Lean 4.29.1, the
version pinned by the project's `lean-toolchain`: 31 passed, 0 failed, 423.4 s total.
Per-file exit codes and wall times are in
[`../data/lean_compile_check.json`](../data/lean_compile_check.json), produced by
[`check_lean_compile.py`](../scripts/check_lean_compile.py).

That is 31 individual compilations after a targeted build of the modules they import
— **not** a full `lake build`, **not** CI, and **not** a maintainer review. Read
[`../docs/06-boundaries.md`](../docs/06-boundaries.md) before describing it otherwise.

Reproducing needs the project's own modules built first: a fresh checkout carries the
dependency oleans but no `equational_theories` oleans, so the imports fail with
`unknown module prefix` until these run.

```
lake build equational_theories.Equations.All
lake build equational_theories.FactsSyntax equational_theories.MemoFinOp \
           equational_theories.DecideBang
python3 scripts/check_lean_compile.py \
    --project "$ETP_HOME/equational_theories" --lean-dir lean
```

Names follow the corpus' module names with `.` written as `__`: `Refutation899` comes
from `equational_theories/Generated/All4x4Tables/Refutation899.lean`. A `T` suffix in
the file name means the transpose of that table.

| file | carrier | pairs separated | satisfied laws listed | refuted laws listed |
|---|---|---|---|---|
| file | carrier | pairs separated | satisfied laws listed | refuted laws listed |
|---|---|---|---|---|
| `Witness_Refutation889.lean` | 6 | 1 | 1 | 1 |
| `Witness_Refutation895.lean` | 8 | 2 | 1 | 2 |
| `Witness_Refutation913.lean` | 8 | 3 | 1 | 3 |
| `Witness_Refutation899.lean` | 9 | 137 | 5 | 32 |
| `Witness_Refutation36.lean` | 11 | 2 | 1 | 2 |
| `Witness_Refutation870.lean` | 11 | 1 | 1 | 1 |
| `Witness_Refutation930T.lean` | 12 | 1 | 1 | 1 |
| `Witness_Refutation930.lean` | 12 | 1 | 1 | 1 |
| `Witness_Refutation939T.lean` | 15 | 4 | 1 | 4 |
| `Witness_Refutation939.lean` | 15 | 4 | 1 | 4 |
| `Witness_Refutation933.lean` | 19 | 1 | 1 | 1 |
| `Witness_Refutation933T.lean` | 19 | 1 | 1 | 1 |
| `Witness_Refutation932.lean` | 21 | 2 | 1 | 2 |
| `Witness_Refutation924.lean` | 21 | 38 | 1 | 38 |
| `Witness_Refutation924T.lean` | 21 | 3 | 1 | 3 |
| `Witness_Refutation923.lean` | 21 | 35 | 1 | 35 |
| `Witness_Refutation929.lean` | 21 | 2 | 1 | 2 |
| `Witness_Refutation932T.lean` | 21 | 2 | 1 | 2 |
| `Witness_Refutation929T.lean` | 21 | 2 | 1 | 2 |
| `Witness_Refutation934.lean` | 24 | 2 | 1 | 2 |
| `Witness_Refutation934T.lean` | 24 | 2 | 1 | 2 |
| `Witness_Refutation931.lean` | 25 | 1 | 1 | 1 |
| `Witness_Refutation931T.lean` | 25 | 1 | 1 | 1 |
| `Witness_Refutation937.lean` | 35 | 1 | 1 | 1 |
| `Witness_Refutation937T.lean` | 35 | 1 | 1 | 1 |
| `Witness_Refutation935.lean` | 36 | 3 | 1 | 3 |
| `Witness_Refutation936T.lean` | 36 | 2 | 1 | 2 |
| `Witness_Refutation936.lean` | 36 | 2 | 1 | 2 |
| `Witness_Refutation935T.lean` | 36 | 3 | 1 | 3 |
| `Witness_Refutation938T.lean` | 65 | 2 | 1 | 2 |
| `Witness_Refutation938.lean` | 65 | 2 | 1 | 2 |

Total: 31 files, 264 pairs.
