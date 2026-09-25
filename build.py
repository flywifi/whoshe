#!/usr/bin/env python3
"""
build.py — produce the deliverable zip for the iMessage Forensic Toolkit.

    python3 build.py          # end-user zip: launcher + README + LICENSE
    python3 build.py --full   # every file in the commit (developer bundle)

Packages the files as they are in the HEAD commit, not the working tree, so the
result is the same on macOS, Linux and Windows:

  * Line endings are LF. The bytes come from git's object store (LF, enforced by
    .gitattributes), never from a Windows checkout where core.autocrlf may have
    turned them into CRLF. A CRLF launcher fails on macOS with
    "/bin/bash^M: bad interpreter". As a backstop the build refuses any text file
    that contains a carriage return.
  * The launcher stays executable. Each entry is marked as made on Unix
    (create_system = 3) with mode 0755 for *.command. Python on Windows would
    otherwise mark entries as MS-DOS, and unzip tools then ignore the mode bits.
  * Uncommitted edits are NOT included. The build warns if there are any.

Everything goes under one top-level folder, `imessage-forensic/`, so unzipping
yields a single folder. The output zip is gitignored and is a deliverable only.
Do NOT commit it.
"""
import re
import subprocess
import sys
import time
import zipfile

LAUNCHER = "imessage_ultimate_launcher.command"
USER_FILES = [LAUNCHER, "README.md", "LICENSE"]
TOP = "imessage-forensic"
TEXT_SUFFIXES = (".command", ".sh", ".py", ".md", ".txt", ".json", "LICENSE", ".gitignore", ".gitattributes")


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout


def head_tree() -> dict:
    """{path: (mode, blob_sha)} for every file in HEAD."""
    tree = {}
    for rec in git("ls-tree", "-r", "-z", "HEAD").split(b"\0"):
        if not rec:
            continue
        meta, path = rec.split(b"\t", 1)
        mode, kind, sha = meta.split()
        if kind == b"blob":
            tree[path.decode()] = (mode.decode(), sha.decode())
    return tree


def main() -> int:
    full = "--full" in sys.argv[1:]
    tree = head_tree()
    files = sorted(tree) if full else USER_FILES
    missing = [f for f in files if f not in tree]
    if missing:
        sys.exit(f"[!] Not in the HEAD commit: {', '.join(missing)}")

    dirty = git("status", "--porcelain", "--", *files).decode().strip()
    if dirty:
        print("[!] Uncommitted changes are NOT included in the zip:")
        print("    " + dirty.replace("\n", "\n    "))

    sha = git("rev-parse", "--short", "HEAD").decode().strip()
    stamp = int(git("log", "-1", "--format=%ct", "HEAD").decode().strip())
    date_time = time.gmtime(stamp)[:6]
    launcher_src = git("cat-file", "blob", tree[LAUNCHER][1]).decode("utf-8")
    m = re.search(r'^_TOOL_VERSION="([^"]+)"', launcher_src, re.M)
    version = m.group(1) if m else "unknown"
    output = f"imessage-forensic-v{version}{'-full' if full else ''}-{sha}.zip"

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for path in files:
            mode, blob = tree[path]
            data = git("cat-file", "blob", blob)
            if path.endswith(TEXT_SUFFIXES) and b"\r" in data:
                sys.exit(f"[!] {path} contains a carriage return (CRLF) — refusing to build.")
            info = zipfile.ZipInfo(f"{TOP}/{path}", date_time=date_time)
            info.create_system = 3                      # Unix: extractors honour the mode bits
            perms = 0o755 if (mode == "100755" or path.endswith(".command")) else 0o644
            info.external_attr = (0o100000 | perms) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)

    verify(output)
    print(f"[+] Wrote {output}  ({len(files)} files from commit {sha})")
    print("    Deliver this zip; do NOT commit it (.gitignore covers *.zip).")
    return 0


def verify(output: str) -> None:
    """Re-open the zip and check what an unzip tool will actually see."""
    problems = []
    with zipfile.ZipFile(output) as z:
        for info in z.infolist():
            perms = (info.external_attr >> 16) & 0o777
            if info.create_system != 3:
                problems.append(f"{info.filename}: create_system={info.create_system} (mode bits would be ignored)")
            if info.filename.endswith(".command") and perms != 0o755:
                problems.append(f"{info.filename}: mode {oct(perms)} (not executable)")
            if info.filename.endswith(TEXT_SUFFIXES) and b"\r" in z.read(info):
                problems.append(f"{info.filename}: contains CR")
            if info.filename.endswith(".command"):
                print(f"    {info.filename}: {oct(perms)}, unix entry, LF only")
    if problems:
        sys.exit("[!] Zip check failed:\n    " + "\n    ".join(problems))


if __name__ == "__main__":
    raise SystemExit(main())
