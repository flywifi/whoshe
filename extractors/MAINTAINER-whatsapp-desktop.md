# MAINTAINER — whatsapp-desktop extractor

## Extractor identity
- **id**: `whatsapp-desktop`
- **detect_mode**: `auto` (no arguments — probes local filesystem)
- **platform**: macOS
- **label**: WhatsApp Desktop Extractor

## Non-negotiable invariants
1. `detect()` must return `False` (not raise) if the WhatsApp app directory does not exist.
2. `extract(out_dir)` must never write files outside `out_dir`.
3. Every output record must include `platform: "WhatsApp"` and `retrieved_at` (ISO 8601).
4. Attachment blobs must not be embedded in the output JSON — reference paths only.
5. Phone number fields must be normalized to E.164 format before output.

## Failure modes
- WhatsApp Desktop not installed → `detect()` returns `False`
- DB encrypted with unknown key scheme → raise `RuntimeError` with explanation
- Media store directory missing → log warning; return text messages only, omit media

## Regression cases
- WhatsApp Desktop updates may change the SQLite schema — verify column names against source_manifest
- Multi-device support (as of 2021) may produce multiple DB shards — all must be merged

## Approval-gated changes
- Any change to phone number normalization logic requires testing against E.164 edge cases (country codes, extensions).
- Changes to the output schema must update `extractors_manifest.json` output_schema.

## Minority-report policy
If two DB shards contain conflicting records for the same message ID, emit:
`"minority_report": {"conflicts": [{"source": "shard_1", "value": ...}, {"source": "shard_2", "value": ...}]}`.
