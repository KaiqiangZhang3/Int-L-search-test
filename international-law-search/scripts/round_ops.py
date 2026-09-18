#!/usr/bin/env python3
"""Allocate and atomically append v3 research-round records."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile


ROUND_TYPES = {
    "breadth",
    "breadth_expansion",
    "depth",
    "primary_materials",
    "state_practice",
    "doctrinal",
    "gap_filling",
    "verification",
    "synthesis",
}
ROUND_STATUSES = {"approved", "active", "paused", "completed", "cancelled"}
MAIN_ID_PATTERN = re.compile(r"^R([1-9][0-9]*)$")
SIDE_ID_PATTERN = re.compile(r"^R([1-9][0-9]*)\.S([1-9][0-9]*)$")
REQUIRED_FIELDS = {
    "round_id",
    "kind",
    "parent_round_id",
    "round_type",
    "status",
    "authorization_decision_id",
    "research_question",
    "exclusions",
    "planned_budget",
    "actual_budget",
    "methods",
    "added_source_keys",
    "updated_source_keys",
    "duplicate_source_keys",
    "unresolved_source_keys",
    "added_claim_ids",
    "revised_claim_ids",
    "report_path",
    "synthesis_version",
    "presentation_version",
    "next_round_options",
    "budget_extension_decision_id",
}
BUDGET_AXES = (
    "bibliographic_discovery",
    "full_text_acquisition",
    "substantive_review",
)
BUDGET_CAPS = BUDGET_AXES + ("query_cap", "time_cap_minutes", "tracing_depth")
BUDGET_FIELDS = set(BUDGET_CAPS) | {"platforms", "seeds", "language_allocations"}
STRING_ARRAY_FIELDS = {
    "exclusions",
    "methods",
    "added_source_keys",
    "updated_source_keys",
    "duplicate_source_keys",
    "unresolved_source_keys",
    "added_claim_ids",
    "revised_claim_ids",
}


def _validate_existing_ids(records: list[dict]) -> None:
    round_ids = [record.get("round_id") for record in records]
    if any(not isinstance(round_id, str) for round_id in round_ids):
        raise ValueError("Every indexed round requires a string round_id")
    if len(round_ids) != len(set(round_ids)):
        raise ValueError("The round index contains a duplicate round_id")
    main_ids = {
        record["round_id"]
        for record in records
        if record.get("kind") == "main"
        and MAIN_ID_PATTERN.fullmatch(record["round_id"])
    }
    for record in records:
        round_id = record["round_id"]
        if record.get("kind") == "main":
            if not MAIN_ID_PATTERN.fullmatch(round_id):
                raise ValueError(f"Invalid main round_id: {round_id!r}")
            if record.get("parent_round_id") is not None:
                raise ValueError("A main round cannot have a parent round")
        elif record.get("kind") == "side":
            match = SIDE_ID_PATTERN.fullmatch(round_id)
            parent_id = record.get("parent_round_id")
            if (
                match is None
                or parent_id not in main_ids
                or f"R{match.group(1)}" != parent_id
            ):
                raise ValueError("A side round parent must be an existing main round")
        else:
            raise ValueError(f"Invalid round kind for {round_id!r}")
    main_numbers = sorted(
        int(match.group(1))
        for record in records
        if record.get("kind") == "main"
        and (match := MAIN_ID_PATTERN.fullmatch(str(record.get("round_id", ""))))
    )
    if main_numbers != list(range(1, len(main_numbers) + 1)):
        raise ValueError("The round index contains a main-round gap")
    for parent_id in main_ids:
        side_numbers = sorted(
            int(match.group(2))
            for record in records
            if record.get("kind") == "side"
            and record.get("parent_round_id") == parent_id
            and (match := SIDE_ID_PATTERN.fullmatch(record["round_id"]))
        )
        if side_numbers != list(range(1, len(side_numbers) + 1)):
            raise ValueError(
                f"The round index contains a side-round gap for {parent_id}"
            )


def allocate_round(
    records: list[dict],
    *,
    kind: str,
    round_type: str,
    parent_round_id: str | None = None,
) -> dict:
    """Allocate the next main or parent-scoped side-round ID."""
    _validate_existing_ids(records)
    if kind not in {"main", "side"}:
        raise ValueError("Round kind must be 'main' or 'side'")
    if round_type not in ROUND_TYPES:
        raise ValueError(f"Unsupported round type: {round_type!r}")

    if kind == "main":
        if parent_round_id is not None:
            raise ValueError("A main round cannot have a parent round")
        main_numbers = [
            int(match.group(1))
            for record in records
            if record.get("kind") == "main"
            and (match := MAIN_ID_PATTERN.fullmatch(str(record.get("round_id", ""))))
        ]
        return {
            "round_id": f"R{max(main_numbers, default=0) + 1}",
            "kind": "main",
            "parent_round_id": None,
            "round_type": round_type,
        }

    if parent_round_id is None:
        raise ValueError("A side round requires parent_round_id")
    parent = next(
        (record for record in records if record.get("round_id") == parent_round_id),
        None,
    )
    if parent is None:
        raise ValueError(f"Unknown parent round: {parent_round_id!r}")
    if parent.get("kind") != "main" or not MAIN_ID_PATTERN.fullmatch(parent_round_id):
        raise ValueError("A side round parent must be a main round")

    side_numbers = [
        int(match.group(2))
        for record in records
        if record.get("kind") == "side"
        and (match := SIDE_ID_PATTERN.fullmatch(str(record.get("round_id", ""))))
        and f"R{match.group(1)}" == parent_round_id
    ]
    return {
        "round_id": f"{parent_round_id}.S{max(side_numbers, default=0) + 1}",
        "kind": "side",
        "parent_round_id": parent_round_id,
        "round_type": round_type,
    }


def _load_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON on line {line_number}: {error.msg}") from error
        if not isinstance(value, dict):
            raise ValueError(f"Round record on line {line_number} must be an object")
        records.append(value)
    return records


def _validate_budget(budget: object, label: str) -> None:
    if not isinstance(budget, dict):
        raise ValueError(f"{label} must be an object")
    missing = sorted(BUDGET_FIELDS - set(budget))
    if missing:
        raise ValueError(f"{label} is missing required fields: {', '.join(missing)}")
    extra = sorted(set(budget) - BUDGET_FIELDS)
    if extra:
        raise ValueError(f"{label} has unsupported fields: {', '.join(extra)}")
    for axis in BUDGET_AXES:
        value = budget.get(axis)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{label}.{axis} must be a non-negative integer")
    for field in ("query_cap", "tracing_depth"):
        value = budget[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{label}.{field} must be a non-negative integer")
    time_cap = budget["time_cap_minutes"]
    if (
        not isinstance(time_cap, (int, float))
        or isinstance(time_cap, bool)
        or time_cap < 0
    ):
        raise ValueError(f"{label}.time_cap_minutes must be a non-negative number")
    if not isinstance(budget["platforms"], list):
        raise ValueError(f"{label}.platforms must be an array")
    for platform in budget["platforms"]:
        if (
            not isinstance(platform, dict)
            or not isinstance(platform.get("name"), str)
            or not platform["name"].strip()
            or not isinstance(platform.get("purpose"), str)
            or not platform["purpose"].strip()
        ):
            raise ValueError(f"{label}.platforms entries require name and purpose")
    if not isinstance(budget["seeds"], list) or any(
        not isinstance(seed, str) or not seed.strip() for seed in budget["seeds"]
    ):
        raise ValueError(f"{label}.seeds must be an array of non-empty strings")
    if not isinstance(budget["language_allocations"], list):
        raise ValueError(f"{label}.language_allocations must be an array")
    for allocation in budget["language_allocations"]:
        if not isinstance(allocation, dict):
            raise ValueError(f"{label}.language_allocations entries must be objects")
        required = {"language", "purpose", *BUDGET_AXES}
        if required - set(allocation):
            raise ValueError(
                f"{label}.language_allocations entries require language, purpose, "
                "and all three budget axes"
            )
        if (
            not isinstance(allocation["language"], str)
            or not allocation["language"].strip()
        ):
            raise ValueError(f"{label}.language_allocations require a language")
        if (
            not isinstance(allocation["purpose"], str)
            or not allocation["purpose"].strip()
        ):
            raise ValueError(f"{label}.language_allocations require a purpose")
        for axis in BUDGET_AXES:
            value = allocation[axis]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(
                    f"{label}.language_allocations.{axis} must be a non-negative integer"
                )


def _validate_record(record: dict) -> None:
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        raise ValueError(f"Round record is missing required fields: {', '.join(missing)}")
    extra = sorted(set(record) - REQUIRED_FIELDS)
    if extra:
        raise ValueError(f"Round record has unsupported fields: {', '.join(extra)}")
    if record["kind"] not in {"main", "side"}:
        raise ValueError("Round kind must be 'main' or 'side'")
    if record["round_type"] not in ROUND_TYPES:
        raise ValueError(f"Unsupported round type: {record['round_type']!r}")
    if record["status"] not in ROUND_STATUSES:
        raise ValueError(f"Unsupported round status: {record['status']!r}")
    for field in ("authorization_decision_id", "research_question"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(f"Round record {field} must be a non-empty string")
    for field in STRING_ARRAY_FIELDS:
        value = record[field]
        if (
            not isinstance(value, list)
            or any(not isinstance(item, str) or not item.strip() for item in value)
            or len(value) != len(set(value))
        ):
            raise ValueError(
                f"Round record {field} must contain unique non-empty strings"
            )
    for field in (
        "report_path",
        "synthesis_version",
        "presentation_version",
        "budget_extension_decision_id",
    ):
        value = record[field]
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"Round record {field} must be null or a non-empty string")
    if not isinstance(record["next_round_options"], list) or any(
        not isinstance(option, dict) for option in record["next_round_options"]
    ):
        raise ValueError("Round record next_round_options must be an array of objects")
    if record["kind"] == "main":
        if not MAIN_ID_PATTERN.fullmatch(str(record["round_id"])):
            raise ValueError("Main round_id must use the form R1")
        if record["parent_round_id"] is not None:
            raise ValueError("A main round cannot have a parent round")
    else:
        if not SIDE_ID_PATTERN.fullmatch(str(record["round_id"])):
            raise ValueError("Side round_id must use the form R1.S1")
        if not isinstance(record["parent_round_id"], str):
            raise ValueError("A side round requires parent_round_id")
    _validate_budget(record["planned_budget"], "planned_budget")
    _validate_budget(record["actual_budget"], "actual_budget")
    if not record.get("budget_extension_decision_id"):
        planned_platforms = {
            (item["name"].strip().casefold(), item["purpose"].strip().casefold())
            for item in record["planned_budget"]["platforms"]
        }
        actual_platforms = {
            (item["name"].strip().casefold(), item["purpose"].strip().casefold())
            for item in record["actual_budget"]["platforms"]
        }
        if not actual_platforms.issubset(planned_platforms):
            raise ValueError(
                "actual_budget includes an unapproved platform or platform purpose"
            )
        if not set(record["actual_budget"]["seeds"]).issubset(
            record["planned_budget"]["seeds"]
        ):
            raise ValueError("actual_budget includes an unapproved seed")

        planned_languages = {
            item["language"].strip().casefold(): item
            for item in record["planned_budget"]["language_allocations"]
        }
        for allocation in record["actual_budget"]["language_allocations"]:
            planned_allocation = planned_languages.get(
                allocation["language"].strip().casefold()
            )
            if planned_allocation is None:
                raise ValueError(
                    "actual_budget includes an unapproved language allocation"
                )
            if allocation["purpose"].strip().casefold() != planned_allocation[
                "purpose"
            ].strip().casefold():
                raise ValueError("actual_budget changes a language allocation purpose")
            for axis in BUDGET_AXES:
                if allocation[axis] > planned_allocation[axis]:
                    raise ValueError(
                        f"actual_budget language allocation {axis} exceeds the "
                        "authorized cap"
                    )
        for field in BUDGET_CAPS:
            planned = record["planned_budget"].get(field)
            actual = record["actual_budget"].get(field)
            if (
                isinstance(planned, (int, float))
                and not isinstance(planned, bool)
                and isinstance(actual, (int, float))
                and not isinstance(actual, bool)
                and actual > planned
            ):
                raise ValueError(
                    f"actual_budget.{field} exceeds the authorized cap without "
                    "a budget extension decision"
                )


def _atomic_write(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            for item in records:
                stream.write(json.dumps(item, ensure_ascii=False, sort_keys=True))
                stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        Path(temporary_name).replace(path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def append_round(path: Path, record: dict) -> None:
    """Validate and atomically append one non-duplicate round."""
    if not isinstance(record, dict):
        raise ValueError("Round record must be an object")
    _validate_record(record)
    records = _load_records(path)
    for existing in records:
        _validate_record(existing)
    _validate_existing_ids(records)
    if any(existing.get("round_id") == record["round_id"] for existing in records):
        raise ValueError(f"Duplicate round_id: {record['round_id']}")
    if record["kind"] == "main":
        main_numbers = sorted(
            int(match.group(1))
            for existing in records
            if existing.get("kind") == "main"
            and (match := MAIN_ID_PATTERN.fullmatch(str(existing.get("round_id", ""))))
        )
        if main_numbers != list(range(1, len(main_numbers) + 1)):
            raise ValueError("Existing main rounds contain an ID gap")
        expected_id = f"R{len(main_numbers) + 1}"
        if record["round_id"] != expected_id:
            raise ValueError(f"The next main round must be {expected_id}")
    else:
        parent = next(
            (
                existing
                for existing in records
                if existing.get("round_id") == record["parent_round_id"]
            ),
            None,
        )
        match = SIDE_ID_PATTERN.fullmatch(record["round_id"])
        embedded_parent_id = f"R{match.group(1)}"
        if (
            parent is None
            or parent.get("kind") != "main"
            or embedded_parent_id != record["parent_round_id"]
        ):
            raise ValueError("A side round parent must be an existing main round")
        sibling_numbers = sorted(
            int(sibling_match.group(2))
            for existing in records
            if existing.get("kind") == "side"
            and existing.get("parent_round_id") == record["parent_round_id"]
            and (
                sibling_match := SIDE_ID_PATTERN.fullmatch(
                    str(existing.get("round_id", ""))
                )
            )
        )
        expected_id = f"{record['parent_round_id']}.S{len(sibling_numbers) + 1}"
        if sibling_numbers != list(range(1, len(sibling_numbers) + 1)):
            raise ValueError("Existing side rounds contain an ID gap")
        if record["round_id"] != expected_id:
            raise ValueError(f"The next side round for this parent must be {expected_id}")
    _atomic_write(path, records + [record])
