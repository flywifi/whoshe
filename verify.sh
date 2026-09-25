#!/usr/bin/env bash
#
# verify.sh — pre-commit integrity check for the iMessage Forensic Toolkit.
#
#   1. shell syntax      bash -n on the launcher, RESET.command, verify.sh, scripts/*.sh
#   2. line endings      no CR in any tracked text file; .gitattributes present
#   3. file modes        every tracked *.command / *.sh is 100755 in git
#   4. embedded Python   all six *_PY_EOF heredocs found; each parses as Python 3.9
#                        and uses no 3.10+ runtime features (X | Y annotations,
#                        match), because the launcher runs them on Apple's 3.9
#   5. standalone Python every tracked *.py parses (UTF-8)
#   6. drift guard       sync_check.py (the listed security invariants)
#
# Static checks only: nothing here runs the tool or exercises macOS behavior.
# Exit 0 = clean; the first failure stops the run.
#
# Works on Linux, macOS and Windows git-bash. Set PYTHON=/path/to/python to
# choose the interpreter; otherwise the first real one of python3, python,
# py -3 is used (this skips the Windows Store shortcut, which doesn't run).
#
set -euo pipefail
cd "$(dirname "$0")"

fail() { echo "      FAIL: $*" >&2; exit 1; }

# ── pick a working Python ────────────────────────────────────────────────────
PY=()
if [ -n "${PYTHON:-}" ]; then
    PY=("$PYTHON")
else
    for cand in "python3" "python" "py -3"; do
        # shellcheck disable=SC2086
        if $cand -c "import sys" >/dev/null 2>&1; then read -r -a PY <<< "$cand"; break; fi
    done
fi
[ ${#PY[@]} -gt 0 ] || fail "no working Python found (install Python 3, or set PYTHON=/path/to/python)"
"${PY[@]}" -c "import sys" >/dev/null 2>&1 || fail "PYTHON=${PYTHON:-} does not run"
PY+=(-X utf8)   # UTF-8 file I/O and stdout, even on Windows (cp1252) consoles
echo "Using Python: $("${PY[@]}" -c 'import sys; print(sys.executable, sys.version.split()[0])')"

echo "[1/6] shell syntax..."
for f in imessage_ultimate_launcher.command RESET.command verify.sh scripts/*.sh; do
    [ -f "$f" ] || continue
    bash -n "$f" || fail "bash syntax error in $f"
done
echo "      ok"

echo "[2-5/6] line endings, file modes, embedded + standalone Python..."
"${PY[@]}" - <<'PYEOF'
import ast, re, subprocess, sys
from pathlib import Path

def fail(msg):
    print(f"      FAIL: {msg}")
    sys.exit(1)

def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout

BINARY = (".zip", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".db", ".sqlite")
tracked = [f for f in git("ls-files", "-z").split("\0") if f]

# [2] line endings
if not Path(".gitattributes").is_file():
    fail(".gitattributes is missing (it forces LF line endings)")
crlf = [f for f in tracked
        if not f.lower().endswith(BINARY) and Path(f).is_file() and b"\r" in Path(f).read_bytes()]
if crlf:
    fail("carriage returns (CRLF) in: " + ", ".join(crlf)
         + "\n            fix: git add --renormalize . (with .gitattributes in place)")
print("      [2] line endings ok (LF only)")

# [3] file modes
bad_modes = []
for line in git("ls-files", "--stage", "-z").split("\0"):
    if not line:
        continue
    meta, path = line.split("\t", 1)
    if path.endswith((".command", ".sh")) and meta.split()[0] != "100755":
        bad_modes.append(f"{path} ({meta.split()[0]})")
if bad_modes:
    fail("not executable in git: " + ", ".join(bad_modes)
         + "\n            fix: git update-index --chmod=+x <file>")
print("      [3] file modes ok (*.command, *.sh are 100755)")

# [4] embedded heredocs
EXPECTED = {"CORE_PY_EOF", "CK_PY_EOF", "PARSER_PY_EOF", "REPORT_PY_EOF",
            "REORG_PY_EOF", "PLATFORM_PY_EOF"}
launcher = Path("imessage_ultimate_launcher.command").read_text(encoding="utf-8")
found = set(re.findall(r"cat\s*<<\s*'(\w+_PY_EOF)'", launcher))
if found != EXPECTED:
    fail(f"heredoc set changed: missing {sorted(EXPECTED - found) or 'none'}, "
         f"new {sorted(found - EXPECTED) or 'none'} (update verify.sh and sync_check.py)")

def py310_features(tree):
    """Constructs that parse under 3.9's grammar but fail at runtime on 3.9."""
    hits = []
    for node in ast.walk(tree):
        if type(node).__name__ == "Match":
            hits.append(f"line {node.lineno}: match statement")
        anns = [getattr(node, "annotation", None), getattr(node, "returns", None)]
        for ann in filter(None, anns):
            for sub in ast.walk(ann):
                if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.BitOr):
                    hits.append(f"line {sub.lineno}: 'X | Y' annotation")
    return hits

for marker in sorted(EXPECTED):
    m = re.search(rf"cat\s*<<\s*'{marker}'.*?\n(.*?)\n{marker}\n", launcher, re.DOTALL)
    if not m:
        fail(f"could not extract heredoc {marker}")
    try:
        tree = ast.parse(m.group(1), feature_version=(3, 9))
    except SyntaxError as e:
        fail(f"{marker} line {e.lineno}: {e.msg} (must parse as Python 3.9)")
    hits = py310_features(tree)
    if hits:
        fail(f"{marker} uses Python 3.10+ features (Apple's Python is 3.9): " + "; ".join(hits))
print(f"      [4] embedded heredocs ok ({len(EXPECTED)} found, Python 3.9 compatible)")

# [5] standalone Python
py_files = [f for f in tracked if f.endswith(".py")]
for f in py_files:
    try:
        ast.parse(Path(f).read_text(encoding="utf-8"), filename=f)
    except SyntaxError as e:
        fail(f"{f} line {e.lineno}: {e.msg}")
print(f"      [5] standalone Python ok ({len(py_files)} files parse)")
PYEOF

echo "[6/6] drift guard (sync_check.py)..."
"${PY[@]}" sync_check.py || fail "sync_check.py reported drift"

echo
echo "ALL CHECKS PASSED"
