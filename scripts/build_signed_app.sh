#!/usr/bin/env bash
#
# build_signed_app.sh — EXPERIMENTAL. Wrap the launcher in a double-clickable,
# optionally signed + notarized .app.
#
# STATUS: never built or tested on a Mac. Treat the output as a prototype until
# it has passed the checks in scripts/RELEASING.md on a clean Mac. Even when it
# works, macOS still shows one "downloaded from the Internet — Open?" prompt,
# and Terminal still needs Full Disk Access.
#
# Run on a Mac (needs codesign / xcrun, only present with Xcode or its
# Command Line Tools). The Windows-only workflow cannot produce this.
#
#   ./scripts/build_signed_app.sh            # build only (unsigned, for testing)
#   SIGN_IDENTITY="Developer ID Application: NAME (TEAMID)" \
#   NOTARY_PROFILE="whoshe-notary" \
#       ./scripts/build_signed_app.sh        # build + sign + notarize + staple
#
# Credentials are taken from the environment / keychain ONLY — nothing secret is
# read from or written to the repo. See scripts/RELEASING.md for one-time setup.
# Do not re-zip the result on Windows: that drops the signature's extended
# attributes and the exec bits.
#
set -euo pipefail
cd "$(dirname "$0")/.."   # repo root

APP_NAME="iMessage Forensic Recovery"
APP="${APP_NAME}.app"
LAUNCHER="imessage_ultimate_launcher.command"
BUNDLE_ID="com.flywifi.imessageforensic"

[ -f "$LAUNCHER" ] || { echo "[!] Run from the repo root ($LAUNCHER missing)"; exit 1; }
VERSION="$(sed -n 's/^_TOOL_VERSION="\([^"]*\)".*/\1/p' "$LAUNCHER" | head -1)"
[ -n "$VERSION" ] || { echo "[!] Could not read _TOOL_VERSION from $LAUNCHER"; exit 1; }

echo "[*] Building $APP (v$VERSION) ..."
rm -rf "$APP" "$APP.zip"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
    <key>CFBundleName</key><string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key><string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key><string>${BUNDLE_ID}</string>
    <key>CFBundleVersion</key><string>${VERSION}</string>
    <key>CFBundleShortVersionString</key><string>${VERSION}</string>
    <key>CFBundleExecutable</key><string>run</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>LSMinimumSystemVersion</key><string>12.0</string>
    <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST

cp "$LAUNCHER" "$APP/Contents/Resources/$LAUNCHER"
chmod 755 "$APP/Contents/Resources/$LAUNCHER"

# The tool is an interactive Terminal program, and a GUI .app has no terminal.
# So 'run' copies the launcher OUT of the bundle with `cp -X` (no extended
# attributes, so the copy carries no quarantine flag), then opens that copy in
# Terminal. Opening the bundled file directly would hand Terminal a quarantined
# script, which Gatekeeper can block even inside a notarized app. The copy also
# survives App Translocation, whose temporary path disappears when the app quits.
cat > "$APP/Contents/MacOS/run" <<'RUN'
#!/bin/bash
RES="$(cd "$(dirname "$0")/../Resources" && pwd)"
DEST="$HOME/Library/Application Support/iMessage Forensic Recovery"
COPY="$DEST/imessage_ultimate_launcher.command"
if mkdir -p "$DEST" && cp -X "$RES/imessage_ultimate_launcher.command" "$COPY" \
   && chmod 755 "$COPY" && open -a Terminal "$COPY"; then
    exit 0
fi
osascript -e 'display dialog "iMessage Forensic Recovery could not open Terminal to start the tool." buttons {"OK"} default button "OK" with icon stop' >/dev/null 2>&1
exit 1
RUN
chmod 755 "$APP/Contents/MacOS/run"

echo "[+] Bundle built: $APP"

# ── Sign (optional) ───────────────────────────────────────────────────────────
if [ -n "${SIGN_IDENTITY:-}" ]; then
    echo "[*] Signing with: $SIGN_IDENTITY"
    # Sign the bundle once. Its seal covers Contents/Resources; signing the
    # scripts separately would store fragile signatures in extended attributes.
    codesign --force --options runtime --timestamp --sign "$SIGN_IDENTITY" "$APP"
    codesign --verify --strict --verbose=2 "$APP"
    echo "[+] Signed."
else
    echo "[i] SIGN_IDENTITY not set — built UNSIGNED (fine for local testing only)."
fi

# ── Notarize + staple (optional) ──────────────────────────────────────────────
if [ -n "${NOTARY_PROFILE:-}" ]; then
    [ -n "${SIGN_IDENTITY:-}" ] || { echo "[!] Notarization requires SIGN_IDENTITY too."; exit 1; }
    echo "[*] Submitting for notarization (profile: $NOTARY_PROFILE) ..."
    ditto -c -k --keepParent "$APP" "$APP.zip"
    # notarytool exits 0 even when Apple rejects the submission, so check the
    # status it reports rather than the exit code.
    RESULT="$(xcrun notarytool submit "$APP.zip" --keychain-profile "$NOTARY_PROFILE" --wait --output-format json)"
    echo "$RESULT"
    if ! printf '%s' "$RESULT" | grep -q '"status" *: *"Accepted"'; then
        SUB_ID="$(printf '%s' "$RESULT" | sed -n 's/.*"id" *: *"\([^"]*\)".*/\1/p' | head -1)"
        echo "[!] Notarization was not accepted. See why with:"
        echo "    xcrun notarytool log ${SUB_ID:-<submission-id>} --keychain-profile \"$NOTARY_PROFILE\""
        exit 1
    fi
    echo "[*] Stapling ticket ..."
    xcrun stapler staple "$APP"
    xcrun stapler validate "$APP"
    # Ask Gatekeeper itself; codesign --verify doesn't test Gatekeeper acceptance.
    spctl --assess --type execute --verbose=4 "$APP"
    rm -f "$APP.zip"
    ditto -c -k --keepParent "$APP" "$APP.zip"
    echo "[+] Notarized + stapled + Gatekeeper-assessed. Distribute: $APP.zip"
else
    echo "[i] NOTARY_PROFILE not set — skipped notarization."
fi

echo "[*] Done. Before distributing, run the clean-Mac checks in scripts/RELEASING.md."
