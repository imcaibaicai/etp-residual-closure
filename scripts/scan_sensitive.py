#!/usr/bin/env python3
"""Pre-publication gate: find anything in this repository that must not be published.

Three classes of hit, all fatal by default:

  1. absolute local paths   -- Windows drive letters, POSIX home directories
  2. personal identifiers   -- names, institutions, account handles
  3. local-only artifacts   -- paths that leak a machine layout even without a name

Usage
-----
    python3 scripts/scan_sensitive.py --root .
    python3 scripts/scan_sensitive.py --root . --json out/scan.json
    python3 scripts/scan_sensitive.py --root . --warn-only      # exit 0 on hits

Exit codes
----------
    0   no hits (or --warn-only)
    1   hits found
    2   the scanner itself failed (unreadable file, bad root)

Design note
-----------
The pattern list is deliberately over-broad: a false positive costs one line of
review, a false negative costs a leak. Everything reported is classified as
`path` or `identifier` so a reviewer can tell "this is a machine layout" from
"this is a person".
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# --- what counts as sensitive -------------------------------------------------

# Absolute local paths.
#
# A single literal backslash is built at run time from its code point, so this
# file's own source contains no path-like example at all. That matters because
# the scanner scans itself: an example that looks like a real absolute path makes
# the gate fail on its own source, and "the gate cannot pass itself" invites
# people to add exemptions.
BSLASH = re.escape(chr(92))

# The first rule catches a drive letter followed by a doubled backslash (how a
# path appears inside JSON); the second catches a drive letter followed by a
# single backslash (how it appears in prose and in Python). A generic
# "/(home|Users)/name" rule covers POSIX and macOS home directories.
PATH_PATTERNS = [
    (re.compile(r"[A-Za-z]:" + BSLASH * 2), "windows-unc-escaped"),
    (re.compile(r"[A-Za-z]:" + BSLASH), "windows-drive"),
    (re.compile(r"(?<![A-Za-z0-9_.])/(?:home|Users)/[A-Za-z0-9_.-]+"), "posix-home"),
    (re.compile("file" + ":/" + "//"), "file-url"),
]

# Personal / institutional identifiers. These catch a person or a place by
# shape; the literal deny list (below) is what catches a specific one, and it
# comes from the command line only.
IDENTIFIER_PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "email-address"),
    (re.compile(r"(?i)\bstudent\s*(id|no\.?|number)\b"), "student-id"),
    (re.compile(r"(?i)\b(university|college)\s+of\s+\w+"), "institution"),
]

# Literal deny list: command line only, never a file.
#
# There is deliberately no deny-file support. A deny file is a list of the exact
# strings you are trying to keep out of a public repository; if it is ever
# committed by accident, the leak is worse than the one it was guarding against,
# because it is a curated inventory. Sensitive literals therefore travel as
# --deny arguments and live only in the process argument vector. Nothing is read
# from disk.
#
# For the same reason this file's own example paths are written with a
# placeholder drive (`X:`) and never as a real-looking absolute path: the scanner
# scans itself, and an example that looks like a real path makes the gate fail on
# its own source.

TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".cff", ".json", ".tsv", ".csv", ".yml", ".yaml",
    ".lean", ".toml", ".cfg", ".ini", ".sh", ".ps1", ".mjs", ".js",
}
BINARY_SNIFF = (b"\x00",)

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "out"}


def iter_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = os.path.join(dirpath, name)
            ext = os.path.splitext(name)[1].lower()
            if ext not in TEXT_SUFFIXES and ext != "":
                continue
            yield path


def load_deny(extra: list[str]) -> list[tuple[re.Pattern, str]]:
    """Build the literal deny list from the command line only. Never from disk."""
    deny = []
    for lit in extra:
        for piece in lit.split(","):
            piece = piece.strip()
            if piece:
                deny.append((re.compile(re.escape(piece)), "deny-literal"))
    return deny


def scan_file(path: str, deny) -> list[dict]:
    hits = []
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise RuntimeError(f"cannot read {path}: {exc}") from exc
    if any(s in raw for s in BINARY_SNIFF):
        return hits
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return hits
    for lineno, line in enumerate(text.splitlines(), 1):
        for pattern, label in PATH_PATTERNS:
            for m in pattern.finditer(line):
                hits.append({
                    "file": path, "line": lineno, "kind": "path",
                    "rule": label, "match": m.group(0),
                    "context": line.strip()[:200],
                })
        for pattern, label in IDENTIFIER_PATTERNS:
            for m in pattern.finditer(line):
                hits.append({
                    "file": path, "line": lineno, "kind": "identifier",
                    "rule": label, "match": m.group(0),
                    "context": line.strip()[:200],
                })
        for pattern, label in deny:
            for m in pattern.finditer(line):
                hits.append({
                    "file": path, "line": lineno, "kind": "identifier",
                    "rule": label, "match": m.group(0),
                    "context": line.strip()[:200],
                })
    return hits


def selftest() -> int:
    """Prove the gate actually fires, without putting a real path in this file.

    Every probe is assembled at run time from character codes, so the source of
    this module contains no path-like or identifier-like example for the scanner
    to flag when it scans itself.
    """
    bs = chr(92)
    at = chr(64)
    probes = [
        ("D" + ":" + bs + "foo" + bs + "bar", PATH_PATTERNS[1][0], True,
         "single-backslash absolute path"),
        ("D" + ":" + bs * 2 + "foo" + bs * 2 + "bar", PATH_PATTERNS[0][0], True,
         "JSON-escaped absolute path"),
        ("/" + "home/" + "someone", PATH_PATTERNS[2][0], True, "POSIX home path"),
        ("user" + at + "example.org", IDENTIFIER_PATTERNS[0][0], True, "email address"),
        ("https" + ":/" + "//github.com/x/y", PATH_PATTERNS[1][0], False, "plain URL"),
        ("ratio " + "3" + ":" + "2", PATH_PATTERNS[1][0], False, "colon in prose"),
    ]
    bad = 0
    for probe, pattern, want, label in probes:
        got = bool(pattern.search(probe))
        if got != want:
            bad += 1
            print(f"SELFTEST FAIL: {label}: expected {want}, got {got}")
    if bad:
        print(f"SELFTEST: FAIL ({bad} of {len(probes)})")
        return 1
    print(f"SELFTEST: PASS ({len(probes)} probes: {len(probes) - 2} positive, 2 negative)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repository root to scan")
    ap.add_argument("--deny", action="append", default=[],
                    help="extra literal that must not appear, comma-separated "
                         "(repeatable). Pass identifiers here; never write them "
                         "into a file inside the repository")
    ap.add_argument("--json", default=None, help="also write hits as JSON here")
    ap.add_argument("--warn-only", action="store_true",
                    help="report hits but exit 0")
    ap.add_argument("--selftest", action="store_true",
                    help="check that the patterns fire on synthetic probes, then exit")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    deny = load_deny(args.deny)
    files = sorted(iter_files(root))
    hits: list[dict] = []
    for path in files:
        try:
            hits.extend(scan_file(path, deny))
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    rel = lambda p: os.path.relpath(p, root).replace(os.sep, "/")
    by_kind = {}
    for h in hits:
        by_kind[h["kind"]] = by_kind.get(h["kind"], 0) + 1
        print(f"{rel(h['file'])}:{h['line']}: [{h['kind']}/{h['rule']}] {h['match']}")
        print(f"    {h['context']}")

    print()
    print(f"scanned {len(files)} text files under {rel(root) or '.'}")
    if hits:
        print(f"HITS: {len(hits)} " + ", ".join(f"{k}={v}" for k, v in sorted(by_kind.items())))
    else:
        print("HITS: 0 (clean)")

    if args.json:
        out = os.path.abspath(args.json)
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        payload = {
            "root": rel(root) or ".",
            "files_scanned": len(files),
            "hits": [{**h, "file": rel(h["file"])} for h in hits],
            "by_kind": by_kind,
        }
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=1, ensure_ascii=False, sort_keys=True)
        print(f"wrote {rel(out)}")

    if hits and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
