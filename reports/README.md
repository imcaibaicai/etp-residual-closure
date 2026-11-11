# reports/ — structured results per stage

> **中文摘要**
> 这里放各阶段的结构化 JSON：漏斗分类、扫表命中、对偶闭合、替换桥接受益、扩张参数、判定库回归。每份都注明它产出什么数字、由哪个脚本生成。
> 两份较大的可再生产物（2.1 MB 反向索引转储、643 KB 的 83 对逐对明细）的重算命令见文末「Regenerating these files」。
> 所有本地路径已脱敏为占位符；少数文件里的 `generated_by` 指流水线当时的脚本路径，它们产出的数字在 `../docs/02-pipeline.md` 里引用。

---

Every file here is JSON produced by a stage of the pipeline; a number in the
documentation traces to a machine-readable record. Paths inside them use the
placeholders from [`../docs/05-reproduce.md`](../docs/05-reproduce.md).

| File | What it records | Produced by |
|---|---|---|
| `funnel-classification.json` | per-pair classification of all 264 pairs against ETP's own `facts` index: `witness`, `witness_via_dual`, or nothing. This is the record behind the 83-pair figure (58 direct + 25 by dual) | first pass, `etp_magma_lib` + graph facts |
| `residual-sweep.json` | the eight-stage funnel down to 8 open pairs, the 65 pairs a full corpus sweep closed, and why 4 more were closed by extension parameters instead of a table | corpus sweep with `etp_magma_lib` |
| `last8-hit-tables.json` | the eight final pairs and which tables separate them, after sweeping all 946 parsed tables | corpus sweep |
| `dual-transpose-closure.json` | the last pair `(2712, 2452)`: its dual pair `(854, 1055)`, the source table, the transposed witness, and the verification of both sides including assignments | closed by hand, then verified |
| `e2452-dual-closure.json` | the same closure recorded as a chain, plus the full 24×24 transposed table and a note on a witness discrepancy | same |
| `bridge-e1486-counterexamples.json` | the 104 pairs closed by substitution bridging, each with its witness table | bridge search + verification |
| `e1487-e2164-verification.json` | verification of the 47 pairs whose hypotheses are `E1487`/`E2164` instances | verification pass |
| `e873-e854-counterexamples.json` | the 4 pairs from the `E873`/`E854` line, with the method note (all 17 local tables scanned, previous funnel scanned 5) | targeted sweep |
| `e2712-e2734-decisions.json` | encoding, dual path, reductions, verdicts and lower bounds for the `E2712`/`E2734` family | decision procedure |
| `ext-settings-16.json` | the 16 §5.6 extension settings from `carlok/parsimagma`'s `docs/the-39.md` (lines 147–163), turned into 8 machine-readable groups and independently rebuilt | reconstruction, not a new result |
| `magma-lib-regression.json` | the evaluator regression: 3,874,236 (table, law) judgments in 5 groups against corpus files, `all_agree: true` | [`../scripts/selftest_regression.py`](../scripts/selftest_regression.py) |
| `witness83-facts-crosscheck.json` | cross-check of the 83 pairs against ETP's facts records | 83-pair pass |
| `witness83-summary.json` | the 83-pair pass: outcomes, witness status, carrier sizes, per-file results | same |
| `silent-witnesses.json` | the 206 pairs whose witness table never annotates them | reverse index + facts records |
| `reverse-index-summary.json` | the strict reverse-index run's totals: 264 targets, 264 covered, 0 uncovered, 240 direct, 24 transpose-only | [`../scripts/reverse_index.py`](../scripts/reverse_index.py) |

`silent-witnesses.json` duplicates [`../data/silent_witnesses.json`](../data/silent_witnesses.json):
`data/` holds the files the deliverable package ships, `reports/` holds what the pipeline
wrote when it ran. When they disagree, the pipeline output is newer.

## Regenerating these files

| File | Command |
|---|---|
| `reverse_index.json` (935 KB to 2.1 MB) | `python3 scripts/reverse_index.py --base … --laws all` (63 s) |
| `witness83/verification.json` (643 KB) | rerun the 83-pair pass; `witness83-summary.json` carries the counts |

## Field notes

- **`leads` / `lead`** fields record *how a pair was first found*, not what closes it in
  the final package. They are the diagnosis of why the old pipeline missed it, and the
  histogram over them is `substitution_bridge 104, published_facts_index 83,
  published_table_sweep 65, corpus_full_sweep 7, ext_parameters 4, dual_transpose 1`,
  summing to 264.
- **`generated_by`** in a few files names a script path from the workspace the pipeline
  ran in. `selftest_regression.py` is shipped here; the others are not, and the values
  they record are quoted in [`../docs/02-pipeline.md`](../docs/02-pipeline.md).
- **Timestamps** are local time with offset, as recorded at runtime.
- **`all_ok` / `all_agree` / `conflicts`** are the fields that matter. An empty conflict
  list means the checks ran; a suppressed count does not.
