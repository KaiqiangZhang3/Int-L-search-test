#!/usr/bin/env python3
"""Reject private material from manifests prepared for external use."""

import argparse
import json
from pathlib import Path
import re
import sys


FILE_URI = re.compile(r"file://", re.IGNORECASE)
POSIX_ABSOLUTE_PATH = re.compile(
    r"(?<![:/A-Za-z0-9])/(?!/)[^\s<>()\[\]{}\"']+"
)
WINDOWS_ABSOLUTE_PATH = re.compile(
    r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|\\\\)[^\s<>()\[\]{}\"']+"
)
FORBIDDEN_PRIVACY_MARKER = re.compile(
    r"private_note_reference|externalizable[\"']?\s*[:=]\s*false",
    re.IGNORECASE,
)
PUBLIC_EXPORT_CLASSES = {
    "public_citation_extract",
    "public_research_output",
}


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _nested_dicts(value):
    if isinstance(value, dict):
        for item in value.values():
            if isinstance(item, dict):
                yield item
            yield from _nested_dicts(item)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                yield item
            yield from _nested_dicts(item)


def _load_jsonl(text: str) -> tuple[list[tuple[str, dict]], list[str]]:
    records = []
    errors = []
    for line_number, raw_line in enumerate(
        text.splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append(f"Line {line_number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"Line {line_number}: each JSONL item must be an object")
            continue
        records.append((f"Line {line_number}", record))
    return records, errors


def _load_markdown(text: str) -> tuple[list[tuple[str, dict]], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], ["Markdown manifest requires YAML-style privacy front matter"]
    try:
        closing = next(
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration:
        return [], ["Markdown manifest has unclosed privacy front matter"]

    metadata = {}
    for line in lines[1:closing]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    raw_externalizable = metadata.get("externalizable")
    if isinstance(raw_externalizable, str):
        if raw_externalizable.lower() == "true":
            metadata["externalizable"] = True
        elif raw_externalizable.lower() == "false":
            metadata["externalizable"] = False
    metadata["content"] = text
    return [("Document", metadata)], []


def _validate_record(location: str, record: dict) -> list[str]:
    errors = []
    classification = record.get("privacy_classification")
    if classification is None:
        errors.append(f"{location}: privacy_classification is required")
    elif classification == "private_note_reference":
        errors.append(f"{location}: private_note_reference is not externalizable")
    elif classification not in PUBLIC_EXPORT_CLASSES:
        errors.append(f"{location}: unsupported privacy_classification")

    if "externalizable" not in record:
        errors.append(f"{location}: externalizable is required")
    elif record.get("externalizable") is False:
        errors.append(f"{location}: externalizable=false")
    elif record.get("externalizable") is not True:
        errors.append(f"{location}: externalizable must be boolean true")

    nested = tuple(_nested_dicts(record))
    if any(
        item.get("privacy_classification") == "private_note_reference"
        for item in nested
    ):
        errors.append(f"{location}: nested private_note_reference is not exportable")
    if any(item.get("externalizable") is False for item in nested):
        errors.append(f"{location}: nested externalizable=false")

    values = tuple(_strings(record))
    if any(FORBIDDEN_PRIVACY_MARKER.search(value) for value in values):
        errors.append(f"{location}: forbidden privacy marker is not exportable")
    if any(FILE_URI.search(value) for value in values):
        errors.append(f"{location}: file:// URI is not exportable")
    if any(
        POSIX_ABSOLUTE_PATH.search(value) or WINDOWS_ABSOLUTE_PATH.search(value)
        for value in values
    ):
        errors.append(f"{location}: absolute local path is not exportable")
    return errors


def validate_export_manifest(path: Path) -> list[str]:
    """Return privacy errors found in a JSONL or Markdown export manifest."""

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"Unable to read manifest: {exc}"]

    if path.suffix.lower() in {".md", ".markdown"}:
        records, errors = _load_markdown(text)
    else:
        records, errors = _load_jsonl(text)
    for location, record in records:
        errors.extend(_validate_record(location, record))
    return errors


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate privacy safety of an external export manifest."
    )
    parser.add_argument("manifest", type=Path)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    errors = validate_export_manifest(args.manifest)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print("Export manifest is privacy-safe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
