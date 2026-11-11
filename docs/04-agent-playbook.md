# 04 — Playbook for an AI agent doing this kind of work

[简体中文](#中文版) · **English**

This is the operating manual, not a story. Everything in it is a decision that
changed the outcome in this project, stated so that a different agent, on a
different model, can reuse it.

---

## English

### 1. Classify the task before you plan it

Most wasted agent effort in mathematics comes from misclassifying the task. Ask one
question first: **is the answer in the data, or does it have to be constructed?**

| Task shape | Tell | Right first move | Wrong first move |
|---|---|---|---|
| **Corpus alignment** (this project) | a list of "unsolved" items; a large corpus that might already contain the answers; the failure mode is "not found", not "impossible" | build an index over the corpus, then query it | search for new objects |
| Construction | no corpus could contain the answer; the statement is about objects nobody has exhibited | search, with symmetry breaking and a hard timeout budget | index what exists and declare it empty |
| Verification / audit | an existing claim plus a checker that might be wrong | write a second independent checker | trust the first checker |
| Formalisation | a mathematical statement plus a proof assistant | state it, then discharge with the project's own automation | prove it in prose |

This project was corpus alignment, and it was misclassified as construction for a
while. The cost was an SMT search over magmas up to `n = 8` for a pair whose witness
had been published for months. Two consequences for planning:

- **A negative result from a search is weak evidence.** "No witness under `n ≤ 8`"
  says nothing about `n = 24`, and nothing at all about whether a table already
  exists in a corpus you did not index.
- **A positive result from an index is strong evidence** and is much cheaper,
  because the object itself is the certificate and evaluating it is mechanical.

Ten-minute test for "is this corpus alignment?" — take 5 of the unresolved items and
check, by hand, whether any object in the largest corpus you have separates them. If
even one does, the problem is indexing, and you should stop searching.

### 2. Index by what an object satisfies, not by what it was made for

The single highest-value move in this project. Annotations, catalogs, and filenames
record **intent**, not **properties**. Intent is a lossy projection:

- a table built to separate `(a, b)` usually separates dozens of other pairs;
- its transpose separates a different set again;
- the annotation may list only what the author proved, not what is true.

So compute the property before you trust the label. In this case: 206 of 264 answers
were separated by a table whose own annotation never mentioned them. Any pipeline that
reads the annotation gets the same 264 misses, no matter how much compute it has.

**Operational form.** For each object, compute the full signature over the entire
universe (here: 4694 laws), store it as a bit vector, and answer queries by bit
operations. The expensive part is the signature; do it once, cache it, and never
evaluate the same (object, law) pair twice.

### 3. Orchestration: disjoint write scopes, one owner per directory

What worked, stated as rules:

1. **One owner per directory, written into the task description.** Two agents writing
   the same file is not a race you can win by being fast; it is a merge you cannot do.
2. **Shared inputs are read-only, always.** Inputs (`equational_theories`,
   `parsimagma`, graph artifacts) were never modified by anyone. One agent editing an
   input to make its line pass would have invalidated everyone else's numbers.
3. **Members cannot delegate further.** Measured: the runtime had `maxDepth = 1`, so a
   member that tried to spawn a sub-member was rejected. Plan for parallelism to come
   from the orchestrator fanning out sideways, not from nesting.
4. **Give each member a number to produce, not a task to attempt.** "Produce the
   per-pair witness table for the 104 pairs that `E168` bridges, as JSON with these
   fields" is checkable. "Work on the 104 pairs" is not.
5. **Have the orchestrator own the join.** Coverage arithmetic, deduplication across
   members' outputs, and the final count belong to one agent, because that is where
   double-counting happens.

### 4. Verification: two independent paths, and make them agree on the witness

The core asset of this project. Not the 264 answers — the fact that they were
checked in a way that could have failed.

**Minimum standard:** any conclusion rests on at least two independently written
implementations. "Independently" means different algorithms, ideally different
authors, and no shared helper that could encode the same mistake. Here:

| Path | Algorithm |
|---|---|
| 1 | stack machine over a compiled instruction list |
| 2 | naive recursion on the term tree |
| 3 | a separate library written for another purpose |

**The strong form, which is what actually caught the errors:** require the paths to
agree not just on *whether* the target is refuted, but on the **witnessing
assignment** — the same map from variables to carrier elements. Agreement on a boolean
is cheap and can be coincidental; agreement on a specific element-by-element
assignment is nearly impossible unless both implementations are right.

Three false results were caught by exactly this, and none would have been caught by a
single evaluator or by "the count looks right":

1. a Z3 encoding that reported `sat` for a constraint that was trivially true — the
   model it returned did not refute the target;
2. an enumeration that reported `unsat` after 3 models because the blocking clause was
   written as `n²` independent clauses instead of one;
3. a coverage figure that was off by 2 because `unknown` cells were counted as
   refutations.

**Budget it.** A second implementation of the evaluator is maybe 80 lines. A wrong
published claim is worse than a late one.

### 5. Land progress in slices; never hold results in a member's head

A member that runs out of context or crashes takes its unsaved findings with it. Rules
that came out of that:

- **Write to disk every ~20 minutes**, in a machine-readable form (JSON with a fixed
  schema, not prose).
- **Report after each slice**, briefly, with the file path and the count. A report
  that says "104/104 written to `reports/x.json`" lets the orchestrator continue even
  if the member dies immediately afterwards.
- **Schema first.** Decide the JSON fields before producing the first record, or you
  will rewrite 264 records to add a field.
- **Keep the intermediate artifacts that are cheap to regenerate out of the final
  package, but keep the summaries.** Here: the 935 KB reverse-index dump is
  regenerable in 63 s; the 264-record witness file with assignments is not
  regenerable without the pipeline, so it ships.

### 6. Order your techniques by cost, and take the cheap ones first

Measured cost ordering for this problem, cheapest first:

| Technique | Cost | Yield here |
|---|---|---|
| substitution bridging (pure term rewrite) | minutes | 104 pairs |
| reverse index over published tables | one 63 s sweep | 65 pairs, then 137 from one table |
| dual + transpose reads | free once the dual map is loaded | 24 pairs |
| symmetry breaking in a solver | hours of engineering | 0 pairs (not needed once indexed) |
| better solver / more time | hours to days | 0 pairs |

The general lesson: **before improving the search, ask whether the search is being
run over the right objects, with the right query direction.** A solver 300× faster
would have produced nothing here, because the answer was not in the search space —
it was in a corpus nobody had indexed.

### 7. Write reports that cannot be wrong

Four habits, all of which this repository enforces on itself:

1. **Separate measured from inferred.** Every number gets a provenance tag: measured
   by us (with the file that holds it), reported by someone else (with the citation),
   or inferred (with the inference). Example from this project: the 940 and 114
   coverage figures are ours and measured; the 790 is `parsimagma`'s own reported
   number, 411 + 379, and is labelled as such everywhere it appears.
2. **Every number names its file.** A number without a path is a rumour. If the
   number is a sum, show the addends and check the sum in a second place
   (`610 + 450 + 2 = 1062`, `940 + 790 − 676 = 1054`).
3. **Put the boundaries at the top, not in a footnote.** What was not run, what was
   not reviewed, what only holds up to a small parameter. Here: no full `lake build`,
   no CI, no maintainer review, and the structural negative result holds only to
   `k = 2`.
4. **Never let a nice number stand without its denominator.** "137 pairs" is
   meaningless without "of 264"; "31 tables" without "out of 946 parsed".

### 8. Pre-claim checklist

Run this before writing any sentence that sounds like a result.

- [ ] Is the claim measured, or is it inferred / reported by someone else? Do I say which?
- [ ] Does every number have a path to a file that contains it?
- [ ] Do the totals reconcile two different ways?
- [ ] Did at least two independent implementations agree — including on the witness?
- [ ] What did I *not* run? Is that in the visible text, not buried?
- [ ] Is any statement of the form "implies" actually an implication, or an equivalence?
- [ ] Am I quoting a search's "unsat" or "unknown" as if either were a proof?
- [ ] Would a reader who reruns my commands get my numbers? (Do the commands exist?)
- [ ] Have I removed every "should be", "presumably", "likely" from a claim sentence?

### 9. Anti-patterns that cost real time here

| Anti-pattern | What it cost |
|---|---|
| starting a solver before checking whether the corpus already answers it | an SMT/CNF workstream to `n = 8`, for a pair already closed by a published transpose |
| trusting `Facts` annotations as a complete index | the entire 264-pair residual, and a false "no solution" conclusion |
| one evaluator | three wrong intermediate results that passed |
| holding results until the end of a member's run | near-total loss of a slice's progress on a context exhaustion |
| reporting a number without its denominator or its file | two contradictory coverage figures in circulation at once (450 vs 452) |
| describing 31 individually compiled files as "the project builds" | a claim that would not survive one maintainer question |

---

## 中文版

这是一份操作手册，不是复盘故事。里面每一条都是在本项目里改变过结果的决定，写法上刻意做成「换一个 Agent、换一个模型也能直接用」。

### 1. 先给任务定性，再排计划

数学任务里最常见的浪费，是定性错了。先问一句：**答案已经在数据里，还是必须新构造出来？**

| 任务形态 | 识别特征 | 正确的第一步 | 错误的第一步 |
|---|---|---|---|
| **语料对齐型**（本项目） | 有一张「未解决」清单；有大型语料，可能早就含答案；失败模式是「没找到」而不是「不存在」 | 给语料建索引，再查询 | 去搜索新对象 |
| 构造型 | 任何现有语料都不可能含答案；命题说的是没人展示过的对象 | 搜索，配对称性破除与硬性超时预算 | 把现有东西索引一遍就宣布没有 |
| 验证 / 审计型 | 已有主张 + 一个可能写错的检查器 | 另写一个独立检查器 | 相信第一个检查器 |
| 形式化型 | 数学陈述 + 证明助手 | 先陈述，再用项目自带的自动化关闭目标 | 用自然语言把证明写完 |

本项目属于语料对齐，但一度被当成构造型在做。代价是：有一对的见证早已公开发表数月，而我们在 `n ≤ 8` 的岩浆空间里跑 SMT 搜索。两条计划层面的结论：

- **搜索给出的否定结论是弱证据。** 「`n ≤ 8` 内没有见证」既不说明 `n = 24` 时没有，更完全不说明你还没索引的那份语料里有没有。
- **索引给出的肯定结论是强证据**，而且便宜得多——对象本身就是证书，求值是机械的。

十分钟判定法：取 5 条未解决项，手工检查你手上**最大**的那份语料里有没有对象能分开它们。只要有一条能，问题就是索引问题，立刻停止搜索。

### 2. 按「对象满足什么」建索引，而不是按「它是为谁造的」

这是全项目性价比最高的一步。注解、目录、文件名记录的是**意图**，不是**性质**。意图是有损投影：

- 一张为分开 `(a, b)` 造出来的表，通常还分开几十对别的；
- 它的转置又分开另一批；
- 注解往往只列作者证过的部分，而不是所有为真的部分。

所以先算性质，再决定信不信标签。本案例里：264 个答案中有 **206 个**是由「注解从未提及该对」的表分开的。任何读注解的流水线都会得到同样的 264 个漏，算力再多也一样。

**操作形态**：对每个对象，在整个论域上算完整签名（这里是 4694 条律），存成位向量，查询全用位运算。贵的是签名；算一次、缓存、同一个（对象，律）对绝不求值两次。

### 3. 编排：写区互不相交，一个目录一个主人

实测有效的规则：

1. **一个目录一个主人，写进任务描述里。** 两个 Agent 写同一个文件不是你跑得快就能赢的竞争，而是一次你无法完成的合并。
2. **共享输入永远只读。** 输入（`equational_theories`、`parsimagma`、两份图产物）谁都没改。只要有人为了让自己的断言成立去改输入，其他人的数字就全部失效。
3. **成员不能再往下派。** 实测运行时是 `maxDepth = 1`，成员尝试再开子成员会被拒绝。所以并行要靠主控横向铺开，而不是靠嵌套。
4. **给成员一个「必须产出的数字」，而不是一个「试着做做」的任务。** 「产出 `E168` 桥接的那 104 对的逐对见证表，JSON，字段如下」是可验收的；「去处理那 104 对」不是。
5. **合并归主控。** 覆盖率算术、成员产出的去重、最终计数，必须由同一个 Agent 负责——重复计数就发生在这一步。

### 4. 验证：两条独立路径，而且要在见证上一致

本项目的核心资产不是那 264 个答案，而是「它们被一种**本来可能失败**的方式检查过」。

**最低标准**：任何结论至少压在两份独立实现上。「独立」指算法不同、最好作者不同、不共用可能编码同一个错误的辅助函数。本案例是：

| 路径 | 算法 |
|---|---|
| 1 | 编译成指令列表的栈机 |
| 2 | 在项树上朴素递归 |
| 3 | 为另一个目的单独写的判定库 |

**强形式，也是真正抓住错误的那个**：要求几条路径不只对「目标是否被反驳」一致，还要对**见证赋值**一致——同一个从变量到承载集元素的映射。布尔值一致很便宜、可能巧合；逐元素赋值一致，除非两边都对，否则几乎不可能。

三个假结果正是这样被抓出来的，而且没有任何一个会被「单一求值器」或「数字看起来对」抓出来：

1. 一个 Z3 编码对恒真约束报了 `sat`，它返回的模型根本没反驳目标；
2. 一个枚举在第 3 个模型后就报 `unsat`，因为「阻断一张表」写成了 `n²` 条独立子句；
3. 一个覆盖率数字差了 2，因为把 `unknown` 当成反驳计了。

**给它留预算**：写第二个求值器大约 80 行。一条错的公开主张，比晚交一天糟得多。

### 5. 分片落盘，绝不把结果留在成员的脑子里

成员上下文耗尽或崩掉，会把它没落盘的发现一起带走。由此得到的规则：

- **每 20 分钟左右落一次盘**，写成机器可读形式（固定 schema 的 JSON，不是散文）。
- **每片做完就报一次**，短，带文件路径和计数。「104/104 写入 `reports/x.json`」这样的报告，让主控在成员随后立刻死掉的情况下也能继续。
- **先定 schema。** 在产出第一条记录之前就把字段定死，否则要为了加一个字段重写 264 条。
- **便宜可再生的中间产物不进最终包，但摘要要留。** 本案例：935 KB 的反向索引转储 63 秒可重算，不进包；带赋值的 264 条见证记录没有流水线就重现不出来，进包。

### 6. 按成本给技巧排序，先吃便宜的

本问题的实测成本排序，从便宜到贵：

| 技巧 | 成本 | 本案例产出 |
|---|---|---|
| 替换桥接（纯项改写） | 分钟级 | 104 对 |
| 对已公开表建反向索引 | 一次 63 秒扫描 | 65 对，随后单表再出 137 |
| 对偶 + 转置读法 | 对偶表加载后免费 | 24 对 |
| 求解器里的对称性破除 | 数小时工程量 | 0 对（索引后不再需要） |
| 换更强求解器 / 加更多时间 | 数小时到数天 | 0 对 |

一般化的教训：**在改进搜索之前，先问搜索是不是跑在正确的对象上、问的方向对不对。** 快 300 倍的求解器在这里也一无所获，因为答案不在搜索空间里——它在一份没人索引过的语料里。

### 7. 写「不可能写错」的报告

四条习惯，本仓库对自己强制执行：

1. **把实测与推断分开。** 每个数字带来源标签：我们实测（附承载它的文件）、他人自报（附引文）、推断（附推理）。本案例的例子：940 与 114 是我们的实测；**790 是 `parsimagma` 自报的 411 + 379**，凡出现处都如此标注。
2. **每个数字都点名文件。** 没有路径的数字是传闻。若是求和，列出加数并在另一处再算一遍（`610 + 450 + 2 = 1062`、`940 + 790 − 676 = 1054`）。
3. **边界写在开头，不塞脚注。** 没跑什么、没谁审过、只在小参数上成立的结论。本案例：没跑全量 `lake build`、没跑 CI、没经维护者审查，结构性否定只到 `k = 2`。
4. **不要给出没有分母的好数字。** 「137 对」缺了「共 264 对」就没有意义；「31 张表」缺了「从 946 张里解析出来」也没有。

### 8. 下结论前的检查表

在写下任何一句听起来像结论的话之前跑一遍。

- [ ] 这是实测，还是推断／他人自报？我说清楚了吗？
- [ ] 每个数字都能指出一个装着它的文件吗？
- [ ] 总数能用两种方式对上吗？
- [ ] 至少两份独立实现一致吗——包括在见证上？
- [ ] 我**没**跑什么？它在显眼处，还是被埋在角落？
- [ ] 我写「蕴含」的地方，真的是蕴含而不是等价吗？
- [ ] 我有没有把搜索的 `unsat` 或 `unknown` 当成证明？
- [ ] 别人照我给的命令重跑，能拿到我的数字吗（命令真的存在吗）？
- [ ] 结论句里的「应该是」「大概」「可能」都删干净了吗？

### 9. 真正吃掉过时间的反模式

| 反模式 | 代价 |
|---|---|
| 没先查语料就先上求解器 | 一条跑到 `n = 8` 的 SMT/CNF 产线，而那一对早被一张已公开表的转置闭合 |
| 把 `Facts` 注解当完备索引 | 整份 264 对残差，外加一个错误的「无解」结论 |
| 只用一个求值器 | 三个中间假结果全部通过 |
| 结果攒到成员运行结束再交 | 一次上下文耗尽几乎丢掉整片进度 |
| 报数字不带分母、不带文件 | 两个互相矛盾的覆盖率数字同时在外流通（450 对 452） |
| 把「31 个文件各自编译通过」说成「项目能构建」 | 一个经不起维护者一句反问的主张 |
