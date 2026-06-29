#!/usr/bin/env bash
#
# build_signed_app.sh — wrap the launcher in a double-clickable, optionally
# signed + notarized .app so end users get a zero-warning launch on macOS 15
# Sequoia and later (where the right-click → Open Gatekeeper bypass is gone).
#
# Run on a Mac (needs codesign / xcrun, only present in macOS + Xcode tools).
#
#   ./scripts/build_signed_app.sh            # build only (unsigned, for testing)
#   SIGN_IDENTITY="Developer ID Application: NAME (TEAMID)" \
#   NOTARY_PROFILE="whoshe-notary" \
#       ./scripts/build_signed_app.sh        # build + sign + notarize + staple
#
# Credentials are taken from the environment / keychain ONLY — nothing secret is
# read from or written to the repo. See scripts/RELEASING.md for one-time setup.
#
set -euo pipefail
cd "$(dirname "$0")/.."   # repo root

APP_NAME="iMessage Forensic Recovery"
APP="${APP_NAME}.app"
LAUNCHER="imessage_ultimate_launcher.command"
BUNDLE_ID="com.flywifi.imessageforensic"
VERSION="10.0"

[ -f "$LAUNCHER" ] || { echo "[!] Run from the repo root ($LAUNCHER missing)"; exit 1; }

echo "[*] Building $APP ..."
rm -rf "$APP" "$APP.zip"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
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

# The forensic tool is an interactive Terminal program, and a GUI .app has no
# attached TTY. So the bundle's executable simply opens Terminal on the bundled
# launcher. Because the launcher ships inside a notarized, stapled bundle, macOS
# trusts it — no quarantine prompt, no chmod, no xattr dance for the user.
cp "$LAUNCHER" "$APP/Contents/Resources/$LAUNCHER"
chmod +x "$APP/Contents/Resources/$LAUNCHER"

cat > "$APP/Contents/MacOS/run" <<'RUN'
#!/bin/bash
RES="$(cd "$(dirname "$0")/../Resources" && pwd)"
open -a Terminal "$RES/imessage_ultimate_launcher.command"
RUN
chmod +x "$APP/Contents/MacOS/run"

echo "[+] Bundle built: $APP"

# ── Sign (optional) ───────────────────────────────────────────────────────────
if [ -n "${SIGN_IDENTITY:-}" ]; then
    echo "[*] Signing with: $SIGN_IDENTITY"
    # Sign inner items first, then the bundle (no fragile --deep).
    codesign --force --options runtime --timestamp \
        --sign "$SIGN_IDENTITY" "$APP/Contents/Resources/$LAUNCHER"
    codesign --force --options runtime --timestamp \
        --sign "$SIGN_IDENTITY" "$APP/Contents/MacOS/run"
    codesign --force --options runtime --timestamp \
        --sign "$SIGN_IDENTITY" "$APP"
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
    xcrun notarytool submit "$APP.zip" --keychain-profile "$NOTARY_PROFILE" --wait
    echo "[*] Stapling ticket ..."
    xcrun stapler staple "$APP"
    xcrun stapler validate "$APP"
    # Re-zip the stapled app for distribution.
    rm -f "$APP.zip"
    ditto -c -k --keepParent "$APP" "$APP.zip"
    echo "[+] Notarized + stapled. Distribute: $APP.zip"
else
    echo "[i] NOTARY_PROFILE not set — skipped notarization."
fi

echo "[*] Done."
