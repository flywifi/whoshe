# Releasing — launch paths for end users

macOS 15 Sequoia removed the right-click → Open Gatekeeper bypass, so an
unsigned tool can no longer be launched with a simple double-click. There are
two supported launch paths; pick based on whether you have an Apple Developer
account.

## Path A — Free curl one-liner (no Apple account, works today)

Users paste **one line** into Terminal:

```
curl -fsSL https://raw.githubusercontent.com/flywifi/whoshe/main/imessage_ultimate_launcher.command | bash
```

Why this is the lowest-friction unsigned option:

- **No Gatekeeper.** `curl`/`wget` do not set the `com.apple.quarantine` flag
  (only browsers do), and piping straight to `bash` means the script never lands
  on disk as a quarantined file. No "unidentified developer" block, no
  "Open Anyway" trip through System Settings.
- **No `chmod`, no `xattr`, no TextEdit mistake.** It runs in the Terminal the
  user pasted it into.
- The launcher is already pipe-safe: its only interactive prompt reads from
  `/dev/tty`, so the menu still works under `curl | bash`.

Requirements: the repo must be public (it is) so the raw URL is reachable.
Terminal will need Full Disk Access for Fresh Extraction — the tool prompts for
that automatically.

## Path B — Notarized double-click (.app, requires Apple Developer Program, $99/yr)

This gives a true zero-warning double-click. Build it on a Mac with Xcode tools.

### One-time setup

1. Enroll in the Apple Developer Program and create a **Developer ID
   Application** certificate in Xcode (Settings → Accounts → Manage
   Certificates). Note the identity string, e.g.
   `Developer ID Application: Your Name (TEAMID)`.
2. Store notarization credentials in the keychain (do this once):
   ```
   xcrun notarytool store-credentials "whoshe-notary" \
       --apple-id "you@example.com" \
       --team-id "TEAMID" \
       --password "app-specific-password"   # appleid.apple.com → App-Specific Passwords
   ```
   This writes to your login keychain only — never into the repo.

### Build + sign + notarize + staple

```
SIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)" \
NOTARY_PROFILE="whoshe-notary" \
    ./scripts/build_signed_app.sh
```

Output: `iMessage Forensic Recovery.app.zip` — a stapled, notarized bundle.
Distribute that zip; users unzip and double-click with no warnings. The app is
a thin wrapper that opens Terminal on the bundled launcher (the tool is an
interactive Terminal program, so it needs a TTY).

To build an unsigned bundle for local testing only, run the script with no env
vars set.

## Never commit build artifacts

`*.app`, `*.app.zip`, and the distributable `*.zip` are gitignored. Push code;
ship the built artifact to users out-of-band (or attach it to a GitHub Release).
