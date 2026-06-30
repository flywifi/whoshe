# MAINTAINER — snapchat-import extractor

## Extractor identity
- **id**: `snapchat-import`
- **detect_mode**: `file_provided` (user supplies a Snapchat data export zip)
- **platform**: cross-platform
- **label**: Snapchat Data Export Importer

## Non-negotiable invariants
1. `detect(zip_path)` must return `True` only if the zip contains `account.json` with a `basic_info` key (Snapchat-specific fingerprint).
2. `detect(zip_path)` must return `False` (not raise) for any non-Snapchat zip.
3. `extract(zip_path, out_dir)` must never write files outside `out_dir`.
4. Every output record must include `platform: "Snapchat"` and `retrieved_at` (ISO 8601).
5. Snapchat timestamps are stored as strings in UTC; must be parsed and preserved as ISO 8601.

## Failure modes
- Zip is a Meta or Telegram export → `detect()` returns `False`
- `chat_history.json` missing from export (Snapchat doesn't always include it) → return `[]`, not an error
- Snap media (photos/videos) referenced but not included in export → include message record with `media_available: false`
- Deleted messages appear as `[deleted]` in export → preserve with `content: null, deleted: true`

## Regression cases
- Snapchat exports mark some messages as `[deleted]` even when content was partially visible — preserve the placeholder text exactly
- Sender usernames vs display names may differ — always use `username` field as the canonical identifier

## Approval-gated changes
- Any change to how deleted message placeholders are handled requires explicit documentation in the output schema.
- Changes to the output schema must update `extractors_manifest.json` output_schema.

## Minority-report policy
Not applicable to import mode (single authoritative source). If `chat_history.json` and `memories_history.json` contain overlapping timestamps for the same conversation, the chat_history is authoritative; emit a minority report if counts diverge by more than 10%.
