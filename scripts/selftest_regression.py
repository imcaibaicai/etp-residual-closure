# -*- coding: utf-8 -*-
"""用 ETP 自带数据给 etp_magma_lib 做回归自检（真值对照）。

三项检查
========
A. ``smallest_magma_examples.txt``（3198 条）
   每行 ``<律编号> <乘法表 JSON>``。这张表是该律的**最小阶满足者**，判定器
   必须对每一条都返回「满足」。返回「反驳」即库的 bug。

B. ``refutations{2x2,3x3,4x4}.txt``（2 阶 10 张、3 阶 299 张、4 阶 515 张表）
   每组两行 ``Table [[...]]`` 与 ``Proves [律编号, ...]``。经核对，``Proves``
   列表**恰好等于**该表在全部 4694 条律里满足的那些（既不多也不少），所以这是一
   个双向检验：不该漏判满足（列表里有、我说没有 = 假阴性），也不该误判满足
   （列表里没有、我说有 = 假阳性）。这是对「满足/反驳」语义最严格的真值对照。

C. 最小性反查（``smallest_magma.txt``，格式 ``<律编号> <最小阶数>``）
   最小阶为 2（3136 条）：断言示例表的阶数确实是 2。
   最小阶为 3（32 条）：穷举全部 16 张 2 阶表，断言无一满足。
   最小阶为 4（14 条）：穷举全部 19683 张 3 阶表，断言无一满足。
   最小阶 ≥5（16 条）：需穷举 4 阶（4^16），不做，只记录跳过条数。

产出
====
``reports/magma-lib-regression.json``：逐项计数与失败样例（最多 20 条）。

用法
====
    python3 scripts/selftest_regression.py [--fast]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))   # <repo>/scripts
sys.path.insert(0, HERE)

from etp_magma_lib import Magma, all_magmas, get_law, satisfies  # noqa: E402

ETP_HOME = os.environ.get("ETP_HOME")
if not ETP_HOME:
    raise SystemExit("set ETP_HOME to the directory holding the parsimagma checkout")
DATA = os.path.join(ETP_HOME, "parsimagma", "data", "etp")
OUT_DIR = os.path.join(os.path.dirname(HERE), "reports")
N_LAWS = 4694


def read_examples():
    """读 smallest_magma_examples.txt -> {律编号: Magma}。"""
    path = os.path.join(DATA, "smallest_magma_examples.txt")
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                eid_text, table_text = line.split(" ", 1)
                out[int(eid_text)] = Magma.from_json(table_text)
    return out


def check_a(examples):
    """A. 每个示例表都应当满足自己那条律。"""
    total = ok = 0
    failures = []
    for eid, magma in sorted(examples.items()):
        law = get_law(eid)
        total += 1
        if satisfies(magma, law):
            ok += 1
        elif len(failures) < 20:
            failures.append({"id": eid, "n": magma.n, "table": magma.table})
    return {
        "check": "A 示例表应当满足对应律",
        "file": os.path.join(DATA, "smallest_magma_examples.txt"),
        "unit": "表×律",
        "total": total,
        "agree": ok,
        "disagree": total - ok,
        "failures": failures,
    }


def iter_refutation_tables(name):
    """逐张产出 (表, Proves 列表) —— 数据文件是两行一组。"""
    path = os.path.join(DATA, name)
    pending = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line.startswith("Table"):
                pending = Magma.from_json(line[len("Table"):].strip())
            else:
                assert line.startswith("Proves"), line[:40]
                yield pending, set(json.loads(line[len("Proves"):].strip()))
                pending = None


def check_b(name, limit=None):
    """B. 表满足的律集合必须与 Proves 列表完全相等（双向）。"""
    tables = 0
    pairs = 0
    agree = 0
    n_missing = 0
    n_extra = 0
    missing = []   # 列表里有、判定器说没有 -> 假阴性
    extra = []     # 列表里没有、判定器说有 -> 假阳性
    for magma, listed in iter_refutation_tables(name):
        tables += 1
        computed = {i for i in range(1, N_LAWS + 1) if satisfies(magma, get_law(i))}
        pairs += len(listed)
        agree += len(computed & listed)
        gone = sorted(listed - computed)
        added = sorted(computed - listed)
        n_missing += len(gone)
        n_extra += len(added)
        for eid in gone[:5]:
            if len(missing) < 20:
                missing.append({"n": magma.n, "law": eid, "kind": "假阴性"})
        for eid in added[:5]:
            if len(extra) < 20:
                extra.append({"n": magma.n, "law": eid, "kind": "假阳性"})
        if limit and tables >= limit:
            break
    return {
        "check": f"B {name}: 满足集 == Proves 列表",
        "file": os.path.join(DATA, name),
        "unit": "表×律",
        "tables": tables,
        "pairs": pairs,
        "law_checks": tables * N_LAWS,
        "agree": agree,
        "disagree": n_missing + n_extra,
        "failures": (missing + extra)[:20],
    }


def check_c(examples, orders):
    """C. 最小阶数与穷举结果一致。"""
    order2 = list(all_magmas(2))
    order3 = None
    checked = agree = skipped = 0
    failures = []
    for eid, claimed in sorted(orders.items()):
        law = get_law(eid)
        if claimed == 2:
            checked += 1
            if examples[eid].n == 2 and satisfies(examples[eid], law):
                agree += 1
            elif len(failures) < 20:
                failures.append({"id": eid, "claimed": 2, "example_n": examples[eid].n})
        elif claimed == 3:
            checked += 1
            if not any(satisfies(m, law) for m in order2):
                agree += 1
            elif len(failures) < 20:
                failures.append({"id": eid, "claimed": 3, "note": "存在 2 阶满足者"})
        elif claimed == 4:
            checked += 1
            if order3 is None:
                order3 = list(all_magmas(3))
            if not any(satisfies(m, law) for m in order3):
                agree += 1
            elif len(failures) < 20:
                failures.append({"id": eid, "claimed": 4, "note": "存在 3 阶满足者"})
        else:
            skipped += 1
    return {
        "check": "C 最小阶数与穷举一致（≥5 阶需穷举 4 阶，跳过）",
        "file": os.path.join(DATA, "smallest_magma.txt"),
        "unit": "律",
        "checked": checked,
        "skipped_needs_order4_bruteforce": skipped,
        "agree": agree,
        "disagree": checked - agree,
        "failures": failures,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="每类只跑前 40 张表")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    t0 = time.time()
    results = []

    examples = read_examples()
    r = check_a(examples)
    results.append(r)
    print(f"[A] {r['total']} 表，一致 {r['agree']}，不一致 {r['disagree']}")

    limit = 40 if args.fast else None
    for name in ("refutations2x2.txt", "refutations3x3.txt", "refutations4x4.txt"):
        r = check_b(name, limit=limit)
        results.append(r)
        print(f"[B] {name}: {r['tables']} 表 / {r['pairs']} 表×律，"
              f"一致 {r['agree']}，不一致 {r['disagree']}")

    orders = {}
    with open(os.path.join(DATA, "smallest_magma.txt"), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                a, b = line.split()
                orders[int(a)] = int(b)
    r = check_c(examples, orders)
    results.append(r)
    print(f"[C] 检 {r['checked']} 条，一致 {r['agree']}，不一致 {r['disagree']}，"
          f"跳过 {r['skipped_needs_order4_bruteforce']}")

    elapsed = time.time() - t0
    # Paths in the report are placeholders: this file is published, and a regenerated
    # report must not reintroduce the machine layout it was produced on.
    for rec in results:
        if isinstance(rec.get("file"), str):
            rec["file"] = rec["file"].replace(DATA, "$ETP_HOME/parsimagma/data/etp").replace("\\", "/")
    payload = {
        "generated_by": "scripts/selftest_regression.py",
        "elapsed_seconds": round(elapsed, 1),
        "checks": results,
        "all_agree": all(r["disagree"] == 0 for r in results),
        "total_judgements": sum(r.get("law_checks", r.get("total", r.get("checked", 0)))
                                for r in results),
    }
    out = os.path.join(OUT_DIR, "magma-lib-regression.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"\n总判定 {sum(r.get('law_checks', r.get('total', r.get('checked', 0))) for r in results)} 次，"
          f"用时 {elapsed:.1f}s；全部一致 = {payload['all_agree']}  -> {out}")


if __name__ == "__main__":
    main()
