#!/bin/bash
# RESET.command — double-click this to clean up stale iMessage Forensic installs.
# Safe to run at any time. Your recovered data (iMsgForensic_* folders) is never touched.

echo ""
echo "  iMessage Forensic Recovery — RESET v10.0"
echo "  ─────────────────────────────────────────"
echo ""
echo "  This removes old tool folders, cached helper scripts, and the"
echo "  Python sandbox so the next launch starts from a clean slate."
echo ""
echo "  Your iMsgForensic_* data folders are NEVER deleted by this script."
echo ""

# ── 1. Remove stale extracted tool folders ────────────────────────────────────
echo "[1/3] Removing stale tool folders..."
removed_dirs=0
for pattern in "$HOME/Downloads/imessage-forensic"*/ "$HOME/Desktop/imessage-forensic"*/; do
    [ -d "$pattern" ] && { rm -rf "$pattern"; removed_dirs=$((removed_dirs + 1)); echo "      removed: $pattern"; }
done
[ "$removed_dirs" -eq 0 ] && echo "      (none found)"

# ── 2. Remove cached helper scripts ──────────────────────────────────────────
echo "[2/3] Removing cached helper scripts (~/.imsg_*.py)..."
removed_py=0
for f in "$HOME"/.imsg_*.py; do
    [ -f "$f" ] && { rm -f "$f"; removed_py=$((removed_py + 1)); echo "      removed: $f"; }
done
[ "$removed_py" -eq 0 ] && echo "      (none found)"

# ── 3. Remove old Python sandbox ─────────────────────────────────────────────
echo "[3/3] Removing Python sandbox (~/.imessage_forensic_sandbox)..."
if [ -d "$HOME/.imessage_forensic_sandbox" ]; then
    rm -rf "$HOME/.imessage_forensic_sandbox"
    echo "      removed."
else
    echo "      (not found)"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "  Done. Stale files cleared."
echo ""
echo "  Your data folders are untouched:"
found_data=0
for d in "$HOME/Desktop/iMsgForensic_"* "$HOME/Desktop/Recovery_"*; do
    [ -d "$d" ] && { echo "    $d"; found_data=1; }
done
[ "$found_data" -eq 0 ] && echo "    (No data folders found — that is fine.)"
echo ""
echo "  Next steps:"
echo "    1. Extract the LATEST zip fresh (delete the old extracted folder first)"
echo "    2. Double-click imessage_ultimate_launcher.command"
echo "    3. The first line of output should say:  iMessage Forensic Recovery v10.0"
echo ""
echo "  This window will close in 10 seconds."
sleep 10
