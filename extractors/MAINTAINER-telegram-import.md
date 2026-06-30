# MAINTAINER — telegram-import extractor

## Extractor identity
- **id**: `telegram-import`
- **detect_mode**: `file_provided` (user supplies a zip/folder export)
- **platform**: cross-platform
- **label**: Telegram JSON Export Importer

## Non-negotiable invariants
1. `detect(zip_path)` must return `True` only if the zip contains a `result.json` with a `chats` key.
2. `detect(zip_path)` must return `False` (not raise) for any non-Telegram zip.
3. `extract(zip_path, out_dir)` must never write files outside `out_dir`.
4. Every output record must include `platform: "Telegram"` and `retrieved_at` (ISO 8601).
5. The `from_id` field (Telegram user ID) must be preserved exactly — never truncated.

## Failure modes
- Zip is a Meta or Snapchat export → `detect()` returns `False`
- `result.json` is malformed JSON → raise `ValueError` with file path and parse position
- Empty export (no chats) → return `[]`, not an error
- Forwarded messages with missing `from` field → include record with `from: null`

## Regression cases
- Telegram occasionally changes the `result.json` schema; the `chats.list[].messages[]` structure is stable but `type` values and media fields are not
- Channel exports have different structure from personal chat exports — both must be handled

## Approval-gated changes
- Any change to how `from_id` is handled (anonymization, hashing) requires explicit user consent documentation.
- Changes to the output schema must update `extractors_manifest.json` output_schema.

## Minority-report policy
Not applicable to import mode (single authoritative source). If the export zip contains duplicate message IDs with different content, emit a minority report in the affected output record.
