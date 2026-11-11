# data/ — the witness set and its accounting

> **中文摘要**
> 13 个文件：264 条见证记录（JSON + TSV 两种形态）、31 张被引用的表（按 sha256 索引）、覆盖率四件套、静默见证清单、三路验证记录、Lean 编译与结构检查记录、图解码结果、替换建议。
> 每个数字都能在这里找到承载它的文件；每份文件都能由一个脚本重算，对应命令见下。
> 所有路径已脱敏为 `$ETP_HOME` / `$WORKSPACE` 占位符。

---

| File | Contents | Regenerate with |
|---|---|---|
| `witnesses_264.json` | one record per pair: pair, site, both law texts, `leads`, witness table, carrier, transpose flag, sha256, refuting assignment, alternative witness count, evaluators and agreement | `python3 scripts/build_witnesses.py` |
| `witnesses_264.tsv` | the same witnesses as a table corpus: `Table [[...]]` then `Proves [...]`, in `data/etp/refutations*.txt` format | same |
| `tables_referenced.json` | the 31 witness tables in full, keyed by sha256, with source module name and carrier | same |
| `coverage.md` | every coverage count with its source, and the decode notes | hand-written from the JSON below |
| `coverage_arithmetic.json` | the 940 / 790 / 676 / 114 decomposition, with both pair lists enumerated | `python3 scripts/reverse_index.py --laws all` |
| `coverage_sets.json` | the 940-pair set and the 790-pair set as pair lists | same |
| `coverage_upstream_direct.json` | the 916-pair set: direct indexing, no transposes | `python3 scripts/reverse_index.py --no-transpose` |
| `silent_witnesses.json` | the 206 pairs whose witness table never annotates them | reverse index + ETP facts records |
| `verification_264.json` | totals, the `leads` histogram, and the conflict list (empty) | `python3 scripts/build_witnesses.py` |
| `lean_compile_check.json` | per-file `lake env lean` result: exit code, wall time, first error | `python3 scripts/check_lean_compile.py` |
| `lean_structure_check.json` | what the text-level structural check covered, what it did not, per-file results | `python3 scripts/check_lean_structure.py` |
| `graph_facts.json` | the 450 / 610 / 2 and 604 / 210 splits decoded from the finite implication graph | `python3 scripts/fetch_etp_data.py --decode` |
| `updated_finite_uncovered.txt` | replacement suggestion for the upstream residual list: same header, no data rows, evidence in comments | hand-written; mirrored in [`../submission/`](../submission/) |

## Data dictionary: `witnesses_264.json`

| Field | Meaning |
|---|---|
| `from`, `to` | the separated pair: `E_from` does not entail `E_to` |
| `set` | `unresolved` (1062 side) or `saturation_refuted` (814 side), as in the residual list |
| `from_law`, `to_law` | the law text from `equations.txt`; its line number is the law number |
| `leads` | how the pair was first found *before* this index existed: `published_facts_index`, `substitution_bridge`, `published_table_sweep`, `corpus_full_sweep`, `ext_parameters`, `dual_transpose`. This is a diagnosis of the old pipeline, not the witness |
| `leads_via_dual` | true when the lead only worked through the dual pair |
| `witness.name` | the ETP module name of the table, with `.` written as `__`; a `#T` suffix means the transpose was used |
| `witness.carrier` | carrier size |
| `witness.is_transpose` | whether the table used is the transpose of the recorded one |
| `witness.sha256` | hash of `json.dumps(table, separators=(",", ":"))`, which is the key into `tables_referenced.json` |
| `refutation_assignment` | variables mapped to elements of the witness that make `E_to` fail |
| `alternative_witnesses` | how many other tables in the corpus also separate the pair |
| `evaluators` | which independent evaluators agreed |
| `agreement` | all three agreed on satisfaction, refutation **and** the assignment |

## Two things that are easy to misread

**`leads` is not a partition of the witness set.** It partitions the *264 pairs by
diagnosis*: 104 + 83 + 65 + 7 + 4 + 1 = 264. A pair whose lead was `substitution_bridge`
is still witnessed by whatever table `witness.name` names.

**`witnesses_264.tsv`'s `Proves` list is the complete satisfied set**, computed over all
4694 laws, not the annotated facts and not just the laws named by the pairs. The refuted
set of a table is its complement in the 4694.

## Sizes

Total about 590 KB in 13 files. The two 9 MB graph artifacts are not here:
[`../scripts/fetch_etp_data.py`](../scripts/fetch_etp_data.py) downloads and decodes them
into `graph_facts.json`, which is 49 KB.
