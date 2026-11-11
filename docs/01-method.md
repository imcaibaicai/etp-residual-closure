# 01 — The three techniques

> **中文摘要**
> 一、按「满足集」建反向索引：表分开一对当且仅当它满足假设、反驳目标，这把「哪张表能分开它」变成一次集合查询而不是一次搜索。
> 二、对偶加转置：转置表的签名只是原表签名的位集置换，`sig(Mᵀ)[i] = sig(M)[dual(i)]`，用 2305 组对偶映射做一次置换即可，不必重扫 4694 条律。
> 三、替换桥接：一条律的纯项替换实例自动被它蕴含，`E168` 的四个替换实例一次覆盖 104 对——这是分钟级的操作，而搜索是小时级。

---

## 1. Index by satisfied set, not by generation pair

### The definition

For a finite magma `M` with carrier size `n`, and the 4694 laws of ETP, define the
**signature** of `M`:

```
sig(M)[i] = 1   if M ⊨ E_i
            0   otherwise                    (i = 1 .. 4694)
```

`M` is a *counterexample* to the implication `E_i ⟹ E_j` exactly when

```
sig(M)[i] = 1   and   sig(M)[j] = 0
```

because that is the definition: `M` satisfies the hypothesis and refutes the
conclusion. Nothing else about `M` matters — not what it was built for, not what
its `Facts` annotation says.

### The reverse direction is what was missing

`parsimagma` already builds a matrix `separates[pair][instance]` by walking
instances × targets. The query that was never asked is the transpose of that:

> given a pair, which instances discharge it?

That is the *same* data, read the other way. It is not a second index and not a
new data structure. The 264 pairs stayed invisible for two independent reasons,
and this is the first one: the pair list was consumed one pair at a time against a
corpus that did not contain the tables that discharge them.

### Cost

Computing a full 4694-law signature means 4694 laws × `n^k` assignments, which is
the only expensive step in the whole pipeline. Measured on this corpus:

| Mode | Work | Time |
|---|---|---|
| `--laws targets` | only the 131 laws named by the 264 pairs | 2.3 s |
| `--laws all` | full signatures over all 4694 laws, 946 tables + transposes | 63 s |

The signature is a bit vector, so all set operations afterwards (separation,
coverage, intersection, union) are bit operations on 4694 bits.

### Worked example

`Refutation899` (9 elements) has `sig[168] = 1` and `sig[j] = 0` for 137 distinct
targets `j` among the 264. So that one table closes 137 pairs. The next two,
`Refutation924` and `Refutation923` (both 21 elements), close 38 and 35 more. The
top three tables close 210 of the 264; 31 tables close all of them.

## 2. Dual plus transpose

### The transpose is a different magma

Given `M = (G, ◇)`, its **transpose** is `Mᵀ = (G, ◇ᵀ)` with

```
a ◇ᵀ b  :=  b ◇ a
```

Same carrier, different magma unless `M` happens to be commutative. As a table,
`Mᵀ` is `M` reflected across the main diagonal. It is the second thing the old
pipeline discarded: a table indexed only as printed loses every pair that only its
transpose separates.

### Why it is a bit permutation, not a re-sweep

Define the **dual** of a term recursively:

```
dual(x)     = x
dual(s ◇ t) = dual(t) ◇ dual(s)
```

and the dual of a law `s = t` is `dual(s) = dual(t)`.

**Lemma.** For every magma `M`, every law `E_i` and every assignment `v`:

```
E_i holds in Mᵀ  ⟺  dual(E_i) holds in M
```

*Proof sketch.* Evaluate `dual(t)` in `M` at `v`; it equals the evaluation of `t`
in `Mᵀ` at `v`, by induction on the term: the operation of `Mᵀ` is the flipped
operation of `M`, so flipping the term and flipping the operation cancel.
Therefore `Mᵀ ⊨ E_i ⟺ M ⊨ dual(E_i)`. ∎

Writing `d(i)` for the index of the dual law, the lemma reads:

```
sig(Mᵀ)[i] = sig(M)[d(i)]
```

So the transpose's entire signature is one permutation of the original's bits. One
`d` lookup table per corpus, then no law is ever evaluated twice.

### The dual map

`parsimagma` ships `data/etp/duals.json`: 2305 explicit dual pairs, covering 4610
of the 4694 laws; the remaining 84 laws are self-dual (`d(i) = i`). Building `d` is
reading that file plus filling in the fixed points.

### The cost, measured

| Operation | Cost |
|---|---|
| adding transposes to the corpus | one extra table per table, 946 → 1892 |
| extra pairs recovered on the residual | **24** of 264 |
| extra pairs recovered on the whole 1054 | 916 → 940 |
| extra CPU | about 30 s over the whole corpus |

