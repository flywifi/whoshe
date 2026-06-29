#!/usr/bin/env bash
#
# verify.sh — one-command integrity check for the iMessage Forensic Toolkit.
#
# Runs the full verification suite before any commit or release:
#   1. launcher bash is syntactically valid
#   2. every embedded Python heredoc parses
#   3. every standalone Python module parses
#   4. the drift guard passes (all security invariants present in BOTH copies)
#
# Exit 0 = everything clean. Any failure aborts immediately (set -e).
# Run from the cloud env or macOS; on Windows use git-bash.
#
set -euo pipefail
cd "$(dirname "$0")"

echo "[1/4] launcher bash syntax..."
bash -n imessage_ultimate_launcher.command
echo "      ok"

echo "[2/4] embedded heredoc Python parses..."
python3 - <<'PYEOF'
import re, ast
t = open("imessage_ultimate_launcher.command", encoding="utf-8").read()
for m in ["CORE_PY_EOF", "PARSER_PY_EOF", "REPORT_PY_EOF", "REORG_PY_EOF", "CK_PY_EOF"]:
    match = re.search(rf"cat\s*<<\s*'{m}'.*?\n(.*?)\n{m}\n", t, re.DOTALL)
    if not match:
        raise SystemExit(f"      FAIL: could not locate heredoc {m}")
    ast.parse(match.group(1))
    print(f"      {m} ok")
PYEOF

echo "[3/4] standalone modules parse..."
python3 -c "import ast;[ast.parse(open(f).read()) for f in ['core.py','parser.py','report.py','merge.py','cloudkit.py','sync_check.py']];print('      ok')"

echo "[4/4] drift guard (sync_check.py)..."
python3 sync_check.py

echo
echo "ALL CHECKS PASSED"
