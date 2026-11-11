# submission/ — drafts for `carlok/parsimagma`

**Nothing in this directory has been posted.** No issue was opened, no PR was opened, no
comment was left, and no file in `carlok/parsimagma` was modified. These are drafts, in
the author's voice, for a human to review and send — or not send.

| File | What it is |
|---|---|
| `issue_draft.md` | issue text: the three measurable defects in the index, the three numbers, the coverage arithmetic, the reproduction command, and the fix in three steps |
| `pr_draft.md` | PR description if the package becomes a PR: the `src/` touch points, why the reverse index is a query rather than a data structure, why transposes are almost free, the four tests to add, and what the PR does not contain |
| `updated_finite_uncovered.txt` | replacement suggestion for `data/etp/finite_uncovered.txt`: same header, no data rows, with the evidence in comments. Byte-identical mirror of [`../data/updated_finite_uncovered.txt`](../data/updated_finite_uncovered.txt) — that copy is the one the accounting file refers to |

The 31 witness tables the drafts refer to are in [`../data/tables_referenced.json`](../data/tables_referenced.json)
(keyed by sha256) and, in ETP's own idiom, in [`../lean/`](../lean/).

## Status of every claim the drafts make

| Claim | Backing file |
|---|---|
| 264 of 264 pairs have a witness | [`../data/witnesses_264.json`](../data/witnesses_264.json) |
| 206 of 264 are separated by a table whose annotation never mentions them | [`../data/silent_witnesses.json`](../data/silent_witnesses.json) |
| 31 tables suffice; `Refutation899` closes 137 | [`../data/witnesses_264.json`](../data/witnesses_264.json) |
| three evaluators agree on all 264, including the assignment | [`../data/verification_264.json`](../data/verification_264.json) |
| 916 / 940 / 676 / 114 / 1054 | [`../data/coverage.md`](../data/coverage.md), [`../data/coverage_arithmetic.json`](../data/coverage_arithmetic.json) |
| 790 is that project's own figure | its `README.md`, `docs/infinite-only-exact.md`, and the 2026-08-28 comment on #1474 — **not measured here** |
| the 31 Lean files compile individually | [`../data/lean_compile_check.json`](../data/lean_compile_check.json) |

## If you are the person who will send these

1. Read [`../docs/06-boundaries.md`](../docs/06-boundaries.md) first. It lists what must
   not be claimed, and the drafts are only safe to send if you believe it.
2. Check the residual revision. `finite_uncovered.txt` has been regenerated upstream at
   least once; if its row count is no longer 264, the issue text needs its numbers and
   its framing adjusted — the defects hold either way, the counts do not.
3. Decide about the 16 stale rows separately. The claim that `src/ext.rs` already closes
   16 of the 39 rows on the 1062 side is a bug report on its own, and it is easier to
   accept than a corpus change.
4. Send it yourself. Nobody should post to someone else's repository on your behalf,
   and this package deliberately does not automate that.
