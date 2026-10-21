---
name: repository-publication-audit
description: Inspect a Git index for local files, oversized blobs, and representative credential patterns using this repository's read-only publication audit CLI.
---

# Repository Publication Audit

Locate the checkout containing tools/repository_audit.py and read README.md for the current detection scope and exit codes. Identify the target repository explicitly.

Inspect `git status --short` and the intended staged file list before running the audit. The tool reads the index, so unstaged edits and untracked files are not included. Stage only files that belong to the requested publication task.

```sh
python tools/repository_audit.py /path/to/target --warnings-as-errors
```

Read the JSON findings and distinguish content detections, path classifications, size warnings, and audit execution failures. When investigating a suspected secret, report the path and reason without reproducing the value. Revise the intended staged content, then rerun the audit when it changes.

The tool does not scan history or untracked files, validate ownership, or change GitHub visibility. Content scanning covers only nonbinary blobs up to 2 MiB and representative patterns. A passing result is evidence about those checks, not a complete publication clearance.

If historical disclosure is in scope, inspect history separately using an appropriate tool and avoid printing secret values. Commit, push, or change visibility only within the user's authorized publication scope; invoking this skill alone does not authorize external publication.

Summarize the target, staged-file scope, errors and warnings, and any unresolved findings. Keep machine-specific audit output local. Use the existing temporary-repository tests when changing the index reader or detection logic.
