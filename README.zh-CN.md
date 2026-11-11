# etp-residual-closure

**Equational Theories Project（ETP）的 264 对蕴含残差，用「早已公开的表」全部闭合；外加一份给 AI Agent 的作业手册。**

**简体中文** · [English](README.md)

![license](https://img.shields.io/badge/code-MIT-blue) ![data](https://img.shields.io/badge/data-Apache--2.0-green) ![python](https://img.shields.io/badge/python-3.8%2B%20stdlib-yellow) ![lean](https://img.shields.io/badge/lean-4.29.1-purple)

---

## 一句话结论

`carlok/parsimagma` 仓库里的 `data/etp/finite_uncovered.txt` 列了 264 对蕴含：ETP 已经证明它们**确实**存在有限反例，而该仓库的构造语料一对都没能造出来。这 264 对现在全部有明确的有限见证，而且**每一条见证都取自 ETP 自己公开的 `Generated/All4x4Tables` 目录**。没有新造岩浆，没有跑扩张族，没有扩大搜索，也没有换更强的求解器。语料本来就是完备的，不完备的是索引。

**31 张表闭合全部 264 对。** 其中一张 9 元表 `Refutation899` 单独覆盖 **137 对**。

## 三个数字

| 数字 | 含义 | 出处 |
|---|---|---|
| **206 / 264** | 被「自己的 `Facts` 注解从不提及该对」的已公开表所闭合的对数 | `data/silent_witnesses.json` |
| **31** | 闭合全部 264 对所需的去重表数 | `data/witnesses_264.json` |
| **137** | 单张 9 元表覆盖的对数 | 同上 |

206/264 是**诊断**：这些见证早就公开了，只是被登记在「它是为哪一对而生成」的键上，而不是「它满足哪些律」的键上。任何以注解对为键的索引都看不见它们，搜索再强也没用。31 是**修法的规模**，比它替换掉的那份残差清单还小。

## 两份语料都不完整，而且它们漏的不是同一批

对照 ETP 有限蕴含图——共 1054 对可有限反驳（1062 侧 450 + 814 侧 604）：

| 语料 | 覆盖的可有限反驳对 | 怎么得到的 |
|---|---|---|
| ETP 已公开表，直接索引 | 916 / 1054（86.9%） | 我们实测 |
| ETP 已公开表 + 转置 | **940 / 1054**（89.2%） | 我们实测 |
| `parsimagma` 语料 | **790 / 1054**（75.0%） | **该项目的自报数**（411 + 379），不是我们测的 |
| 两者交集 | 676 | 我们实测 |
| 仅 ETP 表有 | 264 | 我们实测 |
| 仅 `parsimagma` 有 | 114 | 我们实测 |
| 并集 | **1054 / 1054** | 940 + 790 − 676 |

所以修法不是更强的求解器，而是：**合并两份语料、给每张表补上转置、按「满足集」建索引**。三件事都有实测支撑，推导与算例见 [`docs/01-method.md`](docs/01-method.md)，逐项计数见 [`data/coverage.md`](data/coverage.md)。

## 到底哪里错了

1. **表是按「生成时对应的那一对」索引的，不是按「它满足哪些律」索引的。** `Facts` 行记录的是为这张表输出了哪些事实，不是它满足的律集。206/264 就掉在这个缝里。`sat`/`ref` 列表**在设计上就是不穷尽的**——Lean 只证明被列出来的部分。
2. **语料里没有转置。** `Tᵀ` 是同一个承载集上左右乘互换的另一张岩浆。264 对里有 24 对在 946 张可解析表里找不到任何非转置见证。
3. **残差清单本身是过期快照。** 它在 1062 侧列的 39 对里有 16 对已被 `src/ext.rs` 关掉（见该仓 `docs/the-39.md` 第 147～162 行），而文件此后从未重新生成，于是把两套不同机制各自处理的混合在了一起。

## 仓库结构

| 路径 | 内容 |
|---|---|
| [`docs/00-what-this-is.md`](docs/00-what-this-is.md) | 从零讲：ETP 是什么、岩浆是什么、问题是什么（中英双语） |
| [`docs/01-method.md`](docs/01-method.md) | 三个技巧的推导与算例（反向索引／替换桥接／对偶加转置） |
| [`docs/02-pipeline.md`](docs/02-pipeline.md) | 端到端流程：环境 → 解码 → 语料 → 匹配 → 验证 → 打包 |
| [`docs/03-pitfalls.md`](docs/03-pitfalls.md) | 11 个坑，每条给现象、根因、修法、如何验证修对了 |
| [`docs/04-agent-playbook.md`](docs/04-agent-playbook.md) | **给 AI Agent 的作业手册——本仓库真正的目的**（中英双语） |
| [`docs/05-reproduce.md`](docs/05-reproduce.md) | 复现命令、预期数字、每步校验点、变量含义表 |
| [`docs/06-boundaries.md`](docs/06-boundaries.md) | 没证什么、不能声称什么 |
| [`docs/07-for-etp-maintainers.md`](docs/07-for-etp-maintainers.md) | 若要变成 ETP 正式贡献，流程与形式化形状 |
| [`data/`](data/) | 264 条见证清单、31 张表、覆盖率论证、三路验证记录 |
| [`lean/`](lean/) | 31 个 Lean 见证文件，一文件一定理，全部编译通过（见下） |
| [`scripts/`](scripts/) | 反向索引、岩浆判定库、Lean 生成器、结构检查、数据抓取、脱敏扫描 |
| [`submission/`](submission/) | 给 `carlok/parsimagma` 的 issue 与 PR 草稿；一个都没发出去 |
| [`reports/`](reports/) | 各阶段结构化 JSON（漏斗、扫表、对偶闭合） |
| [`CHECKSUMS.txt`](CHECKSUMS.txt) | 全库每个文件的 sha256 |

## 按目的跳转

- **想学方法？** → [`docs/04-agent-playbook.md`](docs/04-agent-playbook.md)。可迁移的是它，264 个答案不是。
- **想复现数字？** → [`docs/05-reproduce.md`](docs/05-reproduce.md)。
- **想拿给 `carlok/parsimagma` 的交付件？** → [`submission/`](submission/)。
- **想知道什么**没**被证明？** → 先读 [`docs/06-boundaries.md`](docs/06-boundaries.md)，再引用任何数字。

## 一条命令复现

只依赖 Python 3 标准库。无第三方包、无网络、无数据库。

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

用 `finite_uncovered.txt` 的上一个修订版跑，预期输出：

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

只算目标点名的律宇宙 2.3 秒；`--laws all` 对全部 4694 条律算完整签名，带转置扫全语料 63 秒。`--no-transpose` 复现 240/264 的分裂。`--strict` 在任一目标对没有见证时以退出码 1 结束——这才是值得放进 CI 的检查。

`--selfcheck` 会让「栈机求值器」与「朴素递归求值器」在确定性抽样的（表，律）对上互相对照，两者不共用任何代码路径。一旦在满足性、反驳性、或**反例赋值**上出现分歧即致命，退出码 2。

## 验证状态

这一段要在相信上面任何一句话之前读。

| 事项 | 状态 | 证据 |
|---|---|---|
| 264/264 对都有见证 | 实测 | `data/witnesses_264.json` |
| 三个独立求值器对全部 264 对一致（含反驳赋值） | 实测，0 冲突 | `data/verification_264.json` |
| 31 个 Lean 见证文件在 Lean 4.29.1 下编译通过 | **实测：31/31 通过**，整套约 6.5～7 分钟（两次独立测量：384 秒与 423 秒；单文件 10～22 秒） | `data/lean_compile_check.json` |
| 全量 `lake build` | **没跑** | — |
| CI | **没跑** | — |
| 维护者审查 | **没有** | — |
| 把 264 条陈述形式化成 ETP 贡献 | **没做** | 见 [`docs/06-boundaries.md`](docs/06-boundaries.md) |
| Lean 文件的结构检查 | 已跑，仅作次要证据 | `data/lean_structure_check.json` |

Lean 编译这条证据的含义是：在做完所 import 模块的定向构建之后，31 个文件各自用 `lake env lean` 编译通过。这**不是**全量 `lake build`，**不是** CI，**不是**维护者审查。不要把它描述成「已合并」「已接受」「已形式化进 ETP」。

## 来源与许可

- **我们自己的代码**（`scripts/`、`reverse_index.py`、本仓库文字）：MIT，见 [`LICENSE`](LICENSE)。
- **ETP 的表**（946 张可解析表，以及 `data/tables_referenced.json` 里复制的 31 张）：Apache-2.0，来自 `teorth/equational_theories` 的 `equational_theories/Generated/All4x4Tables`，抓取日期 2026-11-10。表文本从 `finOpTable "[[...]]"` 字面量里读出。
- **264 对清单**：Apache-2.0，来自 `carlok/parsimagma` 的 `data/etp/finite_uncovered.txt`（上一个修订版）。
- **`equations.txt`**：ETP，4694 条律，一行一条，行号即编号。
- **`docs/01-method.md` 引用的 §5.6 扩张参数**：出自 `carlok/parsimagma` 的 `docs/the-39.md` 第 147～162 行。
- `parsimagma` 仓库里没有任何文件被改动。`submission/updated_finite_uncovered.txt` 只是一份替换**建议**。

完整归属声明见 [`NOTICE`](NOTICE)。

## 刻意不入库的东西

- 两份 9 MB 的图产物（`graph.json`、`finite_graph.json`）与 1171 个生成出来的 `.lean` 文件**不**入库。[`scripts/fetch_etp_data.py`](scripts/fetch_etp_data.py) 负责下载并解码 RLE 数组；仓库里只放实际被引用的 31 张表。
- 不含人名、校名、账号名、本地绝对路径。所有路径一律写成 `$ETP_HOME` 或 `$WORKSPACE`。[`scripts/scan_sensitive.py`](scripts/scan_sensitive.py) 就是发布前的闸，本仓库发布前跑的就是它：

```bash
python3 scripts/scan_sensitive.py --root . --selftest   # 先证明规则真的会开火
python3 scripts/scan_sensitive.py --root .              # 正式扫；命中即退出码 1
python3 scripts/selfcheck.py --root .                   # BOM、链接、校验和
```

这道闸有两条操作规则。**敏感串一律走命令行 `--deny "真名,机构名"`，绝不写进文件**——deny 文件本质上是「必须保密的清单」，一旦被 `git add -A` 带上公开仓库，泄露的比它防的还多；所以扫描器不从磁盘读任何东西，仓库另外把 deny 文件名的模式列进 `.gitignore` 兜底。**也不要往文档串或注释里写像真路径的示例**：扫描器会扫自己，示例路径会让闸在自己的源码上报错——脚本里的反斜杠是用字符码在运行时拼出来的，正因如此。

## 引用

见 [`CITATION.cff`](CITATION.cff)。数据请引用上游项目，索引结论与作业手册请引用本仓库。

## 同批其他材料

- [`submission/issue_draft.md`](submission/issue_draft.md) — 给 `carlok/parsimagma` 的 issue 文本（未发布）。
- [`submission/pr_draft.md`](submission/pr_draft.md) — PR 说明，含 Rust 侧改动草图（未开）。
- [`NOTICE`](NOTICE) — 归属与逐文件来源。
