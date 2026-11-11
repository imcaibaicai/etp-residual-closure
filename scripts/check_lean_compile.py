#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-compile the Lean witness files one by one and record the result.

This reproduces ``data/lean_compile_check.json``, which is the evidence behind the
claim "all 31 witness files compile". It runs ``lake env lean`` per file, serially,
and records exit code, wall time and the first error line.

Prerequisites, in order
-----------------------
1. The ETP project must have its own modules built. A fresh checkout carries the
   dependency oleans (mathlib etc.) but not ``equational_theories`` oleans, so
   ``import equational_theories.Equations.All`` fails with ``unknown module
   prefix``. Build the modules these files import first:

       lake build equational_theories.Equations.All
       lake build equational_theories.FactsSyntax equational_theories.MemoFinOp \\
                  equational_theories.DecideBang

2. ``lake`` must be on PATH, or passed with ``--lake``.

Usage
-----
    export ETP_HOME=/path/to/etp
    python3 scripts/check_lean_compile.py \\
        --project "$ETP_HOME/equational_theories" \\
        --lean-dir lean \\
        --out data/lean_compile_check.json

What this is NOT
----------------
It is not a full ``lake build``, not the project's CI, and not a maintainer
review. It compiles 31 individual files that import a handful of project modules.
Say exactly that when quoting the result.

The ``project`` field written into the JSON is the label you pass with
``--project-label``, never the real absolute path: this file is published, and a
regenerated record must not reintroduce a machine-local path.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time


def first_error(text: str) -> str | None:
    for line in text.splitlines():
        low = line.lower()
        if "error" in low and "0 errors" not in low:
            return line.strip()[:400]
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True,
                    help="ETP checkout root (the directory holding lakefile.lean)")
    ap.add_argument("--lean-dir", default="lean", help="directory holding the .lean files")
    ap.add_argument("--out", default="data/lean_compile_check.json")
    ap.add_argument("--lake", default="lake", help="path to the lake executable")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per file")
    ap.add_argument("--project-label", default="$ETP_HOME/equational_theories",
                    help="label recorded instead of the real absolute project path")
    ap.add_argument("--only", default=None,
                    help="compile only files whose name contains this substring")
    args = ap.parse_args(argv)

    project = os.path.abspath(args.project)
    lean_dir = os.path.abspath(args.lean_dir)
    if not os.path.isdir(project):
        print(f"error: project not found: {project}", file=sys.stderr)
        return 2
    if not os.path.isdir(lean_dir):
        print(f"error: lean dir not found: {lean_dir}", file=sys.stderr)
        return 2

    files = sorted(n for n in os.listdir(lean_dir) if n.endswith(".lean"))
    if args.only:
        files = [n for n in files if args.only in n]
    if not files:
        print("error: no .lean files to compile", file=sys.stderr)
        return 2

    toolchain_path = os.path.join(project, "lean-toolchain")
    toolchain = "unknown"
    if os.path.isfile(toolchain_path):
        with open(toolchain_path, encoding="utf-8") as fh:
            toolchain = fh.read().strip()

    results = []
    total_seconds = 0.0
    passed = failed = 0
    for name in files:
        path = os.path.join(lean_dir, name)
        started = time.time()
        try:
            proc = subprocess.run(
                [args.lake, "env", "lean", path],
                cwd=project, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=args.timeout,
            )
            exit_code, out, err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            exit_code, out, err = 124, "", f"timeout after {args.timeout}s"
        except FileNotFoundError:
            print(f"error: cannot execute {args.lake!r}; pass --lake", file=sys.stderr)
            return 2
        elapsed = round(time.time() - started, 1)
        total_seconds += elapsed

        combined = (out or "") + "\n" + (err or "")
        ok = exit_code == 0
        passed += ok
        failed += not ok
        rec = {
            "file": name,
            "exit": exit_code,
            "seconds": elapsed,
            "ok": ok,
            "first_error": None if ok else first_error(combined),
        }
        results.append(rec)
        print(f"{'ok  ' if ok else 'FAIL'} {name:34s} {elapsed:6.1f}s exit={exit_code}")

    report = {
        "generated_at": dt.datetime.now().replace(microsecond=0).isoformat(),
        "toolchain": toolchain,
        "project": args.project_label,
        "note": ("compiled one file at a time with `lake env lean`; NOT a full "
                 "`lake build`, NOT a CI run, NOT a maintainer review"),
        "total": len(files),
        "passed": passed,
        "failed": failed,
        "total_seconds": round(total_seconds, 1),
        "results": results,
    }
    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=4)
        fh.write("\n")

    print()
    print(f"total {len(files)}  passed {passed}  failed {failed}  "
          f"{round(total_seconds, 1)}s -> {args.out}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
