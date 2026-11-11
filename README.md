# etp-residual-closure

**264 residual implications of the Equational Theories Project, closed with tables that were already published — plus a playbook for AI agents doing this kind of work.**

[简体中文](README.zh-CN.md) · **English**

![license](https://img.shields.io/badge/code-MIT-blue) ![data](https://img.shields.io/badge/data-Apache--2.0-green) ![python](https://img.shields.io/badge/python-3.8%2B%20stdlib-yellow) ![lean](https://img.shields.io/badge/lean-4.29.1-purple)

---

## TL;DR

`carlok/parsimagma` ships `data/etp/finite_uncovered.txt`: 264 implications that the Equational Theories Project (ETP) has proved *do* have a finite counterexample, and that no construction in that corpus reaches. All 264 now have an explicit finite witness, and **every witness comes from ETP's own published `Generated/All4x4Tables` directory**. No new magma was constructed, no extension family was run, no search was widened, no solver was improved. The corpus was already complete; the index was not.

**31 tables close all 264.** One 9-element magma, `Refutation899`, separates **137** of them.

## The three numbers

| Number | What it measures | Source |
|---|---|---|
| **206 / 264** | pairs separated by a published table whose own `Facts` annotation never mentions them | `data/silent_witnesses.json` |
| **31** | distinct tables needed to close all 264 | `data/witnesses_264.json` |
| **137** | pairs that one 9-element table closes | same |

206 of 264 is the diagnosis: the witnesses were published and indexed under the *pair they were generated for*, not under *the set of laws they satisfy*. An index keyed on the annotated pair cannot see them, whatever the search does. 31 is the size of the repair, and it is smaller than the residual it replaces.

## Neither corpus is complete, and they miss different pairs

Measured against the ETP finite implication graph — 1054 finitely refutable pairs, 450 on the 1062 side plus 604 on the 814 side:

| Corpus | Finitely refutable pairs covered | How obtained |
|---|---|---|
| ETP published tables, direct indexing | 916 / 1054 (86.9%) | measured |
| ETP published tables + transposes | **940 / 1054** (89.2%) | measured |
| `parsimagma` corpus | **790 / 1054** (75.0%) | **reported by that project** (411 + 379), not measured here |
| both | 676 | measured |
| ETP tables only | 264 | measured |
| `parsimagma` only | 114 | measured |
| union | **1054 / 1054** | 940 + 790 − 676 |

So the repair is not a stronger solver. It is: **merge the two corpora, add every table's transpose, and index by satisfied set.** Each of the three is measured; see [`docs/01-method.md`](docs/01-method.md) and [`data/coverage.md`](data/coverage.md).

## What was wrong, precisely

1. **Tables are indexed by generation pair, not by satisfied set.** A `Facts` line records the facts emitted for a table; it is not the set of laws the table satisfies. 206/264 fall in that gap. The `sat`/`ref` lists are *not exhaustive* by design — Lean only proves what is listed.
2. **Transposes are absent from the corpus.** `Tᵀ` is a different magma on the same carrier with left and right swapped. 24 of the 264 pairs have no non-transposed witness anywhere among the 946 parseable tables.
3. **The residual list is a stale artifact.** 16 of the 39 pairs it lists on the 1062 side are already closed by `src/ext.rs` (see that repo's `docs/the-39.md`, lines 147–162); the file was never regenerated, so it mixes pairs two different mechanisms already handle.

## Repository layout

| Path | Contents |
|---|---|
| [`docs/00-what-this-is.md`](docs/00-what-this-is.md) | from zero: what ETP is, what a magma is, what the question is (bilingual) |
| [`docs/01-method.md`](docs/01-method.md) | the three techniques with derivations and worked examples |
| [`docs/02-pipeline.md`](docs/02-pipeline.md) | end-to-end pipeline: environment → decode → corpus → match → verify → package |
| [`docs/03-pitfalls.md`](docs/03-pitfalls.md) | 11 traps, each with symptom, root cause, fix, and how to prove the fix worked |
| [`docs/04-agent-playbook.md`](docs/04-agent-playbook.md) | **the AI-agent operating manual — the point of this repository** (bilingual) |
| [`docs/05-reproduce.md`](docs/05-reproduce.md) | commands, expected numbers, per-step check points, variable table |
| [`docs/06-boundaries.md`](docs/06-boundaries.md) | what is *not* proved, and what may not be claimed |
| [`docs/07-for-etp-maintainers.md`](docs/07-for-etp-maintainers.md) | if this were to become a formal ETP contribution |
| [`data/`](data/) | the 264-pair witness list, the 31 tables, coverage accounting, verification records |
| [`lean/`](lean/) | 31 Lean witness files, one theorem each, all compiled (see below) |
| [`scripts/`](scripts/) | reverse index, magma library, Lean generator, structure check, data fetch, sanitization scan |
| [`submission/`](submission/) | issue draft and PR draft for `carlok/parsimagma`; nothing was posted |
| [`reports/`](reports/) | structured JSON results per stage (funnel, sweeps, dual closure) |
| [`CHECKSUMS.txt`](CHECKSUMS.txt) | sha256 of every file in this repository |

## TL;DR routing

- **Want the method?** → [`docs/04-agent-playbook.md`](docs/04-agent-playbook.md). It is the artifact that transfers; the 264 answers do not.
- **Want to reproduce the numbers?** → [`docs/05-reproduce.md`](docs/05-reproduce.md).
- **Want the delivery for `carlok/parsimagma`?** → [`submission/`](submission/).
- **Want to know what is *not* claimed?** → [`docs/06-boundaries.md`](docs/06-boundaries.md). Read this before quoting any number.

## Reproducing in one command

Standard-library Python 3 only. No dependencies, no network, no database.

```bash
export ETP_HOME=/path/to/etp            # directory holding the two checkouts
git clone https://github.com/teorth/equational_theories "$ETP_HOME/equational_theories"
git clone https://github.com/carlok/parsimagma "$ETP_HOME/parsimagma"

python3 scripts/reverse_index.py \
  --base "$ETP_HOME/equational_theories/equational_theories/Generated/All4x4Tables" \
  --targets "$ETP_HOME/parsimagma/data/etp/finite_uncovered.txt" \
  --equations "$ETP_HOME/parsimagma/data/etp/equations.txt" \
  --out ./out --selfcheck
```

Expected, on the previous revision of `finite_uncovered.txt`:

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

2.3 s for the law universe named by the targets; `--laws all` computes complete 4694-law signatures over the whole corpus with transposes in 63 s. `--no-transpose` reproduces the 240/264 split. `--strict` exits 1 if any target pair is left without a witness — that is the check worth putting in CI.

`--selfcheck` cross-checks a stack-machine evaluator against a naive recursive one on a deterministic sample of (table, law) pairs. They share no code path. A disagreement on satisfaction, on refutation, or on the counterexample **assignment** is fatal and exits 2.

## Verification status

This is the part to read before believing anything above.

| What | Status | Evidence |
|---|---|---|
| 264/264 pairs have a witness | measured | `data/witnesses_264.json` |
| Three independent evaluators agree on all 264, including the refuting assignment | measured, 0 conflicts | `data/verification_264.json` |
| 31 Lean witness files compile under Lean 4.29.1 | **measured: 31 passed, 0 failed, 423.4 s** via `lake env lean` | `data/lean_compile_check.json` |
| Full `lake build` of the ETP project | **not run** | — |
| CI | **not run** | — |
| Maintainer review | **not done** | — |
| Lean formalisation of the 264 statements as ETP contributions | **not attempted** | see [`docs/06-boundaries.md`](docs/06-boundaries.md) |
| Structural check of the Lean files | run, secondary evidence only | `data/lean_structure_check.json` |

The Lean compile evidence is 31 individual files compiled with `lake env lean` after a targeted build of the modules they import. That is **not** a full `lake build`, **not** a CI run, and **not** a maintainer review. Do not describe it as "merged" or "accepted" or "formalised into ETP".

## Provenance and licence

- **Our code** (`scripts/`, `reverse_index.py`, this repository's text): MIT. See [`LICENSE`](LICENSE).
- **ETP tables** (the 946 parseable tables, and the 31 reproduced in `data/tables_referenced.json`): Apache-2.0, from `teorth/equational_theories`, directory `equational_theories/Generated/All4x4Tables`, fetched 2026-11-10. Table text is read out of `finOpTable "[[...]]"` literals.
- **The 264-pair list**: Apache-2.0, from `carlok/parsimagma`, `data/etp/finite_uncovered.txt` at its previous revision.
- **`equations.txt`**: ETP, 4694 laws, one per line, line number = law number.
- **The §5.6 extension parameters** referenced in `docs/01-method.md`: from `carlok/parsimagma`, `docs/the-39.md` lines 147–162.
- No file in `parsimagma` was modified. `submission/updated_finite_uncovered.txt` is a replacement *suggestion*.

See [`NOTICE`](NOTICE) for the full attribution statement.

## What is deliberately not in this repository

- The two 9 MB graph artifacts (`graph.json`, `finite_graph.json`) and the 1171 generated `.lean` files are **not** vendored. [`scripts/fetch_etp_data.py`](scripts/fetch_etp_data.py) downloads them and decodes the RLE arrays; only the 31 tables actually referenced are included here.
- No person names, institution names, account names, or absolute local paths. Every path is `$ETP_HOME` or `$WORKSPACE`. [`scripts/scan_sensitive.py`](scripts/scan_sensitive.py) is the pre-publication gate; it is the same script used on this repository before release:

```bash
python3 scripts/scan_sensitive.py --root . --selftest   # prove the patterns fire
python3 scripts/scan_sensitive.py --root .              # scan; exit 1 on any hit
python3 scripts/selfcheck.py --root .                   # BOM, links, checksums
```

Two operating rules for that gate. **Pass identifiers on the command line (`--deny "name,institution"`), never in a file** — a deny file is a curated inventory of exactly what must stay private, so committing one leaks more than it protects; the scanner therefore reads nothing from disk and the repository ignores deny-file names as a precaution. And **never write a real-looking absolute path into an example**, in a docstring or a comment: the scanner scans itself, and an example path makes the gate fail on its own source. The script builds its own backslashes at run time from character codes for that reason.

## Citing

[`CITATION.cff`](CITATION.cff). Cite the upstream projects for the data and this repository for the indexing result and the playbook.

## Related material from the same effort

- [`submission/issue_draft.md`](submission/issue_draft.md) — issue text for `carlok/parsimagma` (not posted).
- [`submission/pr_draft.md`](submission/pr_draft.md) — PR description with the Rust-side change sketch (not opened).
- [`NOTICE`](NOTICE) — attribution and per-file provenance.
