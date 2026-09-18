#!/usr/bin/env python3
"""Validate cross-record invariants in a canonical retrieval corpus."""

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Iterable, Optional

from corpus_ops import identity_key, validate_retrieval_links


TEMPLATE_PLACEHOLDER = re.compile(r"\{\{[^{}\n]*\}\}")
DRAFT_PLACEHOLDER = re.compile(
    r"^\s*(?:TODO|TBD)(?:\s*(?::|-).*)?\s*$",
    re.IGNORECASE,
)
RELATION_FAMILIES = {
    "literature": {"cites", "responds_to", "criticizes", "extends"},
    "institutional": {"amends", "implements", "interprets", "same_proceeding"},
}


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


def _load_state(path: Path) -> tuple[Optional[dict], list[str]]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [f"{path.name}: unable to read valid state JSON: {exc}"]
    if not isinstance(state, dict):
        return None, [f"{path.name}: project state must be an object"]

    errors = []
    if state.get("schema_version") != 2:
        errors.append(f"{path.name}: schema_version must be 2")
    if not isinstance(state.get("graph_enabled"), bool):
        errors.append(f"{path.name}: graph_enabled must be a boolean")
    if not isinstance(state.get("saturation_enabled"), bool):
        errors.append(f"{path.name}: saturation_enabled must be a boolean")
    decisions = state.get("decision_log")
    branches = state.get("branches")
    if not isinstance(decisions, list):
        errors.append(f"{path.name}: decision_log must be an array")
        decisions = []
    if branches is not None and not isinstance(branches, list):
        errors.append(f"{path.name}: branches must be an array")
        branches = []
    decisions_by_id = {}
    for decision in decisions:
        if not isinstance(decision, dict):
            errors.append(f"{path.name}: each decision_log item must be an object")
            continue
        decision_id = decision.get("decision_id")
        if not isinstance(decision_id, str) or not decision_id.strip():
            errors.append(f"{path.name}: decision_id must be a non-empty string")
        elif decision_id in decisions_by_id:
            errors.append(f"{path.name}: duplicate decision_id {decision_id!r}")
        else:
            decisions_by_id[decision_id] = decision
    for branch in branches or []:
        if not isinstance(branch, dict) or branch.get("retrieval_mode") != "vertical":
            continue
        branch_id = branch.get("branch_id")
        authorization_id = branch.get("authorization_decision_id")
        decision = decisions_by_id.get(authorization_id)
        if decision is None or decision.get("kind") != "approve_trace":
            errors.append(
                f"{path.name}: vertical branch {branch_id!r} lacks an approved "
                "trace authorization"
            )
            continue
        if decision.get("branch_id") != branch_id:
            errors.append(
                f"{path.name}: vertical branch {branch_id!r} does not match its "
                "authorization branch_id"
            )
        if decision.get("seed_id") != branch.get("vertical_seed_id"):
            errors.append(
                f"{path.name}: vertical branch {branch_id!r} seed does not match "
                "its authorization"
            )
        if branch.get("tracing_direction") not in decision.get("directions", []):
            errors.append(
                f"{path.name}: vertical branch {branch_id!r} direction does not "
                "match its authorization"
            )
        approved_budget = branch.get("approved_budget")
        decision_budget = decision.get("budget")
        if (
            not isinstance(decision_budget, dict)
            or not decision_budget
            or approved_budget != decision_budget
        ):
            errors.append(
                f"{path.name}: vertical branch {branch_id!r} budget does not "
                "match its authorization"
            )
        elif (
            "depth_cap" in decision_budget
            and branch.get("max_authorized_depth") != decision_budget["depth_cap"]
        ):
            errors.append(
                f"{path.name}: vertical branch {branch_id!r} depth does not "
                "match its authorization budget"
            )
    return state, errors


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
        relation_family = edge.get("relation_family")
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
        elif relation_family not in RELATION_FAMILIES:
            errors.append(f"{location}: unsupported relation_family")
        elif relation not in RELATION_FAMILIES[relation_family]:
            errors.append(
                f"{location}: unsupported relation {relation!r} for "
                f"{relation_family!r} family"
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


def validate_corpus(
    sources_path: Path,
    edges_path: Optional[Path] = None,
    state_path: Optional[Path] = None,
) -> tuple[int, int, list[str]]:
    source_records, errors = _load_jsonl(sources_path)
    edge_records = []

    if state_path is not None:
        state, state_errors = _load_state(state_path)
        errors.extend(state_errors)
        if state is not None and state.get("graph_enabled") is True and edges_path is None:
            errors.append(f"{state_path.name}: graph_enabled requires --edges")

    if edges_path is not None:
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
    parser.add_argument(
        "--edges",
        type=Path,
        help="Optional verified-edge JSONL file when relationship graphs are enabled.",
    )
    parser.add_argument(
        "--state",
        type=Path,
        help="Optional version-2 project state used to enforce graph optionality.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    source_count, edge_count, errors = validate_corpus(
        args.sources, args.edges, args.state
    )
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
