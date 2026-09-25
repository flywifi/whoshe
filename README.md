# iMessage Forensic Recovery Toolkit

A self-contained Mac tool that extracts, analyzes, and presents your iMessage
history — including messages that may have been deleted — in a searchable HTML
report. No coding required.

---

## Quick Start

Open **Terminal** (press ⌘ + Space, type `Terminal`, press Return), then paste
this line and press Return:

```
curl -fsSL https://raw.githubusercontent.com/flywifi/whoshe/main/imessage_ultimate_launcher.command | bash
```

The tool asks which mode you want (type a number and press Return; just press
Return for a Fresh Extraction), then guides you with dialogs.

The first run can include two one-time steps:

1. **Python.** If your Mac doesn't have Python 3 yet, the tool asks Apple to
   install its free "Command Line Developer Tools". You click **Install** in
   Apple's window, and the download takes 5–30 minutes.
2. **Full Disk Access.** For a Fresh Extraction you switch on Terminal in System
   Settings so the tool can read your Messages
   ([details](#4-granting-full-disk-access)).

**Why a Terminal line instead of double-clicking?** On macOS 15 Sequoia, Apple
removed the right-click → Open shortcut, so double-clicking a downloaded tool
that isn't signed by an Apple-registered developer means approving it through
System Settings. The line above avoids that: nothing is saved as a blocked file,
so there is no "unidentified developer" warning, no `chmod`, and no
"Open Anyway". See [Installation](#3-installation--first-launch) for the
double-click alternative.

> The line always runs the version currently published on this repository's
> `main` branch.

---

## Table of Contents

- [Quick Start](#quick-start)
1. [What This Tool Does](#1-what-this-tool-does)
2. [System Requirements](#2-system-requirements)
3. [Installation — First Launch](#3-installation--first-launch)
4. [Granting Full Disk Access](#4-granting-full-disk-access)
5. [The Four Modes](#5-the-four-modes)
6. [Understanding Your Report](#6-understanding-your-report)
7. [Output Folder Contents](#7-output-folder-contents)
8. [Troubleshooting FAQ](#8-troubleshooting-faq)
   - [8a. Upgrading / Fixing a Stuck Install](#8a-upgrading--fixing-a-stuck-install)
9. [Privacy & Security](#9-privacy--security)
10. [Re-running After Tool Updates](#10-re-running-after-tool-updates)
11. [Known Limitations](#11-known-limitations)
12. [For Developers](#12-for-developers)

---

## 1. What This Tool Does

iMessage Forensic Recovery reads your Mac's Messages database (`chat.db`) and
produces a searchable, self-contained HTML report containing:

- **Every message** in your iMessage/SMS history, organized by contact and date
- **Deletion indicators** (tombstones) — records flagged as removed by the system
- **Recovered fragments** from the write-ahead log (WAL) — partial text that may
  survive even after a message is deleted
- **iCloud sync status** for each message (synced, local-only, or deleted from cloud)

Everything runs locally on your Mac. The tool never uploads your messages
(see [Privacy & Security](#9-privacy--security) for iCloud Desktop sync).

---

## 2. System Requirements

| Requirement | Details |
|---|---|
| Mac operating system | macOS 12 Monterey or later (Intel or Apple Silicon) |
| Internet connection | Needed on the first run for one-time setup, and each time you start the tool with the one-line command (it downloads the tool itself) |
| Disk space | A few MB for the tool; Apple's Command Line Developer Tools take up to a few GB if they need installing; output varies by message history size |
| iMessage account | Must have Messages app with a history on this Mac |

You don't install anything yourself and need no coding skills. If Python 3 is
missing, the tool asks Apple's own installer to add it (see
[First-Time Setup](#first-time-setup-only-if-needed)).

---

## 3. Installation — First Launch

There are two ways to launch the tool. **The one-line method (A) is
recommended.** It has fewer steps and skips macOS's "unidentified developer"
block entirely.

### Option A — One line in Terminal (recommended)

1. Press **⌘ + Space**, type `Terminal`, press **Return**
2. Paste this line and press **Return**:

```
curl -fsSL https://raw.githubusercontent.com/flywifi/whoshe/main/imessage_ultimate_launcher.command | bash
```

There is no file to download or unblock. The tool starts right away. This works
because Gatekeeper only checks files that a browser (or similar app) downloaded
and flagged, and this command never creates such a file. To run the tool again
later, paste the same line again.

### Option B — Download and double-click

If you prefer a file you can double-click:

1. Get the launcher. If you received a zip, double-click it to unzip; the
   launcher is inside the `imessage-forensic` folder.
2. **Unlock it once.** macOS blocks files downloaded from the internet. Open
   Terminal, paste this line, and press **Return**:

   ```
   f=~/Downloads/imessage-forensic/imessage_ultimate_launcher.command; chmod +x "$f" && xattr -c "$f"
   ```

   If the launcher is somewhere else, change the path after `f=`. Or type `f=`,
   drag the launcher from Finder into the Terminal window, then type the rest
   starting from the semicolon.
3. Double-click `imessage_ultimate_launcher.command`. Future double-clicks work
   directly.

> **Without Terminal:** double-click the launcher, click **Done** on the
> warning, then open System Settings → Privacy & Security, scroll down, click
> **Open Anyway**, enter your Mac password, and confirm **Open**. (macOS 15
> removed the old right-click → Open shortcut.)

> **Signed app (experimental):** a notarized `.app` wrapper can be built with an
> Apple Developer account. It has not been tested yet, and it would still show
> one confirmation prompt and still need Full Disk Access. See
> [`scripts/RELEASING.md`](scripts/RELEASING.md).

### First-Time Setup (only if needed)

- **Python 3.** If your Mac already has Python 3 (for example from Apple's
  developer tools, Homebrew or python.org), nothing is installed. If not, a
  dialog explains that Python comes with Apple's free **Command Line Developer
  Tools**. Click **Continue**, then **Install** and **Agree** in Apple's window,
  and enter your Mac password if asked. The download takes 5–30 minutes. Leave
  the Terminal window open; the tool continues by itself when it finishes.
- **Excel export support.** The tool then installs one small Python package
  (`openpyxl`, for the `.xlsx` files) into its own private folder. If that fails
  (for example, you're offline), the tool still works; only the Excel files are
  skipped.

Both happen once. Later runs go straight to the mode menu.

---

## 4. Granting Full Disk Access

To read your Messages database (Fresh Extraction only), Terminal needs Full
Disk Access. The tool detects if this is missing and walks you through it:

1. A dialog explains the requirement. Click **Open Settings**; System
   Settings opens on the right page.
2. Find **Terminal** in the list.
   - If it isn't listed, click **+**, go to **Applications → Utilities**,
     select **Terminal** and click **Open**.
3. Switch it **ON**. macOS may ask for your Mac password.
4. macOS may then offer to **Quit & Reopen** Terminal. Click **Later**. The
   tool keeps checking and continues by itself within a few seconds.
5. If Terminal did quit, open it again and run the tool again (paste the same
   line, or double-click the launcher). The permission is remembered, so it
   goes straight through.

> **Using iTerm, Warp, VS Code or another terminal app?** Give Full Disk Access
> to *that* app instead. The tool's dialog names the app it detected.

> **Where the setting is:** macOS 13 and later: System Settings → Privacy &
> Security → Full Disk Access. macOS 12: System Preferences → Security &
> Privacy → Privacy → Full Disk Access (click the lock first).

> **Privacy tip:** once your extraction is done, you can switch Full Disk
> Access back off. Any other command run in Terminal while it's on can read
> the same protected files.

---

## 5. The Four Modes

When you launch the tool, it asks which mode to use. Choose based on what you
want to do:

### 🔍 Fresh Extraction

**Use when:** This is your first time running the tool, you want to capture the
latest messages, or you're running on a new Mac.

What it does:
- Reads your Messages database
- Carves the write-ahead log for deleted fragments
- Probes CloudKit sync tables
- Parses messages into a structured timeline
- Generates the HTML report
- Saves everything to `iMsgForensic_YYYY-MM-DD_HHMMSS/` on your Desktop

The whole process takes 30 seconds to a few minutes depending on your message
history size.

### 📂 Re-analyze a Folder

**Use when:** You already have an extraction folder and want to regenerate the
report — for example, after the tool has been updated with new features.

What it does:
- You pick an existing `iMsgForensic_` or `Recovery_` folder using a Finder dialog
- The tool upgrades the folder format if needed (old extractions from earlier
  versions are automatically converted)
- Regenerates the HTML report from the saved data

No new data is read from your Messages app — this works entirely from the files
already on your Desktop.

### 🔧 Scan & Repair

**Use when:** You have multiple old extraction folders, some may be incomplete or
from an older version, and you want to bring them all up to date at once.

What it does:
- Scans your Desktop for all `iMsgForensic_`, `Recovery_`, and stray extraction
  folders
- Shows a list so you can choose which ones to process
- Upgrades each selected folder (renames old-format folders, converts files,
  re-exports from the raw database if needed)
- Regenerates reports for all selected folders
- Opens the most recent report when done

### 📱 Import from Other Apps

**Use when:** You want to include messages from WhatsApp, Signal, Instagram,
Snapchat, Telegram, Facebook Messenger, or Google Messages in your analysis.

What it does:
- Automatically detects Signal and WhatsApp Desktop if they are installed on
  your Mac
- For apps with no local database (Instagram, Snapchat, Facebook Messenger,
  Telegram, Google Messages), the tool shows you step-by-step instructions for
  downloading your own data from each platform's website
- You place the downloaded export files in a designated folder on your Desktop
  (`MessageExports/`)
- The tool processes all selected sources into a separate
  `iMsgForensic_MultiPlatform_YYYY-MM-DD_HHMMSS/` folder with its own report.
  This report contains only the imported apps, not your iMessage history (use
  Fresh Extraction for that).

**Which apps store data locally on your Mac:**

| App | Local data on Mac? | How to extract |
|---|---|---|
| iMessage / SMS | ✓ Yes | Fresh Extraction (automatic) |
| Signal Desktop | ✓ Yes (encrypted) | Auto-extracted if Signal is installed |
| WhatsApp Desktop | ✓ Yes (may be encrypted) | Auto-extracted if WhatsApp is installed |
| Telegram | ✗ No local DB | In-app export → JSON → drop in folder |
| Instagram DMs | ✗ No Mac app | Meta data download → ZIP → drop in folder |
| Facebook Messenger | ✗ No Mac app | Meta data download → ZIP → drop in folder |
| Snapchat | ✗ No Mac app | Snapchat My Data → ZIP → drop in folder |
| Google Messages | ✗ No Mac app | Google Takeout → ZIP → drop in folder |

**Platform export instructions** (the tool shows these automatically when you
select a platform, but here's a quick reference):

- **Instagram / Facebook:** Go to [accountscenter.instagram.com](https://accountscenter.instagram.com/info_and_permissions/dyi/) or [facebook.com/dyi](https://www.facebook.com/dyi) → Request a copy → choose JSON format → download the ZIP when ready
- **Snapchat:** Go to [accounts.snapchat.com](https://accounts.snapchat.com) → My Data → Submit Request → download ZIP from email link
- **Telegram:** In Telegram Desktop → Settings → Advanced → Export Telegram Data → select JSON format
- **Google Messages:** Go to [takeout.google.com](https://takeout.google.com) → select Messages only → download ZIP

> **Note on Snapchat:** Only messages that were explicitly saved by you or the
> other person appear in the export. Ephemeral Snaps that were not saved cannot
> be recovered — this is a Snapchat design limitation, not a tool limitation.

---

## 6. Understanding Your Report

The HTML report opens in your browser and has three tabs plus a contact sidebar.

### Timeline Tab

All recovered messages, newest to oldest (sortable by any column).

| Column | Meaning |
|---|---|
| Timestamp | Date and time the message was sent/received |
| Contact | Phone number or email; "Me" = sent by you |
| Message | The message text; 📎 = has an attachment |
| Thread | The conversation this message belongs to |
| Platform | Source app badge (🍎 iMessage, 💚 WhatsApp, 🔵 Signal, 📸 Instagram, etc.) |
| Cloud Status | Badge showing iCloud sync state (see below; iMessage only) |

**Row colors:**
- Normal background = standard message
- Dark red tint = message deleted from iCloud (`ICLOUD_DELETED`)
- Dark purple tint = tombstone (deletion indicator — see Tombstones tab)

### Tombstones Tab

Messages that the system has flagged as deleted or errored. A tombstone does not
guarantee the message was deleted — it means the database has a record with a
deletion marker. The "Deletion Indicator" column shows why the record was flagged.

### WAL Fragments Tab

Text fragments rescued from the write-ahead log — pieces of messages that may
still be present on disk even after deletion. These are best-effort recoveries:
fragments may be incomplete, out of order, or from unrelated SQLite operations.

### Contact Sidebar

Click any contact to filter all three tabs to just that person's messages.

### Badges

| Badge | Meaning |
|---|---|
| `ICLOUD_SYNCED` | Message exists in iCloud |
| `ICLOUD_DELETED` | Message was deleted from iCloud sync |
| `LOCAL_ONLY` | Message exists only on this device, not synced |
| `LOCAL_DELETED` | Message deleted locally but may remain in iCloud |
| `✕ Tombstone` | Database deletion marker present |
| `⚑ URL` | Message contains a web link |
| `⚑ Script` | Message contains script-like content — treat with caution |
| `⚑ Prompt-injection` | Message may contain text designed to manipulate AI review |
| `⚑ Base64` | Message contains long encoded data |

**⚑ Risk flags** are informational — they flag content that a forensic reviewer
or AI assistant should treat carefully, not content that is necessarily malicious.

### Filters

Use the **Search**, **Contact**, **Since**, **Until**, and **Platform** controls
at the top to narrow the visible rows. The Platform filter only appears when
messages from multiple apps are present. Filters apply to whichever tab is active.

---

## 7. Output Folder Contents

Each Fresh Extraction creates a folder on your Desktop named:

```
iMsgForensic_YYYY-MM-DD_HHMMSS/
```

Inside:

```
iMsgForensic_2024-03-15_142037/
├── raw_artifacts/
│   ├── chat.db               ← copy of your Messages database (read-only safe copy)
│   ├── chat.db-wal           ← write-ahead log (source of WAL fragments)
│   ├── chat.db-shm           ← shared memory file
│   └── MANIFEST.json         ← SHA-256 hashes + extraction metadata (chain of custody)
├── export_raw.json           ← all messages as structured JSON
├── export.csv                ← all messages as CSV (opens in Excel/Numbers)
├── wal_raw_dump.json         ← raw WAL carve results
├── cloudkit_probe.json       ← raw CloudKit table data
├── cloudkit_classification.json  ← iCloud sync status per message
└── parsed_output/
    ├── parsed_messages.csv   ← cleaned, timestamped message list
    ├── tombstones.csv        ← deletion indicator records
    ├── wal_candidates.json   ← filtered WAL fragments with contact references
    └── report.html           ← the interactive HTML report ← open this
```

**The file to open is `parsed_output/report.html`.** The tool opens it for you
automatically when it finishes.

---

## 8. Troubleshooting FAQ

### "The tool seems stuck, waiting for developer tools."

This is Apple's Command Line Developer Tools downloading (5–30 minutes,
sometimes longer on slow connections). Apple's own window shows the progress.
Leave the Terminal window open; the tool continues when the install finishes.
If you closed Apple's window or clicked Cancel, the tool offers **Start Again**
every 10 minutes.

### "I pasted the command and nothing happened (or I saw `curl: (22)` / `curl: (6)`)."

The download didn't work. Check your internet connection and that you copied
the whole line, then paste it again. `curl: (22)` means the address wasn't
found. `curl: (6)` means there is no internet connection.

### "It won't open — 'unidentified developer' / 'Apple could not verify it is free of malware'."

This is macOS Gatekeeper blocking a downloaded file. On macOS 15 Sequoia the old
right-click → Open shortcut no longer works. **Easiest fix: use the one-line
Terminal command in [Quick Start](#quick-start) instead.** It never creates a
blocked file.

To keep using the downloaded file, run the unlock line in
[Option B](#option-b--download-and-double-click), then double-click again.

### "I double-clicked it and it opened in TextEdit (or said 'permission denied')."

The file lost its executable permission. This is common after the file was
zipped with Windows tools or passed through email or chat apps. Either use the
[one-line command](#quick-start), which doesn't need that permission, or run
the unlock line in [Option B](#option-b--download-and-double-click).

### "It asks for Full Disk Access. I don't see Terminal in the list."

1. In System Settings → Privacy & Security → Full Disk Access, click the **+** button
2. A Finder dialog opens. Go to **Applications → Utilities**
3. Select **Terminal** and click **Open**
4. Switch it **ON**
5. If macOS offers **Quit & Reopen**, click **Later**; the tool continues by
   itself. If Terminal quit anyway, run the tool again.

If you run the tool from iTerm, Warp or another terminal app, add that app
instead; the dialog names the app it detected.

### "It says 'No Messages database found'."

There is no Messages history on this Mac (`~/Library/Messages/chat.db` doesn't
exist). Open the Messages app, sign in with your Apple ID, let it finish
syncing, then run the tool again.

### "It says 'Couldn't read the Messages database'."

Full Disk Access is on, but the database didn't open. The dialog shows the
error. Quit the Messages app completely (⌘Q) and run the tool again. On a Mac
managed by an employer or school, a management profile can block access. Ask
your IT department.

### "My report is empty / shows no messages."

Possible causes:
- **Wrong folder selected** (Re-analyze mode): make sure you selected an
  `iMsgForensic_` folder, not a folder inside it.
- **No iMessage history on this Mac**: if you've never used Messages on this Mac,
  there's nothing to extract. If you recently restored from a backup, the database
  may be empty until Messages syncs.
- **Messages app not set up**: open the Messages app and confirm you're signed in
  with your Apple ID.

### "I already ran Fresh Extraction. Do I need to run it again to get new messages?"

Yes — the tool takes a snapshot at the time it runs. To capture messages received
after the last extraction, run Fresh Extraction again (it creates a new folder).

To regenerate the report without re-reading your Messages app, use
**Re-analyze a Folder** instead.

### "Can I use this on a Messages backup from a different device?"

Yes. Use **Re-analyze a Folder** and select any folder that contains an
`export.csv`, `export_raw.json`, or a `raw_artifacts/chat.db` from another
device. Old-format `Recovery_` folders from earlier tool versions are also
supported.

### "The report says 'X tombstones' — does that mean those messages were deleted?"

Not necessarily. Tombstones are records that the database has marked with a
deletion indicator — empty message bodies, error codes, or `is_empty=1` flags.
Some of these are genuinely deleted messages; others are system records or
attachment-only messages. Treat tombstones as evidence to investigate further,
not as proof of deletion.

### "Is there a Windows version?"

No. This tool is macOS-only. The Messages database format (`chat.db`) is unique
to macOS and iOS backups, and the tool uses macOS-native APIs (AppleScript,
Full Disk Access, iCloud tables) that do not exist on other platforms.

### "There are no Excel (.xlsx) files in my output."

Excel export needs the `openpyxl` package, which the tool installs on first run.
If that install failed (for example, you were offline), the tool skips the
Excel files. The HTML report and CSV files are unaffected. To retry, delete the
tool's private Python folder and run the tool again while online:
```
rm -rf ~/.imessage_forensic_sandbox
```

### "I keep getting the same crash even after downloading a new version."

The one-line command always fetches the latest version, so this only affects
downloaded copies. macOS creates numbered copies of extracted folders
(`imessage-forensic`, `imessage-forensic 2`, `imessage-forensic 3`, etc.)
when you extract zips more than once, and you end up double-clicking an old
copy of the launcher.

**Quick fix** — paste this in Terminal:

```bash
rm -rf ~/Downloads/imessage-forensic*/ ~/Desktop/imessage-forensic*/
rm -f ~/.imsg_*.py
rm -rf ~/.imessage_forensic_sandbox
```

Your recovered data (`iMsgForensic_*` folders) will NOT be deleted — those have
a different name and location.

Then extract the latest zip fresh and double-click the `.command` file. The
**first line of output** should read:

```
  iMessage Forensic Recovery v10.1 (build 2026-09-25)
```

If that line does **not** appear before any error, you are still running an old
copy. Delete it and use the newly extracted one.

---

## 8a. Upgrading / Fixing a Stuck Install

The tool rebuilds its private Python folder by itself whenever the tool version
or your Python changes, so a reset is rarely needed. If an install still seems
stuck, paste this block into Terminal. It removes old copies of the tool and
its private Python folder, and never touches your recovered data:

```bash
# Safe cleanup — preserves your recovered data
echo "Removing stale tool folders..."
rm -rf ~/Downloads/imessage-forensic*/ ~/Desktop/imessage-forensic*/
echo "Removing cached helper scripts..."
rm -f ~/.imsg_*.py
echo "Removing old Python sandbox (will rebuild fresh on next run)..."
rm -rf ~/.imessage_forensic_sandbox
echo ""
echo "Checking your data folders are intact:"
ls ~/Desktop/iMsgForensic_* 2>/dev/null && echo "  Data folders preserved above." || echo "  (No data folders found.)"
echo "Done."
```

(Developers: `RESET.command` in this repository does the same thing. It is not
included in the user zip, because it deletes the `imessage-forensic` folder it
would be sitting in.)

### After the reset

- **One-line command:** just paste it again. It always runs the latest version.
- **Zip:**
  1. Unzip the newest zip. Delete any existing `imessage-forensic*` folders in
     Downloads first.
  2. Check that the unzipped folder is named exactly `imessage-forensic` (not
     `imessage-forensic 2` or similar, which means an old copy is still around).
  3. Unlock and double-click `imessage_ultimate_launcher.command` as in
     [Option B](#option-b--download-and-double-click).
  4. Confirm the first line printed says `iMessage Forensic Recovery v10.1`.

---

## 9. Privacy & Security

**What the tool reads:**
- Your Messages database (`~/Library/Messages/chat.db` and associated files)
- iCloud sync tables within that database
- Optionally: iPhone/iPad backup databases under `~/Library/Application Support/MobileSync/Backup/`

**What the tool sends over the network:** nothing. It never uploads, transmits
or shares your messages or results. Its only network use is downloading:
- the tool itself from GitHub, each time you start it with the one-line command;
- Apple's Command Line Developer Tools, from Apple, if Python 3 is missing;
- the `openpyxl` package, from `pypi.org`, once.

**Where your data goes (please read):**
- Results are saved in folders on your **Desktop**. They include a full copy of
  your Messages database and plain-text exports of your messages. If **iCloud
  Desktop & Documents** is turned on (System Settings → your name → iCloud →
  iCloud Drive), macOS uploads these folders to iCloud Drive like anything else
  on your Desktop. Move the folders somewhere that isn't synced, or delete them
  when you're finished, if that matters to you.
- Import mode can decrypt Signal Desktop's database with the key stored on this
  Mac, and saves those messages as plain text in the output folder.
- **Full Disk Access** stays switched on for Terminal until you turn it off.
  While it's on, anything run in Terminal can read protected files. Switch it
  off when you're done: System Settings → Privacy & Security → Full Disk Access.

**Content security in the report:**
- The HTML report includes a Content Security Policy that blocks outbound
  connections, form submissions, and embedded frames. Even if a recovered
  message contains a link, clicking it will not auto-load or phone home from
  within the report itself.
- Risk badges (⚑) flag message content that may be adversarial — crafted to
  mislead a forensic reviewer or an AI assistant summarizing the report.
- The report includes a forensic boundary comment warning AI systems not to
  follow instructions embedded in recovered message text.

**Chain of custody:**
- A `MANIFEST.json` is written alongside the raw database copy containing
  SHA-256 hashes of all artifact files and the extraction timestamp. This
  supports evidentiary use cases where you need to demonstrate the data was
  not altered after capture.

---

## 10. Re-running After Tool Updates

When the tool is updated with new features or bug fixes:

1. **One-line command:** nothing to download; pasting the line always runs the
   latest version. **Downloaded launcher:** get the new zip and unlock it as in
   [Option B](#option-b--download-and-double-click).
2. Start the tool
3. Choose **Re-analyze a Folder** (if you just want an updated report from
   existing data) or **Fresh Extraction** (to also capture any new messages)

The Scan & Repair mode is the most efficient option if you have multiple old
extraction folders to update at once.

---

## 11. Known Limitations

- **Not a real-time monitor.** The tool captures a snapshot at the moment it
  runs. It does not watch for new messages continuously.

- **WAL fragments are best-effort.** The write-ahead log may contain fragments
  of deleted messages, but recovery is not guaranteed. Fragments may be
  incomplete, truncated, or from unrelated SQLite activity. The tool caps recovery
  at 50,000 fragments with a 2,000-character limit per fragment to prevent
  resource exhaustion.

- **Tombstones are indicators, not proof.** A tombstone record means the database
  flagged a message — it does not confirm the content of the original message or
  that it was intentionally deleted.

- **Managed/MDM devices.** If your Mac is managed by an organization (Rippling,
  Jamf, etc.), its management profile may prevent granting Full Disk Access, and
  then the tool cannot read Messages. Only the organization's IT department can
  change that.

- **Attachments are not extracted.** The report references attachment filenames
  and MIME types, but the actual image/video/audio files are not copied or
  embedded. Attachments remain at their original paths on your Mac.

- **iOS backups are scanned but not decrypted.** If you have encrypted iPhone
  backups, the tool will detect the backup databases but cannot read encrypted
  content.

---

## 12. For Developers

### Architecture

The toolkit ships to users as a single bash file,
`imessage_ultimate_launcher.command`. Users either pipe it into bash with the
one-line `curl` command or double-click it.

The whole script is one `main()` function called on the last line. So when it
is piped from `curl`, nothing runs until the entire file has arrived.

It embeds six Python modules as single-quoted heredocs. At runtime it writes
them into a private per-run temp directory (`mktemp -d`, mode 0700) and runs
them with the Python it found. An `EXIT` trap deletes the directory afterwards.

| Heredoc marker | Written to (`$TMPDIR_RUN/`) | Purpose | Standalone counterpart |
|---|---|---|---|
| `CORE_PY_EOF` | `imsg_core.py` | DB copy, WAL carving, backup scan, CSV/JSON/XLSX export | `core.py` (partial overlap) |
| `CK_PY_EOF` | `imsg_cloudkit.py` | CloudKit sync-status classification | `cloudkit.py` (partial overlap) |
| `PARSER_PY_EOF` | `imsg_parser.py` | Message parsing, tombstones, WAL cross-reference + attribution | `parser.py` + `extractors/attribution.py` |
| `REPORT_PY_EOF` | `imsg_report.py` | Self-contained HTML report | `report.py` |
| `REORG_PY_EOF` | `imsg_reorganize.py` | Scan / validate / upgrade extraction folders | none |
| `PLATFORM_PY_EOF` | `imsg_platform_import.py` | Import from Signal, WhatsApp, Meta, Snapchat, Telegram, Google Messages | `extractors/*.py` (partial overlap) |

The standalone scripts in the repository root are **separate command-line
tools**, not exact copies of the heredocs. They share the security-relevant
code, which `sync_check.py` checks, but differ in features and some logic.
`merge.py` (multi-device merge) exists only as a standalone tool. The launcher
never imports the `extractors/` package; the `PLATFORM_PY_EOF` heredoc carries
its own copy of that logic.

| File | Purpose |
|---|---|
| `extractors/attribution.py` | Platform attribution engine — weighted regex scoring → per-platform confidence (0.40 threshold) |
| `extractors/recursive_search.py` | iOS MobileSync `Manifest.db` scan for third-party app databases |
| `extractors/signal_desktop.py` | Signal Desktop reader (decrypts with the key in Signal's `config.json` when available, writes plaintext) |
| `extractors/whatsapp_desktop.py` | WhatsApp Desktop reader |
| `extractors/meta_import.py` | Instagram / Facebook Messenger data-export ZIP importer |
| `extractors/snapchat_import.py` | Snapchat "My Data" ZIP importer |
| `extractors/telegram_import.py` | Telegram export importer |
| `extractors/google_messages_import.py` | Google Takeout Messages importer |
| `extractors/normalize.py` | Normalize any platform schema → common columns |

### Two-Copy Architecture and Drift Guard

Because the security-relevant code exists twice (standalone + embedded),
security fixes must be applied in both places. A drift guard checks the listed
invariants:

```bash
python3 sync_check.py
```

This script asserts ten invariants across both copies:

| # | Invariant | Checked in |
|---|---|---|
| 1 | Formula-injection guard defined (`_FORMULA_PFX`, `def _safe`) | `core.py`, `parser.py`, `merge.py` + CORE/PARSER/REORG heredocs |
| 2 | Formula-injection guard applied (≥2 call sites of `_safe(`) | same as #1 |
| 3 | SQLite table names SQL-quoted in CloudKit probe | `core.py` + CORE heredoc |
| 4 | WAL carving has count + length caps (`50_000`, `2_000`) | `core.py` + CORE heredoc |
| 5 | Symlink artifacts logged (`is_symlink`) | `core.py` + CORE heredoc |
| 6 | Report ships CSP + FORENSIC BOUNDARY comment + sec-banner + risk flags | `report.py` + REPORT heredoc |
| 7 | WAL attribution engine present (threshold + `top_platform`) | `extractors/attribution.py` + PARSER heredoc |
| 8 | Platform-organized report sections (`platform_section`) | `report.py` + REPORT heredoc |
| 9 | Misc/unattributed tab for unclaimed fragments | `report.py` + REPORT heredoc |
| 10 | Attribution confidence badge (`conf-badge`) in report | `report.py` + REPORT heredoc |

Invariants 1–6 are the original security hardening; 7–10 were added with the
platform-attribution feature.

Exit code 0 = all pass. Exit code 1 = drift detected with a report showing which
invariant failed in which file. Run this after every security-relevant change.

### Adding a New Security Invariant

1. Add a tuple to the `INVARIANTS` list in `sync_check.py`:
   ```python
   ("description of invariant", has(r"pattern_to_find"), [
       "standalone_file.py", "launcher:HEREDOC_MARKER",
   ]),
   ```
2. Implement the fix in both the standalone `.py` and the launcher heredoc.
3. Re-run `python3 sync_check.py` to confirm both copies pass.

### Standalone CLI Usage

The standalone scripts need Python 3.10 or later. The launcher's embedded
modules also run on Apple's Python 3.9.

```bash
# Extract (takes no arguments: reads ~/Library/Messages/chat.db and writes
# ~/Desktop/iMsgForensic_<timestamp>/; needs Full Disk Access)
python3 core.py

# Classify CloudKit sync status
python3 cloudkit.py --input ~/Desktop/iMsgForensic_<timestamp>

# Parse into a timeline (optional filters: --contact, --since, --until, --keyword)
python3 parser.py --input ~/Desktop/iMsgForensic_<timestamp>

# Generate the HTML report
python3 report.py --input ~/Desktop/iMsgForensic_<timestamp>/parsed_output \
                  --cloudkit ~/Desktop/iMsgForensic_<timestamp>/cloudkit_classification.json

# Merge several extractions (multi-device)
python3 merge.py --inputs /path/to/device1 /path/to/device2 --output /path/to/merged
python3 merge.py --scan ~/Desktop            # or find iMsgForensic_* folders automatically
```

Each script has `--help`.

### Repository Layout

```
.
├── imessage_ultimate_launcher.command   # the tool users run (bash + 6 embedded Python modules), mode 100755
├── RESET.command                        # cleanup helper for developers, mode 100755 (not in the user zip)
├── core.py  cloudkit.py  parser.py  report.py  merge.py   # standalone CLI tools
├── sync_check.py                        # drift guard (see above)
├── extractors/                          # standalone multi-platform readers/importers
├── verify.sh                            # pre-commit check suite
├── build.py                             # builds the user zip from the HEAD commit
├── scripts/                             # experimental signed-.app build + RELEASING.md
├── README.md  LICENSE
└── .gitattributes  .gitignore           # LF line endings enforced; build outputs ignored
```

**Windows hazards.** `.gitattributes` forces LF line endings, which matters
because a CRLF launcher fails on macOS with `/bin/bash^M: bad interpreter`. Both
`.command` files must stay mode `100755` in git. Editing a tracked file on
Windows keeps the mode. It gets lost when a file is added fresh, for example
through a GitHub web upload or deleting and re-adding it. Check and restore it
with:

```bash
git ls-files --stage *.command   # expect 100755 on both
git update-index --chmod=+x imessage_ultimate_launcher.command RESET.command
```

### Verifying a Change

Before you commit, run from the repo root:

```bash
./verify.sh
```

It aborts on the first failure of:

1. `bash -n imessage_ultimate_launcher.command` — launcher bash is valid
2. the embedded Python heredocs parse (`CORE/PARSER/REPORT/REORG/CK` markers)
3. the main standalone modules parse (`core.py parser.py report.py merge.py cloudkit.py sync_check.py`)
4. `python3 sync_check.py` — the drift guard's 10 invariants

**Not yet covered:** the `PLATFORM_PY_EOF` heredoc, `extractors/*.py`,
`RESET.command`, `scripts/*.sh`, line endings, and file modes. On Windows
(git-bash), run it as `PYTHONUTF8=1 ./verify.sh`, and make sure `python3` is a
real Python rather than the Microsoft Store shortcut.

`sync_check.py` only checks the listed security invariants. It does not detect
other logic drift between a standalone script and its heredoc. Keeping those in
step is a manual job.

### Building a Release

```bash
python3 build.py          # user zip: launcher + README + LICENSE
python3 build.py --full   # every tracked file (developer bundle)
```

This packages the files from the **HEAD commit**, not your working tree.
Uncommitted edits are left out, and the build warns about them. Every entry sits
under an `imessage-forensic/` folder. It is marked as a Unix entry with mode
0755 for `.command` files, so the launcher stays executable even when you build
on Windows. The build refuses any text file containing a CR (CRLF) character.
Output: `imessage-forensic-v<version>-<commit>.zip`.

The zip is a **deliverable only**. It is gitignored and must never be committed.
See [`scripts/RELEASING.md`](scripts/RELEASING.md) for the ways to hand the tool
to users.
