# Releasing — launch paths for end users

macOS 15 Sequoia removed the right-click → Open Gatekeeper bypass, so a
downloaded, unsigned `.command` can no longer be opened with a simple
double-click. The user has to go to System Settings → Privacy & Security →
Open Anyway. There are three ways to hand the tool to users.

## Path A — curl one-liner (recommended; no Apple account)

Users paste one line into Terminal:

```
curl -fsSL https://raw.githubusercontent.com/flywifi/whoshe/main/imessage_ultimate_launcher.command | bash
```

- **No Gatekeeper step.** `curl` doesn't set the `com.apple.quarantine` flag
  (only browsers and other quarantine-aware apps do), and the script is piped
  straight to `bash`, so it never exists as a blocked file. There is no
  "unidentified developer" dialog, no `chmod`, no `xattr`, and no Open Anyway.
- **Truncation-safe.** The whole launcher is one `main()` function called on
  the last line. If the download is cut off, bash hits a syntax error and runs
  nothing.
- **Stdin-safe.** Nothing in the launcher reads the script's stdin. The menu
  reads from `/dev/tty`.

What the user still sees on a first run:
- Apple's Command Line Developer Tools install, if the Mac has no Python 3.
  That is one Apple dialog and a 5-30 minute download.
- The Full Disk Access switch for Terminal, for Fresh Extraction only.

Caveats:
- **The URL serves whatever is on `main`.** Changes on other branches only
  reach users after they're merged. Anyone who can push to `main` controls
  what users run. For a fixed, reviewable version, cut a release tag and
  replace `main` in the URL with the tag name.
- If the URL fails (404, offline), `curl -f` prints one error line and runs
  nothing.

## Path B — downloaded zip, double-click

```
python3 build.py
```

This produces `imessage-forensic-v<version>-<sha>.zip`, which contains an
`imessage-forensic/` folder with the launcher, README.md and LICENSE.
`build.py` packages the **committed** files and sets LF line endings and Unix
mode bits, so the zip is correct even when built on Windows. It does not
include uncommitted edits.

Users still have to clear Gatekeeper once. On Sequoia that means either running
the `xattr`/`chmod` line from README Option B, or double-clicking, then going to
System Settings → Privacy & Security → Open Anyway, then confirming.

Don't re-zip the folder with Windows tools (Explorer "Send to → Compressed
folder", PowerShell `Compress-Archive`). They drop the executable bit.

## Path C — notarized .app (EXPERIMENTAL; requires Apple Developer Program, $99/yr)

`scripts/build_signed_app.sh` builds a `.app` wrapper. It has **never been
built or tested**, and it can only be built on a Mac. Even when it works:
- macOS still shows one "downloaded from the Internet — Open?" confirmation.
- Terminal still needs Full Disk Access.
- The app's main executable is a shell script, a pattern Apple doesn't
  recommend. A compiled stub or Platypus would be more robust.

### One-time setup
1. Enroll in the Apple Developer Program and create a **Developer ID
   Application** certificate (Xcode → Settings → Accounts → Manage
   Certificates).
2. Store notarization credentials in the login keychain:
   ```
   xcrun notarytool store-credentials "whoshe-notary" \
       --apple-id "you@example.com" --team-id "TEAMID" \
       --password "app-specific-password"   # appleid.apple.com → App-Specific Passwords
   ```

### Build
```
SIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)" \
NOTARY_PROFILE="whoshe-notary" \
    ./scripts/build_signed_app.sh
```

The script:
- checks that Apple actually **accepted** the submission (`notarytool` exits 0
  even on rejection)
- staples the ticket
- runs `spctl --assess`

### Before distributing, test on a clean Mac
In a fresh macOS user account with no developer tools:
1. Download the `.app.zip` in Safari.
2. Unzip it and double-click the app.
3. Expect exactly one "Open?" prompt, then Terminal opens and the tool runs.

If Gatekeeper blocks the Terminal step, don't ship Path C.

## Never commit build artifacts

`*.zip`, `*.app/`, `*.app.zip` and `*.dmg` are gitignored. Push code, and ship
the built artifact out-of-band (or attach it to a GitHub Release).
