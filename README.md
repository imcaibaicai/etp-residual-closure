# etp-residual-closure

The 264 residual implications of the Equational Theories Project (ETP), all closed with tables ETP has already published. The repository also carries a working manual for AI agents.

[简体中文](README.zh-CN.md) · **English**

![license](https://img.shields.io/badge/code-MIT-blue) ![data](https://img.shields.io/badge/data-Apache--2.0-green) ![python](https://img.shields.io/badge/python-3.8%2B%20stdlib-yellow) ![lean](https://img.shields.io/badge/lean-4.29.1-purple)

## The problem

`data/etp/finite_uncovered.txt` in `carlok/parsimagma` lists 264 implications. ETP proved long ago that all 264 have a finite counterexample, but the construction corpus in that repository produces a witness for none of them.

All 264 now have an explicit finite witness, and every witness is taken from ETP's own published `Generated/All4x4Tables` directory. No new magma was constructed, no extension family was run, the search was not widened, and the solver was not changed.

The corpus was sufficient all along. What was missing was the index.

31 tables close all 264 pairs. One 9-element table, `Refutation899`, covers 137 of them on its own.

## The three numbers

| Number | Meaning | Source |
|---|---|---|
| 206 / 264 | pairs that the witness table's own `Facts` annotation never mentions | `data/silent_witnesses.json` |
| 31 | distinct tables needed to close all 264 pairs | `data/witnesses_264.json` |
| 137 | pairs covered by one 9-element table | same |

206/264 states the diagnosis: these witness tables have been public for a long time, but they are indexed under the pair they were generated for rather than under the laws they satisfy. Any index keyed on the annotated pair cannot see them, and a stronger search does not help. 31 is the size of the repair, and it is shorter than the residual list it replaces.

## Neither corpus is complete, and they miss different pairs

Measured against the ETP finite implication graph, 1054 pairs are finitely refutable: 450 on the 1062 side and 604 on the 814 side.

| Corpus | Finitely refutable pairs covered | How obtained |
|---|---|---|
| ETP published tables, indexed directly | 916 / 1054 (86.9%) | measured here |
| ETP published tables plus transposes | 940 / 1054 (89.2%) | measured here |
| `parsimagma` corpus | 790 / 1054 (75.0%) | the numbers that project reports (411 + 379), not measured here |
| intersection of the two | 676 | measured here |
| ETP tables only | 264 | measured here |
| `parsimagma` only | 114 | measured here |
| union | 1054 / 1054 | 940 + 790 − 676 |

So the repair is not a stronger solver. It is three things: merge the two corpora, add a transpose for every table, and index by the set of laws a table satisfies. All three rest on measurement; the derivations and worked examples are in [`docs/01-method.md`](docs/01-method.md), and the per-item counts are in [`data/coverage.md`](data/coverage.md).

## What went wrong

1. **Tables are indexed by the pair they were generated for, not by the laws they satisfy.** A `Facts` line records which facts were emitted for a table, not the set of laws the table satisfies. 206/264 falls in that gap. The `sat`/`ref` lists are not exhaustive by design, and Lean proves only the part that is listed.
2. **The corpus has no transposes.** `Tᵀ` is a different magma on the same carrier with left and right multiplication swapped. 24 of the 264 pairs have no non-transposed witness anywhere among the 946 parseable tables.
3. **The residual list is a stale snapshot.** 16 of the 39 pairs it lists on the 1062 side are already closed by `src/ext.rs` (see `docs/the-39.md` lines 147–162 in that repository). The file was never regenerated, so pairs handled by two different mechanisms ended up in one list.

## What is in the repository

| Path | Contents |
|---|---|
| [`docs/00-what-this-is.md`](docs/00-what-this-is.md) | starting from zero: what ETP is, what a magma is, what the question is (bilingual) |
| [`docs/01-method.md`](docs/01-method.md) | derivations and worked examples for the three techniques: reverse index, substitution bridging, duality with transpose |
| [`docs/02-pipeline.md`](docs/02-pipeline.md) | end-to-end flow: environment, decoding, corpus, matching, verification, packaging |
| [`docs/03-pitfalls.md`](docs/03-pitfalls.md) | 11 traps, each with symptom, root cause, fix, and a way to verify the fix; two smaller ones at the end |
| [`docs/04-agent-playbook.md`](docs/04-agent-playbook.md) | working manual for AI agents: recognising the task shape, disjoint write scopes, verification discipline, batched writes, reporting discipline (bilingual) |
| [`docs/05-reproduce.md`](docs/05-reproduce.md) | reproduce commands, expected numbers, per-step check points, meaning of each variable |
| [`docs/06-boundaries.md`](docs/06-boundaries.md) | where the evidence stops: what was run, what was not, which numbers are not ours |
| [`docs/07-for-etp-maintainers.md`](docs/07-for-etp-maintainers.md) | process and formalisation shape if this becomes a formal ETP contribution |
| [`data/`](data/) | the 264 witness records, the 31 tables, coverage accounting, three-way verification records |
| [`lean/`](lean/) | 31 Lean witness files, one theorem per file |
| [`scripts/`](scripts/) | reverse index, magma decision library, Lean generator, structure check, data fetch, sanitisation scan |
| [`submission/`](submission/) | issue and PR drafts for `carlok/parsimagma` |
| [`reports/`](reports/) | structured JSON per stage: funnel, table sweeps, dual closure |
| [`CHECKSUMS.txt`](CHECKSUMS.txt) | sha256 of every file in the repository |

## Where to start reading

- Want the method: read [`docs/04-agent-playbook.md`](docs/04-agent-playbook.md). The manual is what transfers; the 264 answers do not.
- Want to reproduce the numbers: read [`docs/05-reproduce.md`](docs/05-reproduce.md).
- Want something to hand to `carlok/parsimagma`: see [`submission/`](submission/).
- Want the evidence boundary: see [`docs/06-boundaries.md`](docs/06-boundaries.md).

## Reproducing in one command

Python 3 standard library only. No third-party packages, no network, no database.

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

Run against the previous revision of `finite_uncovered.txt`, the output is:

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

2.3 s to compute the law universe named by the targets; `--laws all` computes full signatures over all 4694 laws for the whole corpus with transposes in 63 s. `--no-transpose` reproduces the 240/264 split. `--strict` exits 1 when any target pair is left without a witness, which makes it usable in CI.

`--selfcheck` compares a stack-machine evaluator against a naive recursive evaluator on deterministically sampled (table, law) pairs, and the two share no code path. A disagreement on satisfaction, on refutation, or on the counterexample assignment exits 2.

## Evidence

| Item | Result | Record |
|---|---|---|
| All 264 pairs have a witness | 264/264 | `data/witnesses_264.json` |
| Three independent evaluators agree pair by pair, including the refuting assignment | 0 conflicts | `data/verification_264.json` |
| 31 Lean witness files compile under Lean 4.29.1 | 31/31 pass; the whole set takes about 6.5–7 minutes (two runs of 384 s and 423 s, 10–22 s per file) | `data/lean_compile_check.json` |
| Full `lake build` | not run | — |
| CI | not run | — |
| Maintainer review | none | — |
| The 264 statements formalised as ETP contributions | not done | [`docs/06-boundaries.md`](docs/06-boundaries.md) |
| Structural check of the Lean files | run, used as secondary evidence only | `data/lean_structure_check.json` |

The Lean row was produced by first building the modules that these 31 files import, then compiling each file with `lake env lean`. It is not a full `lake build`, and it does not mean ETP has taken these files.

## Where the data comes from

Reproducing takes three upstream inputs:

- ETP's `Generated/All4x4Tables`: 1171 generated files, of which 946 carry a parseable `finOpTable "[[...]]"` table literal.
- ETP's published finite implication graph (RLE encoded). [`scripts/fetch_etp_data.py`](scripts/fetch_etp_data.py) downloads it and decodes it into `data/graph_facts.json`.
- `parsimagma`'s `data/etp/finite_uncovered.txt` and `equations.txt`.

The repository carries the 31 tables that are actually cited, indexed by sha256 in `data/tables_referenced.json`, in the notation ETP itself uses in [`lean/`](lean/). The remaining large files are obtained either with the script above or from an upstream checkout.

## Licence and provenance

- Our own code (`scripts/`, the text of this repository): MIT, see [`LICENSE`](LICENSE).
- ETP tables (the 946 parseable tables, and the 31 copied in `data/tables_referenced.json`): Apache-2.0, from `equational_theories/Generated/All4x4Tables` in `teorth/equational_theories`, fetched 2026-11-10. Table text is read out of the `finOpTable "[[...]]"` literal.
- The 264-pair list: Apache-2.0, from `data/etp/finite_uncovered.txt` in `carlok/parsimagma` (previous revision).
- `equations.txt`: ETP, 4694 laws, one per line, line number is the law number.
- The §5.6 extension parameters cited in `docs/01-method.md`: from `docs/the-39.md` lines 147–162 in `carlok/parsimagma`.

No file in `parsimagma` was modified; `submission/updated_finite_uncovered.txt` is a suggested replacement. Full attribution is in [`NOTICE`](NOTICE).

## Check scripts

```bash
python3 scripts/selfcheck.py --root .                      # BOM, links, checksums
python3 scripts/scan_sensitive.py --root . --selftest      # confirm the rules fire on synthetic probes
python3 scripts/scan_sensitive.py --root .                 # scan local paths, person names, institution names; exit 1 on a hit
```

`scan_sensitive.py` treats only the strings passed on the command line with `--deny "name,institution"` as sensitive strings, and reads no file.

## Citing

See [`CITATION.cff`](CITATION.cff). Cite the upstream projects for the data, and this repository for the indexing result and the manual.

## Other material from the same batch

- [`submission/issue_draft.md`](submission/issue_draft.md): issue text for `carlok/parsimagma`, not posted.
- [`submission/pr_draft.md`](submission/pr_draft.md): PR description with a sketch of the Rust-side change, not opened.
- [`NOTICE`](NOTICE): attribution and per-file provenance.
