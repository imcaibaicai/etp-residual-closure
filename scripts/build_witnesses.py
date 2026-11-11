# -*- coding: utf-8 -*-
"""Build ``submission/data/witnesses_264.json`` from the reverse-index run.

三个求值路径必须一致，任何一条不同意就中止：

1. ``reverse_index.FastLaw``（栈机，reverse_index.py 自带）
2. ``reverse_index.refutes_naive``（朴素递归，reverse_index.py 自带）
3. ``etp_magma_lib``（工作区独立实现的第三份判定库）

同时给每对标注「它最早是被哪条线索找到的」（漏斗来源），与「本次用什么表
闭合」分开记录：前者答复「为什么以前漏」，后者是交付物。
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))   # <repo>/scripts
WS = os.path.dirname(HERE)                          # <repo>
sys.path.insert(0, HERE)

import reverse_index as R  # noqa: E402
from etp_magma_lib import Magma as LibMagma, counterexample, get_law, refutes, satisfies  # noqa: E402

ETP_HOME = os.environ.get("ETP_HOME")
if not ETP_HOME:
    raise SystemExit(
        "set ETP_HOME to the directory that holds the equational_theories and "
        "parsimagma checkouts")

DATA = os.path.join(WS, "data")
REPORTS = os.path.join(WS, "reports")
SUBREP = REPORTS
IDX = os.path.join(SUBREP, "reverse_index_all", "reverse_index.json")
EQUATIONS = os.path.join(ETP_HOME, "parsimagma", "data", "etp", "equations.txt")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def truthy_pairs(records, key_path):
    out = set()
    for rec in records:
        try:
            cur = rec
            for k in key_path:
                cur = cur[k]
        except (KeyError, TypeError):
            continue
        out.add((int(cur[0]), int(cur[1])))
    return out


def build_provenance():
    """每对 → 它在本轮之前是被哪条线索命中的（漏斗来源）。

    这不是交付物的分类，是成因分析：说明「以前为什么漏」。来源文件见 docstring。
    """
    prov = {}

    # 83 对：ETP full_entries 里有现成 facts 索引（58 直接 + 25 经对偶）
    cls = load_json(os.path.join(REPORTS, "20261110-uncovered-264-classification.json"))
    for rec in cls["records"]:
        if rec["status"] in ("witness", "witness_via_dual"):
            prov[(rec["from"], rec["to"])] = {
                "leads": "published_facts_index",
                "via_dual_lead": rec["status"] == "witness_via_dual",
            }

    # 104 对：替换桥接（E168 是母律，纯项替换）
    e1486 = load_json(os.path.join(REPORTS, "e1486", "counterexamples_final.json"))
    for key in e1486["witnesses"]:
        a, b = key.split("_")
        prov.setdefault((int(a), int(b)), {"leads": "substitution_bridge"})

    # 65 对：公开表扫描（9 元表为主）
    scan = load_json(os.path.join(REPORTS, "20261110-残差收敛-扫表结果.json"))
    for hit in scan["hits"]:
        prov.setdefault((hit["from"], hit["to"]), {"leads": "published_table_sweep"})

    # 4 对：carlok 自己的 §5.6 扩张参数
    for rec in scan.get("closed_by_extension_but_no_table", []):
        prov.setdefault((rec["from"], rec["to"]), {"leads": "ext_parameters"})

    # 7 对：946 张表全扫
    last8 = load_json(os.path.join(REPORTS, "20261110_最后8对-命中表.json")) \
        if os.path.exists(os.path.join(REPORTS, "20261110_最后8对-命中表.json")) \
        else load_json(os.path.join(REPORTS, "20261110-最后8对-命中表.json"))
    for key, rec in last8["pairs"].items():
        a, b = key.split("_")
        if rec.get("closed"):
            prov.setdefault((int(a), int(b)), {"leads": "corpus_full_sweep"})

    # 1 对：对偶 + 转置
    prov.setdefault((2712, 2452), {"leads": "dual_transpose"})
    return prov


def main():
    idx = load_json(IDX)
    laws = R.load_equations(EQUATIONS)
    prov = build_provenance()

    pairs_file = os.path.join(ETP_HOME, "parsimagma", "data", "etp", "finite_uncovered.txt")
    label_of = {}
    for label, a, b in R.load_targets(pairs_file):
        label_of[(a, b)] = label

    records = []
    tables = {}
    conflicts = []
    funnel_counts = {}

    magmas, _ = R.load_corpus(os.path.join(ETP_HOME, "etp-refutations-all"))
    by_name = {m.name: m for m in magmas}
    name_sha = {m["name"]: m["sha256"] for m in idx["tables"]}
    all_fast = {i: R.FastLaw(R.Law(laws[i - 1])) for i in range(1, len(laws) + 1)}

    for key, rec in idx["witnesses"].items():
        a, b = rec["from"], rec["to"]
        cands = rec["tables"]
        # 选见证：优先非转置，其次载体小，再按名字
        chosen = sorted(cands, key=lambda c: (c["is_transpose"], c["carrier"], c["name"]))[0]

        fast = all_fast[a]
        target = all_fast[b]
        table_sha = name_sha[chosen["name"]]
        base = by_name[chosen["name"].replace("#T", "")]
        magma = base.transposed() if chosen["is_transpose"] else base
        table = magma.table
        if magma.sha256() != table_sha:
            conflicts.append({"pair": [a, b], "reason": "sha256 mismatch", "name": chosen["name"]})

        # 路径 1：栈机
        sat_fast = magma.satisfies(fast)
        cex_fast = target.counterexample(magma.flat, magma.n)
        # 路径 2：朴素递归
        cex_naive = R.refutes_naive(table, target.law)
        sat_naive = R.refutes_naive(table, fast.law) is None
        # 路径 3：第三方库
        lib = LibMagma(table)
        lib_law_b = get_law(b)
        sat_lib = satisfies(lib, get_law(a))
        cex_lib = None
        raw = counterexample(lib, lib_law_b) if refutes(lib, lib_law_b) else None
        if raw is not None:
            # 库返回的是按 law.variables 排序的元组；本脚本统一用 dict
            cex_lib = dict(zip(lib_law_b.variables, raw))

        agree = (
            sat_fast == sat_naive == sat_lib is True
            and cex_fast is not None
            and cex_naive is not None
            and cex_lib is not None
            and cex_fast == cex_naive == cex_lib
        )
        if not agree:
            conflicts.append({
                "pair": [a, b], "name": chosen["name"],
                "sat": [sat_fast, sat_naive, sat_lib],
                "cex": [cex_fast, cex_naive, cex_lib],
            })

        lead = prov.get((a, b), {"leads": "unattributed"})
        funnel_counts[lead["leads"]] = funnel_counts.get(lead["leads"], 0) + 1

        tables[table_sha] = {
            "sha256": table_sha,
            "carrier": magma.n,
            "source": chosen["name"],
            "is_transpose": chosen["is_transpose"],
            "table": table,
        }

        records.append({
            "from": a,
            "to": b,
            "set": label_of.get((a, b), ""),
            "from_law": laws[a - 1],
            "to_law": laws[b - 1],
            "leads": lead["leads"],
            "leads_via_dual": lead.get("via_dual_lead", False),
            "witness": {
                "name": chosen["name"],
                "carrier": magma.n,
                "is_transpose": chosen["is_transpose"],
                "sha256": table_sha,
            },
            "refutation_assignment": cex_lib,
            "alternative_witnesses": len(cands),
            "evaluators": ["stack_machine", "naive_recursive", "etp_magma_lib"],
            "agreement": agree,
        })

    records.sort(key=lambda r: (r["set"], r["from"], r["to"]))
    payload = {
        "generator": "scripts/build_witnesses.py",
        "sources": {
            "residual_list": "$ETP_HOME/parsimagma/data/etp/finite_uncovered.txt",
            "reverse_index": os.path.relpath(IDX, WS),
            "laws": EQUATIONS,
            "corpus": r"$ETP_HOME/etp-refutations-all",
        },
        "method": ("每对取一个见证表：优先非转置、其次载体最小。三条独立求值路径"
                   "（栈机、朴素递归、etp_magma_lib）必须同时同意「满足假设、反驳目标、"
                   "且给出同一个反例赋值」，任一条不同意即记入 conflicts 并中止。"),
        "leads_histogram": dict(sorted(funnel_counts.items(), key=lambda kv: -kv[1])),
        "totals": {
            "pairs": len(records),
            "agreement_true": sum(1 for r in records if r["agreement"]),
            "transpose_witnesses": sum(1 for r in records if r["witness"]["is_transpose"]),
            "distinct_tables": len(tables),
            "conflicts": len(conflicts),
        },
        "records": records,
    }
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "witnesses_264.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(DATA, "tables_referenced.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"note": "见证表的完整乘法表，按 sha256 索引；witnesses_264.json 里的 "
                           "witness.sha256 指向这里。sha256 是对 "
                           "json.dumps(table, separators=(',',':')) 取的。",
                   "tables": tables}, fh, ensure_ascii=False, indent=1)

    # TSV：与他 data/etp/refutations*.txt 同格式，一张表一条记录
    written = set()
    with open(os.path.join(DATA, "witnesses_264.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Witness tables for the 264 pairs listed by data/etp/finite_uncovered.txt.\n")
        fh.write("# Format matches data/etp/refutations*.txt: 'Table [[...]]' then 'Proves [...]'.\n")
        fh.write("# Proves is the complete set of laws the table satisfies (all 4694 laws checked).\n")
        fh.write("# A table's refuted set is the complement. Blank line separates records.\n\n")
        for rec in records:
            sha = rec["witness"]["sha256"]
            if sha in written:
                continue
            written.add(sha)
            tab = tables[sha]["table"]
            fh.write(f"Table {json.dumps(tab)}\n")
            mag = R.Magma("x", tab)
            sat = sorted(i for i in all_fast if mag.satisfies(all_fast[i]))
            fh.write(f"Proves {json.dumps(sat)}\n\n")

    report = {
        "totals": payload["totals"],
        "leads_histogram": payload["leads_histogram"],
        "conflicts": conflicts,
        "distinct_tables": len(tables),
    }
    with open(os.path.join(SUBREP, "verification_264.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if not conflicts else 1


if __name__ == "__main__":
    sys.exit(main())
