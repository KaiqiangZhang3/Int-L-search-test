#!/usr/bin/env python3
"""Validate cross-record invariants in a canonical retrieval corpus."""

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Iterable

from corpus_ops import identity_key, validate_retrieval_links


TEMPLATE_PLACEHOLDER = re.compile(r"\{\{[^{}\n]*\}\}")
DRAFT_PLACEHOLDER = re.compile(
    r"^\s*(?:TODO|TBD)(?:\s*(?::|-).*)?\s*$",
    re.IGNORECASE,
)


def _location(path: Path, line_number: int) -> str:
    return f"{path.name}:{line_number}"


def _load_jsonl(path: Path) -> tuple[list[tuple[int, dict]], list[str]]:
    records = []
    errors = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return records, [f"{path}: unable to read file: {exc}"]

    for line_number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip():
            continue
        location = _location(path, line_number)
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append(f"{location}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"{location}: each JSONL record must be an object")
            continue
        records.append((line_number, record))
    return records, errors


def _validate_sources(
    path: Path, records: Iterable[tuple[int, dict]]
) -> tuple[set[str], list[str]]:
    source_ids = set()
    errors = []
    for line_number, record in records:
        location = _location(path, line_number)
        source_id = record.get("id")
        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(f"{location}: source id must be a non-empty string")
        elif source_id in source_ids:
            errors.append(f"{location}: duplicate source id: {source_id!r}")
        else:
            source_ids.add(source_id)

        try:
            key = identity_key(record)
        except (AttributeError, TypeError, ValueError) as exc:
            errors.append(f"{location}: invalid identity fields: {exc}")
        else:
            if key is None:
                errors.append(f"{location}: source lacks a sufficient identity key")

        for field in ("description", "inclusion_reason"):
            value = record.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"{location}: {field} must be a non-empty string"
                )
            elif TEMPLATE_PLACEHOLDER.search(value) or DRAFT_PLACEHOLDER.fullmatch(
                value
            ):
                errors.append(
                    f"{location}: {field} contains an unresolved placeholder"
                )

        try:
            validate_retrieval_links(record)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"{location}: retrieval linkage error: {exc}")
    return source_ids, errors


def _validate_edges(
    path: Path,
    records: Iterable[tuple[int, dict]],
    source_ids: set[str],
) -> list[str]:
    errors = []
    for line_number, edge in records:
        location = _location(path, line_number)
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        relation = edge.get("relation")
        status = edge.get("status")
        record_scope = edge.get("record_scope")

        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(f"{location}: source_id must be a non-empty string")
        elif source_id not in source_ids:
            errors.append(f"{location}: unknown source_id: {source_id!r}")
        if not isinstance(target_id, str) or not target_id.strip():
            errors.append(f"{location}: target_id must be a non-empty string")
        elif target_id not in source_ids:
            errors.append(f"{location}: unknown target_id: {target_id!r}")
        if relation == "cited_by":
            errors.append(
                f"{location}: canonical edges must use cites direction, not cited_by"
            )
        if status == "candidate":
            errors.append(f"{location}: candidate edge is outside the final corpus")
        elif status != "verified":
            errors.append(f"{location}: canonical edge status must be verified")
        if record_scope != "canonical":
            errors.append(f"{location}: edge record_scope must be canonical")

        evidence = edge.get("evidence")
        if not isinstance(evidence, dict):
            errors.append(f"{location}: verified edge requires evidence")
            continue
        evidence_source = evidence.get("source")
        evidence_location = evidence.get("location")
        if not isinstance(evidence_source, str) or not evidence_source.strip():
            errors.append(f"{location}: evidence.source must be a non-empty string")
        if not isinstance(evidence_location, str) or not evidence_location.strip():
            errors.append(f"{location}: evidence.location must be a non-empty string")
    return errors


def validate_corpus(sources_path: Path, edges_path: Path) -> tuple[int, int, list[str]]:
    source_records, errors = _load_jsonl(sources_path)
    edge_records, edge_load_errors = _load_jsonl(edges_path)
    errors.extend(edge_load_errors)

    source_ids, source_errors = _validate_sources(sources_path, source_records)
    errors.extend(source_errors)
    errors.extend(_validate_edges(edges_path, edge_records, source_ids))
    return len(source_records), len(edge_records), errors


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate canonical source and verified-edge JSONL files."
    )
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--edges", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    source_count, edge_count, errors = validate_corpus(args.sources, args.edges)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    edge_label = "edge" if edge_count == 1 else "edges"
    print(f"Validated {source_count} sources and {edge_count} verified {edge_label}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
