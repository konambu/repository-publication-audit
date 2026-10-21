"""Read-only publication checks against Git's index; never print secret values."""

import argparse
import json
import re
import subprocess
from pathlib import Path, PurePosixPath


SECRET_PATTERNS = (
    rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
    rb"\bgithub_pat_[A-Za-z0-9_]{50,}\b",
    rb"\bAKIA[0-9A-Z]{16}\b",
    rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}\b",
)


def inspect_path(path, size):
    """Return findings without opening files or mutating the index."""
    name = PurePosixPath(path).name
    parts = PurePosixPath(path).parts
    findings = []
    if any(p in parts for p in (".godot", "__pycache__", ".continue", "reference_private")):
        findings.append(("error", "machine-local or private directory"))
    if name.endswith((".log", ".pyc", ".tmp")) or re.search(r"\.blend\d+$", name):
        findings.append(("error", "generated log, cache or backup"))
    if (name == ".env" or name.startswith(".env.")) and name != ".env.example":
        findings.append(("error", "environment configuration"))
    if name.lower().endswith((".pem", ".key", ".pmx", ".pmd")):
        findings.append(("error", "private key or reference-model extension requires review"))
    if size >= 100 * 1024 * 1024:
        findings.append(("error", "blob is at least 100 MiB"))
    elif size >= 10 * 1024 * 1024:
        findings.append(("warning", "blob is at least 10 MiB"))
    return findings


def contains_secret(data):
    return any(re.search(pattern, data) for pattern in SECRET_PATTERNS)


def git(root, *args, input_data=None):
    return subprocess.run(
        ["git", "-C", str(root), *args], input=input_data,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout


def audit(root):
    entries = []
    for record in git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, oid, stage = metadata.split()
        if stage != b"0":
            raise ValueError("Resolve index conflicts before auditing.")
        if mode == b"160000":
            raise ValueError("Submodules need a separate publication review.")
        entries.append((path.decode("utf-8"), oid.decode("ascii")))
    ids = list(dict.fromkeys(oid for _, oid in entries))
    sizes = {}
    if ids:
        raw = git(root, "cat-file", "--batch-check", input_data=("\n".join(ids) + "\n").encode())
        for line in raw.splitlines():
            oid, kind, size = line.split()
            if kind != b"blob":
                raise ValueError("Unexpected non-blob index entry.")
            sizes[oid.decode()] = int(size)
    # Scan small blobs in a single subprocess, including staged contents that
    # differ from the working tree. Large binaries are reported by size only.
    small = [oid for oid in ids if sizes[oid] <= 2 * 1024 * 1024]
    suspicious = set()
    if small:
        raw = git(root, "cat-file", "--batch", input_data=("\n".join(small) + "\n").encode())
        offset = 0
        for expected in small:
            end = raw.index(b"\n", offset)
            oid, kind, length = raw[offset:end].split()
            if oid.decode() != expected or kind != b"blob":
                raise ValueError("Unexpected cat-file response.")
            offset = end + 1
            data = raw[offset:offset + int(length)]
            offset += int(length) + 1
            if b"\0" not in data and contains_secret(data):
                suspicious.add(expected)
    findings = []
    for path, oid in entries:
        checks = inspect_path(path, sizes[oid])
        if oid in suspicious:
            checks.append(("error", "possible credential; value redacted"))
        for severity, reason in checks:
            findings.append({"severity": severity, "path": path, "reason": reason})
    return {
        "scope": "Git index only; not untracked files or commit history",
        "files": len(entries), "bytes": sum(sizes[oid] for _, oid in entries),
        "secret_scan_max_blob_bytes": 2 * 1024 * 1024,
        "findings": findings,
        "errors": sum(f["severity"] == "error" for f in findings),
        "warnings": sum(f["severity"] == "warning" for f in findings),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only publication audit of a Git index; secret values are never printed."
    )
    parser.add_argument("repository", nargs="?", type=Path, default=Path.cwd(),
                        help="Repository directory (default: current directory)")
    parser.add_argument("--warnings-as-errors", action="store_true",
                        help="Exit 1 for large-file warnings as well as errors")
    args = parser.parse_args(argv)
    root = args.repository.resolve()
    try:
        report = audit(root)
    except (subprocess.CalledProcessError, ValueError, UnicodeError) as error:
        # Git stderr can contain local configuration; don't echo it publicly.
        print(json.dumps({"error": "Audit failed", "type": type(error).__name__}))
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 1 if report["errors"] or (args.warnings_as_errors and report["warnings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
