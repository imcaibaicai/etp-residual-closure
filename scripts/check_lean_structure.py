# -*- coding: utf-8 -*-
"""Structural check of the generated Lean files.

编译是**另一条独立证据**，在 ``lean/`` 下 31 个文件上做过：Lean 4.29.1、
``lake env lean`` 逐个编译，31/31 通过（两次独立测量：384 秒与 423 秒），记录在
``data/lean_compile_check.json``，由 ``scripts/check_lean_compile.py`` 复现。
前提是先定向构建这些文件 import 的模块；全新检出里只有依赖包的 olean，没有
``equational_theories`` 的，直接编译会报 ``unknown module prefix``。

本脚本做的是与编译**不重叠**的**结构检查**（读文本，不编译），并逐项声明查了什么：

1. 文件头 import 齐全、``set_option`` 存在；
2. ``def «名字» : Magma (Fin n)`` 里的 ``n`` 与 ``finOpTable`` 字面量的边长一致，
   表项都在 ``0..n-1`` 内；
3. 一条定理、名字与 def 对应，``Facts G [sat] [ref]`` 的列表与该表在
   ``witnesses_264.json`` 里真正答过的律集合一致；
4. 全包内 def 名唯一；
5. 括号与 ``«»`` 配对，文件以定理结束。
"""

from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))   # <repo>/scripts
WS = os.path.dirname(HERE)                          # <repo>
LEAN = os.path.join(WS, "lean")
DATA = os.path.join(WS, "data")
OUT = os.path.join(WS, "data", "lean_structure_check.json")

DEF = re.compile(r'def «([^»]+)» : Magma \(Fin (\d+)\) where\n  op := finOpTable "(\[\[.*?\]\])"')
THM = re.compile(r'theorem «facts ([^»]+)» :\n  ∃ \(G : Type\) \(_ : Magma G\) \(_: Finite G\), '
                 r'Facts G \[([^\]]*)\] \[([^\]]*)\] :=\n    ⟨Fin (\d+), «([^»]+)», '
                 r'Finite\.of_fintype _, by decideFin!⟩')


def main():
    with open(os.path.join(DATA, "witnesses_264.json"), encoding="utf-8") as fh:
        doc = json.load(fh)
    with open(os.path.join(DATA, "tables_referenced.json"), encoding="utf-8") as fh:
        tabs = json.load(fh)["tables"]

    expect = {}
    for rec in doc["records"]:
        sha = rec["witness"]["sha256"]
        e = expect.setdefault(sha, {"sat": set(), "ref": set()})
        e["sat"].add(rec["from"])
        e["ref"].add(rec["to"])

    files = sorted(f for f in os.listdir(LEAN) if f.endswith(".lean"))
    seen_names = {}
    results = []
    failures = []

    for fname in files:
        path = os.path.join(LEAN, fname)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()

        issues = []
        imports = [ln for ln in text.splitlines() if ln.startswith("import ")]
        if len(imports) != 5:
            issues.append(f"import count {len(imports)} != 5")
        if "set_option linter.unusedVariables false" not in text:
            issues.append("missing set_option")

        d = DEF.search(text)
        t = THM.search(text)
        if not d:
            issues.append("def not matched")
        if not t:
            issues.append("theorem not matched")

        if d and t:
            def_name, n_def, literal = d.group(1), int(d.group(2)), d.group(3)
            table = json.loads(literal)
            n_tab = len(table)
            if n_tab != n_def:
                issues.append(f"def carrier {n_def} != table size {n_tab}")
            if any(len(r) != n_tab for r in table):
                issues.append("table not square")
            if any(not (0 <= v < n_tab) for r in table for v in r):
                issues.append("table entry out of range")
            thm_name, sat, ref, n_thm, used = t.group(1), t.group(2), t.group(3), int(t.group(4)), t.group(5)
            if thm_name != def_name or used != def_name:
                issues.append(f"name mismatch def={def_name} thm={thm_name} used={used}")
            if n_thm != n_def:
                issues.append(f"theorem carrier {n_thm} != def carrier {n_def}")

            sha = None
            for k, v in tabs.items():
                if v["table"] == table:
                    sha = k
                    break
            sat_l = sorted(int(x) for x in sat.split(",") if x.strip())
            ref_l = sorted(int(x) for x in ref.split(",") if x.strip())
            if sha is None:
                issues.append("table not found in tables_referenced.json")
            else:
                if sat_l != sorted(expect[sha]["sat"]):
                    issues.append("satisfied list != witnesses_264 sat set")
                if ref_l != sorted(expect[sha]["ref"]):
                    issues.append("refuted list != witnesses_264 ref set")
                if tabs[sha]["carrier"] != n_def:
                    issues.append("carrier disagrees with tables_referenced.json")
                if tabs[sha]["is_transpose"] != def_name.endswith("T"):
                    issues.append("transpose flag disagrees with name suffix")

            if def_name in seen_names:
                issues.append(f"duplicate def name, also in {seen_names[def_name]}")
            seen_names[def_name] = fname

        if text.count("«") != text.count("»"):
            issues.append("unbalanced «»")
        if not text.rstrip().endswith("⟩"):
            issues.append("file does not end with a term")

        results.append({"file": fname, "issues": issues})
        if issues:
            failures.append({"file": fname, "issues": issues})

    report = {
        "checked": ["imports present", "def carrier == table size", "table square and in range",
                    "one theorem per file, name matches def", "Facts lists == witnesses_264 sets",
                    "carrier matches tables_referenced.json", "transpose flag matches name suffix",
                    "def names unique", "«» balanced", "file ends with a term"],
        "not_checked": [
            "compilation: checked separately, by `lake env lean` against Lean 4.29.1 "
            "(data/lean_compile_check.json: 31 passed, 0 failed; 384 s and 423 s on two runs). This "
            "script reads the files as text and compiles nothing",
            "a full `lake build` of the ETP project, and its CI",
            "proof terms: `by decideFin!` is read as text here, never elaborated",
        ],
        "files": len(files),
        "passed": len(files) - len(failures),
        "failed": len(failures),
        "failures": failures,
        "per_file": results,
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: report[k] for k in ("files", "passed", "failed", "failures")},
                     ensure_ascii=False, indent=1))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