### Control used

The identity `sig(Mᵀ) = sig(M) ∘ d` was checked against a direct sweep on two
tables: `Refutation899` (9 elements) and `Refutation934` (24). The permuted
signature equalled the swept signature of the transpose, set for set. The identity
itself follows from the lemma above; the two sweeps are a control on the
implementation, not a proof of the identity.

### Worked example: the last pair

`E2712 ⟹ E2452` had no non-transposed witness anywhere in the 946 tables, and no
witness under the dual-plus-direct check either, which is why an earlier pass
called the residual "stuck". It closes like this:

| Step | Value |
|---|---|
| dual pair of `(2712, 2452)` | `(854, 1055)` |
| that pair is separated by | `Refutation934`, 24 elements |
| so take the transpose of `Refutation934` | sha256 `424a7fc0fd815bee…f381` |
| the transpose satisfies `E2712` | yes (`x = ((y◇x)◇(y◇z))◇x`) |
| the transpose refutes `E2452` | yes, at `{x:19, y:2, z:5}` |

## 3. Substitution bridging

### The rule

If `σ` maps each variable of a law `L` to an arbitrary term, then the instance
`σ(L)` is a **consequence** of `L`: every magma satisfying `L` satisfies `σ(L)`,
because any assignment that makes `σ(s) = σ(t)` fail would make `s = t` fail at the
assignment obtained by evaluating the substituted terms.

So: find a law that is already witnessed, and look for targets that are its
substitution instances. No search over magmas is needed — this is term rewriting.

### What it bought

`E168 = x = (y ◇ x) ◇ (x ◇ z)` turned out to be the mother law of four of the
residual hypotheses:

| Substitution | Instance |
|---|---|
| `z → z ◇ z` | `E1486` |
| `z → z ◇ w` | `E1487` |
| `y → y ◇ z`, `z → w` | `E2164` |
| `y → y ◇ y` | `E2126` |

Any magma satisfying `E168` automatically satisfies all four, so a single witness
for `E168` covers their residual pairs too. ETP had already published a 9-element
table satisfying `E168` — `Refutation899`, the same table that closes 137 pairs
directly. Two more tables were needed for the remaining hypotheses in this family:
`Refutation929` (21 elements, satisfies `E1486`) and `Refutation923` (21 elements,
satisfies `E2126`).

Together the bridging accounted for **104** of the 264 pairs (`E168` as mother law,
four targets), found in minutes.

### Equivalence, not implication — and why it matters for the count

For three of these laws the ETP implication graph records the implication in **both**
directions: `E168 ⟺ E1487 ⟺ E2164`. The substitution above gives one direction;
the reverse direction is in the graph.

Consequence for how the residual should be read: those 47 pairs are, mathematically,
24 distinct problems, 23 of which were asked twice. The count 264 overstates the
number of independent questions.

The accompanying analysis characterises these three laws as equivalent to a
single condition: the operation is surjective, and for every `x` the set of values
`Im(R_x) ◇ Im(L_x)` is exactly `{x}`. Treat that characterisation as an
explanation of the shape of the witness, not as a machine-checked theorem — nobody
formalised it in this work.

### Why bridging beats searching

Finding a mother law is: parse 4694 laws as terms, try a small set of substitutions
on each, check which laws come out. That is minutes of Python.

Searching for the same counterexample directly is: for each carrier size `n`, decide
satisfiability of "satisfies `E_i` and refutes `E_j`" over all `n`-element magmas.
That is hours to days, and for the pairs in this residual it is *known impossible*
below certain sizes because the project had already proved unsat by exhaustive
search there.

The measured gap is not a constant factor; it is the difference between a problem
that finishes during lunch and one that does not finish.

## 4. Why we did not search: the encoding detour, in one table

Before the indexing result, an attempt was made to find witnesses by SMT. The
encoding mattered far more than the solver:

| Encoding | Instance | Result |
|---|---|---|
| Z3 array theory: `K` + chained `Store` + `Select` | `n = 7` | 600 s, `unknown` |
| Z3 one-hot boolean | `n = 7` | **1.8 s** |
| one-hot boolean + canonical "first occurrence order" on values | `n = 7` | 120 s `unknown` → **3.5 s `unsat`** |
| CNF + cadical | `n = 8` | worse than Z3 with symmetry breaking |

Two of the three orders-of-magnitude gains came from symmetry breaking, not from a
better solver. That is the transferable lesson; the exact numbers are in
[`03-pitfalls.md`](03-pitfalls.md) under the encoding entries.

None of this was needed once the tables were indexed. It is recorded because the
next person will otherwise redo it.
