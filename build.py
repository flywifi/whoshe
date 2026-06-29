#!/usr/bin/env python3
"""
build.py — produce the deliverable zip for the iMessage Forensic Toolkit.

Why Python instead of `zip`/PowerShell: this script sets each entry's
permission bits explicitly via ZipInfo.external_attr, so the executable bit on
the .command launchers survives even when the zip is built on Windows (where the
filesystem has no Unix exec bit). Run it the same way everywhere:

    python3 build.py

What it does:
  * Collects the file list from `git ls-files`, so only tracked files are
    packaged. This automatically excludes __pycache__/, *.pyc, and *.zip
    (they are in .gitignore), and never bundles the output zip itself.
  * Writes mode 0o100755 for *.command, 0o100644 for everything else.
  * Re-opens the finished zip and asserts both .command entries are 0o755.

The output zip is gitignored and is a deliverable only — do NOT commit it.
"""
import os
import stat
import subprocess
import sys
import zipfile

OUTPUT = "imessage-forensic-toolkit-LATEST.zip"


def tracked_files():
    """Return git-tracked files (respects .gitignore, excludes the output zip)."""
    out = subprocess.run(
        ["git", "ls-files"],
        capture_output=True, text=True, check=True,
    ).stdout
    files = [line for line in out.splitlines() if line and line != OUTPUT]
    if not files:
        sys.exit("[!] `git ls-files` returned nothing — run from the repo root.")
    return files


def mode_for(path: str) -> int:
    """0o755 for double-clickable launchers, 0o644 otherwise."""
    return 0o100755 if path.endswith(".command") else 0o100644


def build() -> list[str]:
    files = tracked_files()
    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)
    commands = []
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(files):
            info = zipfile.ZipInfo(path)
            info.external_attr = mode_for(path) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(path, "rb") as fh:
                z.writestr(info, fh.read())
            if path.endswith(".command"):
                commands.append(path)
    return commands


def verify_exec_bits() -> None:
    """Re-open the zip and assert the .command entries are executable."""
    bad = []
    with zipfile.ZipFile(OUTPUT) as z:
        commands = [i for i in z.infolist() if i.filename.endswith(".command")]
        if not commands:
            sys.exit("[!] No .command files found in the zip — aborting.")
        for info in commands:
            perms = (info.external_attr >> 16) & 0o777
            mark = "ok" if perms == 0o755 else "WRONG"
            print(f"    {info.filename}: {oct(perms)} ({mark})")
            if perms != 0o755:
                bad.append(info.filename)
    if bad:
        sys.exit(f"[!] Not executable in zip: {', '.join(bad)}")


def main() -> int:
    commands = build()
    size = os.path.getsize(OUTPUT)
    print(f"[+] Wrote {OUTPUT} ({size:,} bytes)")
    print("[+] Checking executable bits inside the zip:")
    verify_exec_bits()
    print(f"[+] Done. {len(commands)} .command launcher(s) preserved at 0o755.")
    print("    Deliver this zip to the user — do NOT commit it (.gitignore covers it).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
