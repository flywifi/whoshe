# iMessage Forensic Recovery Toolkit

A self-contained Mac tool that extracts, analyzes, and presents your iMessage
history — including messages that may have been deleted — in a searchable HTML
report. Double-click to run. No coding required.

---

## Table of Contents

1. [What This Tool Does](#1-what-this-tool-does)
2. [System Requirements](#2-system-requirements)
3. [Installation — First Launch](#3-installation--first-launch)
4. [Granting Full Disk Access](#4-granting-full-disk-access)
5. [The Four Modes](#5-the-four-modes)
6. [Understanding Your Report](#6-understanding-your-report)
7. [Output Folder Contents](#7-output-folder-contents)
8. [Troubleshooting FAQ](#8-troubleshooting-faq)
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

Everything runs locally on your Mac. Nothing is uploaded anywhere.

---

## 2. System Requirements

| Requirement | Details |
|---|---|
| Mac operating system | macOS 12 Monterey or later |
| Internet connection | Required once (for one-time software install), then optional |
| Disk space | ~200 MB for the tool's software; output varies by message history size |
| iMessage account | Must have Messages app with a history on this Mac |

No Python, no Homebrew, no coding skills required — the tool installs everything
it needs automatically on first run.

---

## 3. Installation — First Launch

### Step 1 — Download

Download `imessage_ultimate_launcher.command` and save it anywhere (your Desktop
is fine).

### Step 2 — Unlock the file (one-time, ~30 seconds)

macOS blocks files downloaded from the internet and also requires them to be
marked executable before they can run. Two Terminal commands handle both at once.

1. Press **⌘ + Space**, type `Terminal`, press **Return**
2. Copy and paste the following line into Terminal, then press **Return**:

```
chmod +x ~/Downloads/imessage_ultimate_launcher.command && xattr -d com.apple.quarantine ~/Downloads/imessage_ultimate_launcher.command
```

> **File not in Downloads?** Drag the file from Finder into the Terminal window
> instead of typing the path — Terminal will fill in the correct path for you.
> Then add `chmod +x ` before it and ` && xattr -d com.apple.quarantine ` after,
> or run each command separately.

3. Double-click `imessage_ultimate_launcher.command` — it will run.

You only need to do this once. After that, double-clicking works directly.

> **macOS 15 Sequoia note:** The old right-click → Open shortcut was removed in
> macOS 15. If you see a warning and clicking Open does nothing, use the Terminal
> commands above — they bypass Gatekeeper entirely and are simpler.

### Step 3 — First-Time Software Install (~3 minutes)

On the very first run, the tool will ask to install **Homebrew** and **Python 3**
(free, open-source software). A dialog will appear before anything installs —
click OK to proceed. The Terminal window will show activity in the background
while it installs.

This only happens once. Future runs skip directly to extraction.

---

## 4. Granting Full Disk Access

To read your Messages database, Terminal needs Full Disk Access permission. The
tool detects if this is missing and walks you through it automatically:

1. A dialog appears explaining the requirement
2. Click **Open Settings** — the tool opens System Settings to the exact page
3. In the list, find **Terminal**
   - If Terminal is not listed: click the **+** button, then navigate to
     **Applications → Utilities → Terminal**
4. Toggle the switch **ON** next to Terminal
5. Switch back to the Terminal window — the tool detects the change and
   **continues automatically** within a few seconds

You do not need to re-launch the tool.

> **Note for macOS 13 and later:** The setting is at  
> System Settings → Privacy & Security → Full Disk Access

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
- The tool processes all selected sources and combines them with your iMessage
  history into a single unified report

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

### "The tool seemed to freeze for several minutes after I clicked OK."

This is normal on the first run. The tool is installing Homebrew and Python 3,
which takes 2-5 minutes depending on your internet speed. The Terminal window
will show progress. Wait for the next dialog to appear.

### "It says Terminal needs Full Disk Access. I don't see Terminal in the list."

1. In System Settings → Privacy & Security → Full Disk Access, click the **+** button
2. A Finder dialog opens — navigate to **Applications → Utilities**
3. Select **Terminal** and click **Open**
4. Toggle the switch next to Terminal to **ON**
5. Switch back to the Terminal window — the tool will detect it and continue

### "It says 'Work Profile Detected' and asks me to run a Terminal command."

Your organization's IT profile is blocking direct database access. Follow the
steps in the dialog:

1. Press **⌘ + Space**, type `Terminal`, press **Return**
2. Paste this command and press **Return**:
   ```
   cp -r ~/Library/Messages ~/Desktop/Messages_copy
   ```
3. Wait for the command to finish (no output = success; may take 1-2 minutes)
4. Click **Continue** in the tool's dialog

If you're unsure, ask your IT department to grant Terminal "Full Disk Access" in
your device's management profile.

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

### "What if I get an error about 'biplist' or 'openpyxl'?"

The tool installs these automatically on first run. If the install failed (e.g.,
due to a network error), delete the folder `~/.imessage_forensic_sandbox` and
re-run the tool — it will reinstall cleanly.

To delete the sandbox, open Terminal and run:
```
rm -rf ~/.imessage_forensic_sandbox
```

### "I keep getting the same crash even after downloading a new version."

This is caused by macOS creating numbered copies of extracted folders
(`imessage-forensic`, `imessage-forensic 2`, `imessage-forensic 3`, etc.)
when you extract the same zip multiple times. You end up double-clicking an
old copy of the launcher.

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
  iMessage Forensic Recovery v10.0 (build 2026-06-20)
```

If that line does **not** appear before any error, you are still running an old
copy. Delete it and use the newly extracted one.

---

## 8a. Upgrading / Fixing a Stuck Install

### Double-clickable reset (easiest)

The toolkit includes `RESET.command`. Double-click it to automatically remove
stale tool folders, cached scripts, and the Python sandbox — without touching
your data. Then extract the new zip fresh and run as normal.

### Manual reset via Terminal

If `RESET.command` is not available (e.g., you only have the launcher from an
old version), paste this block into Terminal:

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

### After the reset

1. Extract the LATEST zip into a **new, clean folder** (delete any existing
   `imessage-forensic*` folders in Downloads first).
2. Verify the extracted folder is named exactly `imessage-forensic` (not
   `imessage-forensic 2` or similar — that means you still have an old copy).
3. Double-click `imessage_ultimate_launcher.command`.
4. Confirm the first line printed says `iMessage Forensic Recovery v10.0`.

---

## 9. Privacy & Security

**What the tool reads:**
- Your Messages database (`~/Library/Messages/chat.db` and associated files)
- iCloud sync tables within that database
- Optionally: iPhone/iPad backup databases under `~/Library/Application Support/MobileSync/Backup/`

**What never leaves your machine:**
- Everything. The tool runs entirely offline. No data is uploaded, transmitted,
  or shared. Reports are saved locally on your Desktop.
- The one-time software install (Homebrew, Python 3, packages) downloads from
  public package servers (`brew.sh`, `pypi.org`). After that, no network access
  is needed.

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

1. Download the new `imessage_ultimate_launcher.command`
2. Double-click to run
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
  Jamf, etc.), the MDM profile may block direct database access. The Terminal
  workaround (`cp -r ~/Library/Messages ~/Desktop/Messages_copy`) works in most
  cases, but some highly-restricted profiles may block even that.

- **Attachments are not extracted.** The report references attachment filenames
  and MIME types, but the actual image/video/audio files are not copied or
  embedded. Attachments remain at their original paths on your Mac.

- **iOS backups are scanned but not decrypted.** If you have encrypted iPhone
  backups, the tool will detect the backup databases but cannot read encrypted
  content.

---

## 12. For Developers

### Architecture

The toolkit ships as a single double-clickable bash file:
`imessage_ultimate_launcher.command`

This file embeds five Python modules as heredocs (single-quoted delimiters prevent
variable expansion). At runtime, the bash launcher writes each module to a hidden
file in `$HOME` and invokes them via `python3`:

| Heredoc marker | Written to | Purpose |
|---|---|---|
| `CORE_PY_EOF` | `~/.imsg_core.py` | DB extraction, WAL carving, backup scan, XLSX export |
| `CK_PY_EOF` | `~/.imsg_cloudkit.py` | CloudKit sync table classification |
| `PARSER_PY_EOF` | `~/.imsg_parser.py` | Message parsing, tombstone detection, timeline CSV |
| `REPORT_PY_EOF` | `~/.imsg_report.py` | Self-contained HTML report generation |
| `REORG_PY_EOF` | `~/.imsg_reorganize.py` | Scan, classify, and upgrade extraction folders |

The same five modules also exist as standalone CLI scripts
(`core.py`, `cloudkit.py`, `parser.py`, `report.py`, `merge.py`) for
command-line use and testing. All of these files live at the **root of this
repository** alongside the launcher.

Multi-platform support lives in the `extractors/` package, which is only used by
the standalone CLI (the launcher heredocs run from a temp directory and cannot
import it, so the attribution logic is inlined into the launcher's parser
heredoc):

| File | Purpose |
|---|---|
| `extractors/attribution.py` | Platform attribution engine — weighted regex scoring → per-platform confidence (0.40 threshold) |
| `extractors/recursive_search.py` | iOS MobileSync `Manifest.db` scan for third-party app databases |
| `extractors/signal_desktop.py` | Signal Desktop reader (marks records `ENCRYPTED`; never decrypts) |
| `extractors/whatsapp_desktop.py` | WhatsApp Desktop reader |
| `extractors/meta_import.py` | Instagram / Facebook Messenger data-export ZIP importer |
| `extractors/snapchat_import.py` | Snapchat "My Data" ZIP importer |
| `extractors/telegram_import.py` | Telegram export importer |
| `extractors/google_messages_import.py` | Google Takeout Messages importer |
| `extractors/normalize.py` | Normalize any platform schema → common columns |

### Two-Copy Architecture and Drift Guard

Because the modules exist twice (standalone + embedded), security fixes must be
applied in both places. A drift guard enforces this:

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

```bash
# Extract from a Messages database
python3 core.py ~/Library/Messages/chat.db /path/to/output

# Parse extracted data
python3 parser.py /path/to/output

# Classify CloudKit sync status
python3 cloudkit.py /path/to/output

# Generate HTML report
python3 report.py /path/to/output/parsed_output /path/to/output/cloudkit_classification.json

# Merge multiple extractions (multi-device)
python3 merge.py /path/to/device1 /path/to/device2 --output /path/to/merged
```

### Repository Layout

This is a standalone repository — every file lives at the root:

```
.
├── imessage_ultimate_launcher.command   # main entry point (bash + embedded Python), executable (100755)
├── RESET.command                        # double-clickable cleanup helper, executable (100755)
├── core.py                              # DB copy, CloudKit probe, WAL carving, exports
├── cloudkit.py                          # CloudKit residual record probing
├── parser.py                            # message parsing, tombstones, WAL cross-ref + attribution
├── report.py                            # HTML report generation
├── merge.py                             # unified timeline across sources
├── sync_check.py                        # drift guard (see above)
├── README.md
└── extractors/                          # multi-platform readers/importers (standalone CLI only)
```

Both `.command` files must stay executable in git (mode `100755`) so they run
when cloned on macOS. If you edit one on Windows the execute bit is dropped;
restore it with:

```bash
git update-index --chmod=+x imessage_ultimate_launcher.command
git update-index --chmod=+x RESET.command
git ls-files --stage *.command   # expect 100755 on both
```

### Verifying a Change

After any edit to analysis logic, run all of these from the repo root — all must
be clean before delivering:

```bash
# 1. launcher bash is syntactically valid
bash -n imessage_ultimate_launcher.command

# 2. standalone modules parse
python3 -c "import ast;[ast.parse(open(f).read()) for f in ['core.py','parser.py','report.py','merge.py','cloudkit.py','sync_check.py']];print('py OK')"

# 3. the drift guard — must report all 10 invariants pass
python3 sync_check.py
```

Remember the dual-copy rule: any change to logic in a standalone module MUST be
mirrored in the corresponding launcher heredoc (and vice-versa), or `sync_check.py`
will fail.
