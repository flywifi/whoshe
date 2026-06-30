# MAINTAINER — meta-import extractor

## Extractor identity
- **id**: `meta-import`
- **detect_mode**: `file_provided` (user supplies a Meta data export zip)
- **platforms**: Facebook, Instagram
- **label**: Meta (Facebook/Instagram) Export Importer

## Non-negotiable invariants
1. `detect(zip_path)` must return `True` only for Meta (Facebook or Instagram) exports; `False` for all others.
2. `extract(zip_path, out_dir)` must never write files outside `out_dir`.
3. Every output record must include `platform: "Facebook"` or `platform: "Instagram"` (never "Meta") and `retrieved_at` (ISO 8601).
4. Message text in Meta exports is UTF-8 stored as Latin-1 mojibake — must be re-encoded before output.
5. Timestamps in Meta exports are Unix epoch integers — must be converted to ISO 8601.

## Failure modes
- Zip is a Telegram or Snapchat export → `detect()` returns `False`
- Messages JSON uses Latin-1 encoding → apply `bytes.decode('latin-1').encode('utf-8')` fix
- Photo/video attachments → include `uri` reference only; do not embed binary content
- Inbox vs archived vs filtered message folders → all must be traversed

## Regression cases
- Meta changed their export format in 2022 (nested `messages_N.json` files instead of single file) — both formats must be handled
- Instagram DMs have a different folder structure than Facebook Messenger

## Approval-gated changes
- Any change to the mojibake re-encoding logic requires testing against non-ASCII characters in multiple languages.
- Platform detection logic (`"Facebook"` vs `"Instagram"`) changes must update the output_schema enum in `extractors_manifest.json`.

## Minority-report policy
If the same conversation thread appears in both inbox and archived folders with different message counts, emit a minority report noting the discrepancy and choosing the higher-count source.
