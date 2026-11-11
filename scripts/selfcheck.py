#!/usr/bin/env python3
"""Repository self-check: no BOM, relative links resolve, CHECKSUMS.txt verifies.

Usage
-----
    python3 scripts/selfcheck.py --root .
    python3 scripts/selfcheck.py --root . --write-checksums     # regenerate CHECKSUMS.txt
    python3 scripts/selfcheck.py --root . --skip-checksums

Exit codes
----------
    0   all checks pass
    1   at least one check failed
    2   the checker itself failed

Checks
------
  1  encoding   every text file is valid UTF-8 with no BOM and no CRLF-only weirdness
                (CRLF is allowed; a lone CR is not)
  2  links      every relative Markdown link / image target exists on disk;
                absolute URLs, mailto:, and pure anchors are skipped
  3  checksums  CHECKSUMS.txt lists every tracked file and every hash matches

Why BOM matters here
--------------------
A UTF-8 BOM in a .lean file makes Lean report `1:0: error: expected token`, and a
BOM in CHECKSUMS.txt breaks byte comparisons downstream. Nothing in this
repository may carry one.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from urllib.parse import unquote

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "out"}
CHECKSUM_NAME = "CHECKSUMS.txt"
# Files excluded from CHECKSUMS.txt: it cannot hash itself.
CHECKSUM_EXCLUDE = {CHECKSUM_NAME}

LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]+>|[^)\s]+)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def rel(root: str, path: str) -> str:
    return os.path.relpath(path, root).replace(os.sep, "/")


def iter_files(root: str, suffixes=None):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            if suffixes is not None:
                if os.path.splitext(name)[1].lower() not in suffixes:
                    continue
            yield path


def check_encoding(root: str) -> list[str]:
    problems = []
    for path in iter_files(root):
        with open(path, "rb") as fh:
            raw = fh.read()
        if raw.startswith(b"\xef\xbb\xbf"):
            problems.append(f"BOM: {rel(root, path)}")
            continue
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            problems.append(f"UTF-16 BOM: {rel(root, path)}")
            continue
        if b"\x00" in raw:
            continue  # binary, skip
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            problems.append(f"not UTF-8: {rel(root, path)} ({exc})")
            continue
        if "\r" in text.replace("\r\n", ""):
            problems.append(f"lone CR: {rel(root, path)}")
    return problems


def check_links(root: str) -> list[str]:
    problems = []
    for path in iter_files(root, suffixes={".md"}):
        base = os.path.dirname(path)
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        # strip fenced code blocks: commands inside them are not links
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in LINK_RE.finditer(line):
                target = m.group(1).strip()
                if target.startswith("<") and target.endswith(">"):
                    target = target[1:-1]
                if not target or target.startswith("#"):
                    continue
                if SCHEME_RE.match(target):
                    continue
                target = target.split("#", 1)[0].split("?", 1)[0]
                if not target:
                    continue
                if target.startswith("/"):
                    problems.append(
                        f"absolute link (use a relative one): {rel(root, path)}:{lineno} -> {target}")
                    continue
                resolved = os.path.normpath(os.path.join(base, unquote(target)))
                if not os.path.exists(resolved):
                    problems.append(
                        f"broken link: {rel(root, path)}:{lineno} -> {target}")
    return problems


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked_files(root: str) -> list[str]:
    out = []
    for path in iter_files(root):
        name = rel(root, path)
        if name in CHECKSUM_EXCLUDE:
            continue
        out.append(name)
    return sorted(out)


def write_checksums(root: str) -> str:
    lines = [
        "# sha256 of every file in this repository, sorted by path.",
        "# Verify: python3 scripts/selfcheck.py --root .",
        '# Regenerate: python3 scripts/selfcheck.py --root . --write-checksums',
    ]
    for name in tracked_files(root):
        lines.append(f"{sha256_file(os.path.join(root, name))}  {name}")
    text = "\n".join(lines) + "\n"
    target = os.path.join(root, CHECKSUM_NAME)
    with open(target, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return text


def check_checksums(root: str) -> list[str]:
    problems = []
    target = os.path.join(root, CHECKSUM_NAME)
    if not os.path.isfile(target):
        return [f"{CHECKSUM_NAME} missing (generate it with --write-checksums)"]
    listed = {}
    with open(target, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("  ", 1)
            if len(parts) != 2 or len(parts[0]) != 64:
                problems.append(f"{CHECKSUM_NAME}:{lineno}: malformed line")
                continue
            listed[parts[1]] = parts[0]
    on_disk = set(tracked_files(root))
    for name, digest in sorted(listed.items()):
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            problems.append(f"{CHECKSUM_NAME}: listed file missing: {name}")
            continue
        actual = sha256_file(path)
        if actual != digest:
            problems.append(f"{CHECKSUM_NAME}: hash mismatch: {name}")
    for name in sorted(on_disk - set(listed)):
        problems.append(f"{CHECKSUM_NAME}: file not listed: {name}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--write-checksums", action="store_true")
    ap.add_argument("--skip-checksums", action="store_true")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    if args.write_checksums:
        text = write_checksums(root)
        n = sum(1 for line in text.splitlines() if line and not line.startswith("#"))
        print(f"wrote {CHECKSUM_NAME}: {n} files")

    failed = 0
    for label, fn in (
        ("encoding", check_encoding),
        ("links", check_links),
        ("checksums", None if args.skip_checksums else check_checksums),
    ):
        if fn is None:
            print(f"[skip] {label}")
            continue
        problems = fn(root)
        if problems:
            failed += len(problems)
            print(f"[FAIL] {label}: {len(problems)} problem(s)")
            for p in problems[:200]:
                print(f"    {p}")
            if len(problems) > 200:
                print(f"    ... and {len(problems) - 200} more")
        else:
            print(f"[ok]   {label}")

    print()
    print("SELFCHECK: " + ("PASS" if failed == 0 else f"FAIL ({failed} problems)"))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
