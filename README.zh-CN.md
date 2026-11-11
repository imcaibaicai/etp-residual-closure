# etp-residual-closure

Equational Theories Project（ETP）的 264 对蕴含残差，用 ETP 已经公开的表全部闭合。仓库另外附一份给 AI Agent 的作业手册。

**简体中文** · [English](README.md)

![license](https://img.shields.io/badge/code-MIT-blue) ![data](https://img.shields.io/badge/data-Apache--2.0-green) ![python](https://img.shields.io/badge/python-3.8%2B%20stdlib-yellow) ![lean](https://img.shields.io/badge/lean-4.29.1-purple)

## 问题

`carlok/parsimagma` 的 `data/etp/finite_uncovered.txt` 列了 264 对蕴含。ETP 早就证明这 264 对都存在有限反例，但那个仓库的构造语料一对也没造出来。

现在这 264 对全部有明确的有限见证，见证全部取自 ETP 自己公开的 `Generated/All4x4Tables` 目录。没有新造岩浆，没有跑扩张族，没有扩大搜索范围，也没有换求解器。

语料本来就是够用的，缺的是索引。

31 张表闭合全部 264 对，其中 9 元的 `Refutation899` 一张表覆盖 137 对。

## 三个数字

| 数字 | 含义 | 出处 |
|---|---|---|
| 206 / 264 | 见证表自己的 `Facts` 注解从未提到该对的对数 | `data/silent_witnesses.json` |
| 31 | 闭合全部 264 对需要的去重表数 | `data/witnesses_264.json` |
| 137 | 单张 9 元表覆盖的对数 | 同上 |

206/264 说明的是诊断结论：这些见证表早就公开了，只是被索引在「它是为哪一对生成的」这个键上，而不是「它满足哪些律」这个键上。按注解对建的任何索引都看不见它们，搜索做得再强也没用。31 是修法的规模，比它替换掉的那份残差清单还短。

## 两份语料都不完整，漏的不是同一批

对照 ETP 有限蕴含图，可有限反驳的对共 1054 对（1062 侧 450 对，814 侧 604 对）：

| 语料 | 覆盖的可有限反驳对 | 怎么得到的 |
|---|---|---|
| ETP 已公开表，直接索引 | 916 / 1054（86.9%） | 我们实测 |
| ETP 已公开表 + 转置 | 940 / 1054（89.2%） | 我们实测 |
| `parsimagma` 语料 | 790 / 1054（75.0%） | 该项目自报的数（411 + 379），不是我们测的 |
| 两者交集 | 676 | 我们实测 |
| 仅 ETP 表有 | 264 | 我们实测 |
| 仅 `parsimagma` 有 | 114 | 我们实测 |
| 并集 | 1054 / 1054 | 940 + 790 − 676 |

所以修法不是更强的求解器，而是三件事：合并两份语料、给每张表补上转置、按「满足集」建索引。三件事都有实测支撑，推导与算例在 [`docs/01-method.md`](docs/01-method.md)，逐项计数在 [`data/coverage.md`](data/coverage.md)。

## 到底哪里错了

1. **表按生成时对应的那一对索引，不按它满足哪些律索引。** `Facts` 一行记的是为这张表输出了哪些事实，不是它满足的律集。206/264 就掉在这个缝里。`sat`/`ref` 列表在设计上就不穷尽，Lean 只证明被列出来的部分。
2. **语料里没有转置。** `Tᵀ` 是同一个承载集上左右乘互换的另一张岩浆。264 对里有 24 对，在 946 张可解析表里找不到任何非转置见证。
3. **残差清单是过期快照。** 它在 1062 侧列的 39 对里有 16 对已被 `src/ext.rs` 关掉（见该仓 `docs/the-39.md` 第 147～162 行），文件此后没再重新生成，于是把两套机制各自处理的混在了一起。

## 仓库里有什么

| 路径 | 内容 |
|---|---|
| [`docs/00-what-this-is.md`](docs/00-what-this-is.md) | 从零讲起：ETP 是什么、岩浆是什么、问题是什么（中英双语） |
| [`docs/01-method.md`](docs/01-method.md) | 三个技巧的推导与算例：反向索引、替换桥接、对偶加转置 |
| [`docs/02-pipeline.md`](docs/02-pipeline.md) | 端到端流程：环境、解码、语料、匹配、验证、打包 |
| [`docs/03-pitfalls.md`](docs/03-pitfalls.md) | 11 条坑，每条给现象、根因、修法和验证办法，末尾另附两条小的 |
| [`docs/04-agent-playbook.md`](docs/04-agent-playbook.md) | 给 AI Agent 的作业手册：任务形态识别、写区互斥、验证纪律、分批落盘、报告纪律（中英双语） |
| [`docs/05-reproduce.md`](docs/05-reproduce.md) | 复现命令、预期数字、每步校验点、变量含义 |
| [`docs/06-boundaries.md`](docs/06-boundaries.md) | 证据停在什么位置：跑过什么、没跑什么、哪些数不是我们测的 |
| [`docs/07-for-etp-maintainers.md`](docs/07-for-etp-maintainers.md) | 若要变成 ETP 正式贡献，流程与形式化形状 |
| [`data/`](data/) | 264 条见证清单、31 张表、覆盖率账目、三路验证记录 |
| [`lean/`](lean/) | 31 个 Lean 见证文件，一文件一定理 |
| [`scripts/`](scripts/) | 反向索引、岩浆判定库、Lean 生成器、结构检查、数据抓取、脱敏扫描 |
| [`submission/`](submission/) | 给 `carlok/parsimagma` 的 issue 与 PR 草稿 |
| [`reports/`](reports/) | 各阶段结构化 JSON：漏斗、扫表、对偶闭合 |
| [`CHECKSUMS.txt`](CHECKSUMS.txt) | 全库每个文件的 sha256 |

## 从哪读起

- 想要方法：读 [`docs/04-agent-playbook.md`](docs/04-agent-playbook.md)。能带走的是它，264 个答案带不走。
- 想复现数字：读 [`docs/05-reproduce.md`](docs/05-reproduce.md)。
- 想拿给 `carlok/parsimagma` 用：看 [`submission/`](submission/)。
- 想知道证据边界：看 [`docs/06-boundaries.md`](docs/06-boundaries.md)。

## 一条命令复现

只依赖 Python 3 标准库，没有第三方包、不需要网络和数据库。

```bash
export ETP_HOME=/path/to/etp            # 放两个检出的目录
git clone https://github.com/teorth/equational_theories "$ETP_HOME/equational_theories"
git clone https://github.com/carlok/parsimagma "$ETP_HOME/parsimagma"

python3 scripts/reverse_index.py \
  --base "$ETP_HOME/equational_theories/equational_theories/Generated/All4x4Tables" \
  --targets "$ETP_HOME/parsimagma/data/etp/finite_uncovered.txt" \
  --equations "$ETP_HOME/parsimagma/data/etp/equations.txt" \
  --out ./out --selfcheck
```

用 `finite_uncovered.txt` 的上一个修订版跑，输出是：

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

只算目标点名的律宇宙 2.3 秒；`--laws all` 对全部 4694 条律算完整签名、带转置扫全语料 63 秒。`--no-transpose` 复现 240/264 的分裂。`--strict` 在任一目标对没有见证时退出码 1，这一条适合放进 CI。

`--selfcheck` 拿「栈机求值器」和「朴素递归求值器」在确定性抽样的（表，律）对上互相对照，两者不共用代码路径。满足性、反驳性、或反例赋值任一项出现分歧就退出 2。

## 证据

| 事项 | 结果 | 记录 |
|---|---|---|
| 264 对都有见证 | 264/264 | `data/witnesses_264.json` |
| 三个独立求值器逐对一致（含反例赋值） | 0 冲突 | `data/verification_264.json` |
| 31 个 Lean 见证文件在 Lean 4.29.1 下编译 | 31/31 通过；整套约 6.5～7 分钟（两次测量 384 秒与 423 秒，单文件 10～22 秒） | `data/lean_compile_check.json` |
| 全量 `lake build` | 没跑 | — |
| CI | 没跑 | — |
| 维护者审查 | 没有 | — |
| 264 条陈述形式化成 ETP 贡献 | 没做 | [`docs/06-boundaries.md`](docs/06-boundaries.md) |
| Lean 文件的结构检查 | 跑过，只作旁证 | `data/lean_structure_check.json` |

Lean 那一行做的是：先定向构建这 31 个文件所 import 的模块，再逐个用 `lake env lean` 编译。它不等于全量 `lake build`，也不等于 ETP 收了这批文件。

## 数据从哪来

复现要三份上游数据：

- ETP 的 `Generated/All4x4Tables`：1171 个生成文件，其中 946 个带可解析的 `finOpTable "[[...]]"` 表字面量。
- ETP 公开的有限蕴含图（RLE 编码）。[`scripts/fetch_etp_data.py`](scripts/fetch_etp_data.py) 下载后解码成 `data/graph_facts.json`。
- `parsimagma` 的 `data/etp/finite_uncovered.txt` 与 `equations.txt`。

仓库里带的是实际被引用的 31 张表，按 sha256 索引在 `data/tables_referenced.json`，ETP 自己的写法在 [`lean/`](lean/)。其余大文件用上面那个脚本或上游 checkout 现取。

## 许可与出处

- 我们自己的代码（`scripts/`、本仓库文字）：MIT，见 [`LICENSE`](LICENSE)。
- ETP 的表（946 张可解析表，以及 `data/tables_referenced.json` 里复制的 31 张）：Apache-2.0，来自 `teorth/equational_theories` 的 `equational_theories/Generated/All4x4Tables`，抓取日期 2026-11-10。表文本从 `finOpTable "[[...]]"` 字面量里读出。
- 264 对清单：Apache-2.0，来自 `carlok/parsimagma` 的 `data/etp/finite_uncovered.txt`（上一个修订版）。
- `equations.txt`：ETP，4694 条律，一行一条，行号即编号。
- `docs/01-method.md` 引用的 §5.6 扩张参数：出自 `carlok/parsimagma` 的 `docs/the-39.md` 第 147～162 行。

`parsimagma` 仓库里没有任何文件被改动，`submission/updated_finite_uncovered.txt` 是一份替换建议。完整归属见 [`NOTICE`](NOTICE)。

## 检查脚本

```bash
python3 scripts/selfcheck.py --root .                      # BOM、链接、校验和
python3 scripts/scan_sensitive.py --root . --selftest      # 用合成探针确认规则会命中
python3 scripts/scan_sensitive.py --root .                 # 扫本地路径、人名、机构名；命中即退出 1
```

`scan_sensitive.py` 只把命令行 `--deny "名字,机构"` 传进去的串当敏感串，不读任何文件。

## 引用

见 [`CITATION.cff`](CITATION.cff)。数据引上游项目，索引结论与作业手册引本仓库。

## 同批其他材料

- [`submission/issue_draft.md`](submission/issue_draft.md)：给 `carlok/parsimagma` 的 issue 文本，未发布。
- [`submission/pr_draft.md`](submission/pr_draft.md)：PR 说明，含 Rust 侧改动草图，未开。
- [`NOTICE`](NOTICE)：归属与逐文件来源。
