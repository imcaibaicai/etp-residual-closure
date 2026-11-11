# 00 — What this is, from zero

[简体中文](#中文版) · **English**

---

## English

### The one-paragraph version

The Equational Theories Project (ETP) studies 4694 equations in a language with one
binary operation, and asks which equations imply which. 264 of those implications were
already known to have a *finite* counterexample, but a companion project's corpus of
magmas could not produce one for any of them. This repository shows that every one of
the 264 witnesses was already sitting in ETP's own published table directory, that
**31 tables cover all 264**, and that the failure was an index keyed on "what a table
was built for" rather than "what a table satisfies". Everything else here is evidence,
reproduction, and a playbook for doing that class of work with an AI agent.

Read on only if you want the definitions behind those words.

### A magma is a set with one binary operation

A *magma* is a set `G` together with a binary operation `◇ : G × G → G`. Nothing
else is assumed: no associativity, no identity, no inverses, no commutativity. A
*finite magma* is one whose carrier is finite, and it can be written out
completely as a table: `n` rows and `n` columns, every entry in `0..n-1`, where
entry `(i, j)` is `i ◇ j`.

That table is the whole object. If you have the table, you can evaluate any term.

### An equational theory is a set of identities

An *identity* (or *law*) is a universally quantified equation between two terms
built from variables and `◇`. Three examples, using the notation the Equational
Theories Project uses (`x ◇ y` for the operation):

| Law number | Text | Meaning |
|---|---|---|
| `E1` | `x = x` | true in every magma; the weakest of the 4694 |
| `E4` | `x = x ◇ y` | `x` absorbs everything on the right; the 2-element table below satisfies it |
| `E168` | `x = (y ◇ x) ◇ (x ◇ z)` | the "mother law" of the family this repository leans on: three residual hypotheses are its literal substitution instances, see [`01-method.md`](01-method.md) §3 |

A law *holds* in a magma when the two sides evaluate to the same element for
**every** assignment of elements to the variables. This is a finite check: with a
carrier of size `n` and `k` variables, there are `n^k` assignments, and each one is
a term evaluation. So for a fixed finite magma and a fixed law, satisfaction is
decidable by brute force, and a *counterexample* is a concrete assignment that
makes the two sides differ.

### A worked example small enough to check by hand

Take the set `{0, 1}` with `a ◇ b = a`, the left projection. The whole magma is this
table:

| `◇` | 0 | 1 |
|---|---|---|
| **0** | 0 | 0 |
| **1** | 1 | 1 |

Test two laws against it, with `x, y, z` ranging over `{0, 1}`:

| Law | Left side | Right side | Verdict |
|---|---|---|---|
| `E4`: `x = x ◇ y` | `x` | `x ◇ y = x` | holds for all 4 assignments |
| `E5`: `x = y ◇ x` | `x` | `y ◇ x = y` | fails at `x=0, y=1` |

So this one 2-element table is a finite counterexample to "`E4` implies `E5`": it
satisfies the hypothesis and refutes the conclusion, witnessed by the assignment
`x=0, y=1`. That is the entire mechanism of this repository — a table, an assignment,
and a mechanical check. The 264 pairs differ only in scale: carriers up to 65 elements,
and 4694 laws to test instead of a handful.

### The Equational Theories Project

The Equational Theories Project (ETP) is a collaborative project that studies
**4694** identities in this one-operation language, and asks, for pairs `(i, j)`:

> Does `E_i` imply `E_j`? That is, does every magma satisfying `E_i` also satisfy `E_j`?

There are 4694² ≈ 22 million ordered pairs. The project's implication graph
records, for each pair, whether the implication is known to hold (with proof),
known to fail (with a counterexample), or open. Two extra distinctions get
recorded for failures:

- **finite refutation**: there is a *finite* magma satisfying `E_i` and refuting `E_j`;
- **infinite-only refutation**: every refutation needs an infinite carrier.

The second is a genuinely harder statement, because no table can witness it.

### The particular gap this repository closes

A companion project, `carlok/parsimagma`, maintains a corpus of constructions: a
library of magmas, each with a signature recording which of the 4694 laws it
satisfies. It ships a file, `data/etp/finite_uncovered.txt`, that lists the pairs
where:

- ETP has proved a **finite** counterexample exists, and
- **no** construction in that corpus separates the pair.

At the previous revision of that file the list had **264 pairs** (39 from the
1062-side set, 225 from the 814-side set). Those are the pairs this repository
closes.

### Why it turned out to be an indexing problem

ETP also publishes a directory of generated refutation files,
`equational_theories/Generated/All4x4Tables/`. Each file contains one magma as an
explicit table (`finOpTable "[[...]]"`) plus a theorem in the project's `Facts`
format recording what was proved about it. 946 of the 1171 files carry a table
literal that can be parsed.

Those tables were **already public**. And it turns out they separate **all 264**
pairs. The reason the residual list did not notice is that a table's `Facts` line
records *the facts emitted for it* — normally the pair it was built to separate —
not the set of laws the table actually satisfies. One table routinely satisfies a
hypothesis law and refutes dozens of targets that were never listed.

So the fix is not a better solver. It is:

1. compute each table's **satisfied set** over all 4694 laws (not read it off the annotation);
2. **add each table's transpose**, which is a different magma on the same carrier;
3. answer the query in the **reverse direction**: given a pair, which tables discharge it.

### What is in the rest of this repository

| If you want | Read |
|---|---|
| the three techniques, with derivations and worked examples | [`01-method.md`](01-method.md) |
| the end-to-end pipeline, stage by stage | [`02-pipeline.md`](02-pipeline.md) |
| the eleven traps that produced wrong answers before they were caught | [`03-pitfalls.md`](03-pitfalls.md) |
| **how an AI agent should run a job like this** | [`04-agent-playbook.md`](04-agent-playbook.md) |
| the commands and the numbers they must produce | [`05-reproduce.md`](05-reproduce.md) |
| what is not proved and must not be claimed | [`06-boundaries.md`](06-boundaries.md) |

### Prerequisites for reading the code

Python 3.8 or newer, standard library only. No linear algebra, no SAT solver, no
graph library. The whole computation is: parse a law, evaluate it on a table for
all assignments, and intersect sets of law numbers.

---

## 中文版

### 一句话版本

Equational Theories Project（ETP）研究只有一种二元运算的语言里的 4694 条等式，追问哪条蕴含哪条。其中 264 对蕴含**已知存在有限反例**，但姊妹项目的岩浆语料一对都造不出来。本仓库说明：这 264 个见证早已躺在 ETP 自己公开的表目录里，**31 张表覆盖全部 264 对**，出问题的是索引——它按「这张表是为谁造的」建立，而不是按「这张表满足什么」。其余内容是证据、复现步骤，以及一份给 AI Agent 的同类作业手册。

想看清这些词背后的定义，再往下读。

### 岩浆 = 一个集合 + 一个二元运算

**岩浆**（magma）是一个集合 `G` 配一个二元运算 `◇ : G × G → G`，此外不作任何假设：不要求结合律、不要求单位元、不要求逆元、不要求交换律。**有限岩浆**就是承载集有限的岩浆，它可以被完整写成一张表：`n` 行 `n` 列，每个格子的值在 `0..n-1` 内，第 `(i, j)` 格就是 `i ◇ j`。

这张表就是全部对象。有了表，任何项都能求值。

### 等式理论 = 一堆恒等式

**恒等式**（也叫律）是用变量与 `◇` 搭出来的两个项之间的、带全称量词的等式。下面三个例子用的是 ETP 的记号（`x ◇ y` 表示运算）：

| 律编号 | 文本 | 含义 |
|---|---|---|
| `E1` | `x = x` | 在任何岩浆里都成立；4694 条里最弱的一条 |
| `E4` | `x = x ◇ y` | `x` 在右侧吸收一切；下面那张 2 元表满足它 |
| `E168` | `x = (y ◇ x) ◇ (x ◇ z)` | 本仓库倚重的那个「母律」：三条残差假设都是它的字面替换实例，见 [`01-method.md`](01-method.md) §3 |

一条律在某张岩浆里**成立**，指的是：对变量到元素的**任意**赋值，等式两边求值结果都相同。这是有限检查：承载集大小 `n`、变量 `k` 个，就只有 `n^k` 种赋值，每种赋值做一次项求值。所以「给定有限岩浆、给定律，它是否成立」是可判定的，而一个**反例**就是一个具体的赋值，使两边不相等。

### 一个能手算的小例子

取集合 `{0, 1}`，运算定义为 `a ◇ b = a`（左投影）。整张岩浆表就是：

| `◇` | 0 | 1 |
|---|---|---|
| **0** | 0 | 0 |
| **1** | 1 | 1 |

拿两条律在它上面验，`x, y, z` 都取自 `{0, 1}`：

| 律 | 左边 | 右边 | 判定 |
|---|---|---|---|
| `E4`：`x = x ◇ y` | `x` | `x ◇ y = x` | 全部 4 种赋值都成立 |
| `E5`：`x = y ◇ x` | `x` | `y ◇ x = y` | 在 `x=0, y=1` 时失败 |

所以这一张 2 元表就是「`E4` 蕴含 `E5`」的有限反例：它满足假设、反驳结论，见证赋值是 `x=0, y=1`。本仓库的全部机制就是这个——一张表、一个赋值、一次机械检验。264 对的区别只在规模：承载集最大 65 元，要试的律从几条变成 4694 条。

### ETP 在做什么

Equational Theories Project（ETP）协作研究这个只有一种运算的语言里的 **4694** 条恒等式，并对每一对 `(i, j)` 追问：

> `E_i` 是否蕴含 `E_j`？也就是说，是否每个满足 `E_i` 的岩浆也满足 `E_j`？

4694² 约 2200 万个有序对。项目的蕴含图逐对记录：该蕴含是已知成立（有证明）、已知不成立（有反例）、还是开放。不成立的那一类还要再区分：

- **有限反驳**：存在一张**有限**岩浆满足 `E_i` 而反驳 `E_j`；
- **只能无限反驳**：任何反驳都需要无限承载集。

后者是真正更强的陈述，因为表格形式的见证根本不存在。

### 本仓库补的是哪个洞

姊妹项目 `carlok/parsimagma` 维护一个构造语料：一堆岩浆，每个都带签名，记录它满足 4694 条律里的哪些。它发布了一个文件 `data/etp/finite_uncovered.txt`，列出同时满足下面两条的对：

- ETP 已证明**有限**反例存在，且
- 该语料里**没有任何**构造能分开这一对。

该文件上一个修订版列了 **264 对**（1062 侧 39 对，814 侧 225 对）。本仓库闭合的就是这些对。

### 为什么这其实是个索引问题

ETP 还公开发布了一个生成的反驳文件目录 `equational_theories/Generated/All4x4Tables/`。每个文件里是一张显式写出表的岩浆（`finOpTable "[[...]]"`），外加一条项目 `Facts` 格式的定理，记录对它证了什么。1171 个文件里有 946 个带可解析的表字面量。

这些表**本来就是公开的**。而它们其实分开了**全部 264 对**。残差清单没发现的原因在于：表的 `Facts` 行记录的是**为它输出了哪些事实**——通常就是它被造出来要分开的那一对——而不是这张表真正满足的律集。一张表经常满足某条假设律、同时反驳几十个从未被列出的目标。

所以修法不是更强的求解器，而是：

1. 对全部 4694 条律**算出**每张表的**满足集**（而不是从注解里读）；
2. **给每张表补上转置**——同一个承载集上左右乘互换的另一张岩浆；
3. 把查询**反过来问**：给定一对，哪些表能分开它。

### 仓库其余部分看什么

| 你想要 | 读 |
|---|---|
| 三个技巧的推导与算例 | [`01-method.md`](01-method.md) |
| 端到端流水线，逐阶段 | [`02-pipeline.md`](02-pipeline.md) |
| 在被抓住之前曾产出错误答案的 11 个坑 | [`03-pitfalls.md`](03-pitfalls.md) |
| **AI Agent 该怎样把这类活干成** | [`04-agent-playbook.md`](04-agent-playbook.md) |
| 复现命令与它们必须产出的数字 | [`05-reproduce.md`](05-reproduce.md) |
| 没证明什么、不许声称什么 | [`06-boundaries.md`](06-boundaries.md) |

### 读代码的前提

Python 3.8 以上，只用标准库。不需要线性代数、不需要 SAT 求解器、不需要图库。整个计算就是：解析一条律、在表上遍历所有赋值求值、把律编号集合取交。
