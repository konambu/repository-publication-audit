---
name: utf8-source-editing
description: Edit Japanese or encoding-sensitive source files while preserving encoding, BOM, and newline conventions and diagnosing apparent mojibake.
---

# UTF-8 Source Editing

Adapted from an encoding-sensitive game development workflow. Use this when terminal text appears corrupted or edits might change a source file's encoding.

Inspect the actual bytes and the repository's encoding conventions first. Terminal rendering alone cannot identify a file's encoding. If decoding as UTF-8 fails, stop assuming UTF-8 and determine the existing encoding before rewriting. Keep valid Japanese text intact.

Prefer a focused patch against stable source lines. ASCII function names and identifiers make useful anchors when nearby comments display incorrectly. Avoid PowerShell text pipelines that decode and rewrite an entire tracked file with implicit defaults.

Preserve the existing BOM and newline convention unless the requested change requires conversion. If a scripted transformation is necessary, use an explicit decoder and encoder, fail on decoding errors, and check that anchors match the expected number of times before writing. Do not silently replace undecodable bytes.

Review the resulting diff for unintended whole-file changes. Confirm the changed file decodes with the intended encoding and run its parser or compiler where available. A successful parse checks syntax, not whether Japanese wording is correct; inspect the affected text separately.

Keep encoding repair scoped to the user's request. Broad normalization of unrelated files makes review harder and can obscure functional changes.
