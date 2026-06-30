#!/usr/bin/env python3
"""Drift guard for the whoshe extractor registry.

Three invariants enforced:

  1. Every extractor registered in extractors_manifest.json has a source file
     at the declared path.
  2. Every extractor source file implements both detect() and extract()
     (verified by AST-free grep for function definitions).
  3. Every extractor has a MAINTAINER-{id}.md file in this directory.

Run:   python3 extractors/sync_check.py
Exit:  0 if every invariant holds, 1 (with a report) otherwise.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "extractors" / "extractors_manifest.json"
EXTRACTORS_DIR = ROOT / "extractors"


def main() -> int:
    failures: list[str] = []

    if not MANIFEST.exists():
        print(f"[!] Manifest not found: {MANIFEST}")
        return 1

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    extractors = manifest.get("extractors", [])

    for entry in extractors:
        eid = entry["id"]
        path = ROOT / entry["path"]

        # Invariant 1: source file exists at declared path
        if not path.exists():
            failures.append(
                f"  ✗ Invariant 1 — declared path not found: {entry['path']} (extractor: {eid})"
            )
            continue

        # Invariant 2: source file implements detect() and extract()
        src = path.read_text(encoding="utf-8")
        if not re.search(r"^def detect\b", src, re.MULTILINE):
            failures.append(
                f"  ✗ Invariant 2 — missing detect() function: {entry['path']} (extractor: {eid})"
            )
        if not re.search(r"^def extract\b", src, re.MULTILINE):
            failures.append(
                f"  ✗ Invariant 2 — missing extract() function: {entry['path']} (extractor: {eid})"
            )

        # Invariant 3: MAINTAINER-{id}.md exists
        maintainer = EXTRACTORS_DIR / f"MAINTAINER-{eid}.md"
        if not maintainer.exists():
            failures.append(
                f"  ✗ Invariant 3 — missing MAINTAINER-{eid}.md (extractor: {eid})"
            )

    print(f"whoshe extractor registry drift check — {len(extractors)} extractor(s)\n")
    if failures:
        print("DRIFT DETECTED:\n")
        print("\n".join(failures))
        print(f"\n{len(failures)} invariant(s) failed.")
        return 1

    print(f"OK — all 3 invariants pass across {len(extractors)} extractor(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
