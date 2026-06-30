# MAINTAINER — google-messages-import extractor

## Extractor identity
- **id**: `google-messages-import`
- **detect_mode**: `file_provided` (user supplies a Google Takeout zip)
- **platform**: cross-platform (Google Messages via RCS/SMS)
- **label**: Google Messages Takeout Importer

## Non-negotiable invariants
1. `detect(zip_path)` must return `True` only if the zip contains `Takeout/Google Messages/` path structure.
2. `detect(zip_path)` must return `False` (not raise) for any non-Google-Messages Takeout zip.
3. `extract(zip_path, out_dir)` must never write files outside `out_dir`.
4. Every output record must include `platform: "Google Messages"` and `retrieved_at` (ISO 8601).
5. Both SMS and RCS message types must be normalized to the same output schema.

## Failure modes
- Generic Google Takeout zip without Messages folder → `detect()` returns `False`
- `.html` files in Takeout (Google's format is HTML, not JSON) → parse HTML; never return raw HTML in output
- Missing recipient field in group MMS → include with `to: null`
- Attachments → include `filename` and `mime_type` only; do not embed binary content

## Regression cases
- Google Takeout format for Messages changed from `.json` to `.html` files in 2021 — HTML parsing path must remain tested
- MMS group threads have multiple participants; all must be captured in `participants` array

## Approval-gated changes
- Any change to HTML parsing logic requires testing against known-good Takeout samples.
- Changes to the output schema must update `extractors_manifest.json` output_schema.

## Minority-report policy
If the same message thread appears in both SMS and RCS exports with conflicting timestamps, emit a minority report choosing the RCS timestamp (higher fidelity) and noting the SMS timestamp as a conflict.
