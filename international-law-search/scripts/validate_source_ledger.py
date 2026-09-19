#!/usr/bin/env python3
"""Validate a Standard-mode source ledger and its cross-record invariants."""

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "source-ledger-record.schema.json"
LEDGER_OPS_PATH = Path(__file__).with_name("ledger_ops.py")


def _load_ledger_ops():
    spec = importlib.util.spec_from_file_location("source_ledger_ops", LEDGER_OPS_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LEDGER_OPS = _load_ledger_ops()

REVIEW_RANK = {
    "not_reviewed": 0,
    "metadata_verified": 1,
    "abstract_reviewed": 2,
    "selected_sections_reviewed": 3,
    "full_text_substantively_reviewed": 4,
}
DESCRIPTION_MINIMUM_REVIEW = {
    "metadata": "metadata_verified",
    "abstract": "abstract_reviewed",
    "selected_sections": "selected_sections_reviewed",
    "full_text": "full_text_substantively_reviewed",
}
ABSOLUTE_POSIX_PATH = re.compile(r"^/(?!/)")
ABSOLUTE_WINDOWS_PATH = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")


class LedgerReadError(Exception):
    """Raised when the ledger or its bundled schema cannot be read."""


def _matches_type(value, expected) -> bool:
    if isinstance(expected, list):
        return any(_matches_type(value, item) for item in expected)
    checks = {
        "null": lambda item: item is None,
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "boolean": lambda item: isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
    }
    return expected in checks and checks[expected](value)


def _resolve_ref(root_schema: dict, reference: str) -> dict:
    if not reference.startswith("#/"):
        raise ValueError(f"Unsupported schema reference: {reference}")
    current = root_schema
    for component in reference[2:].split("/"):
        current = current[component.replace("~1", "/").replace("~0", "~")]
    return current


def _condition_matches(value, condition: dict, root_schema: dict) -> bool:
    return not _schema_errors(value, condition, root_schema, "$", probe=True)


def _schema_errors(
    value, schema: dict, root_schema: dict, location: str, probe=False
) -> list[str]:
    if "$ref" in schema:
        schema = _resolve_ref(root_schema, schema["$ref"])
    errors = []
    if "type" in schema and not _matches_type(value, schema["type"]):
        return [f"{location}: expected type {schema['type']!r}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: unsupported value {value!r}")
    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: value must equal {schema['const']!r}")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        errors.append(f"{location}: string is shorter than minLength")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{location}: array is shorter than minItems")
        if schema.get("uniqueItems"):
            serialized = [
                json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value
            ]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{location}: array items must be unique")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(
                    _schema_errors(
                        item,
                        item_schema,
                        root_schema,
                        f"{location}[{index}]",
                        probe,
                    )
                )
    if isinstance(value, dict):
        for name in schema.get("required", []):
            if name not in value:
                errors.append(f"{location}: required property {name!r} is missing")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for name, item in value.items():
            if name in properties:
                errors.extend(
                    _schema_errors(
                        item,
                        properties[name],
                        root_schema,
                        f"{location}.{name}",
                        probe,
                    )
                )
            elif additional is False:
                errors.append(f"{location}: unsupported property {name!r}")
            elif isinstance(additional, dict):
                errors.extend(
                    _schema_errors(
                        item,
                        additional,
                        root_schema,
                        f"{location}.{name}",
                        probe,
                    )
                )
    if "oneOf" in schema:
        matches = [
            candidate
            for candidate in schema["oneOf"]
            if not _schema_errors(value, candidate, root_schema, location, probe=True)
        ]
        if len(matches) != 1:
            errors.append(f"{location}: value must match exactly one allowed shape")
    for condition in schema.get("allOf", []):
        if "if" in condition and _condition_matches(value, condition["if"], root_schema):
            errors.extend(_schema_errors(value, condition.get("then", {}), root_schema, location, probe))
        elif "if" not in condition:
            errors.extend(_schema_errors(value, condition, root_schema, location, probe))
    return errors


def _read_records(path: Path) -> list[tuple[int, object, str | None]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise LedgerReadError(f"Unable to read source ledger: {exc}") from exc
    records = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            records.append((line_number, None, exc.msg))
            continue
        records.append((line_number, record, None))
    return records


def _is_local_path(value) -> bool:
    return isinstance(value, str) and (
        value.casefold().startswith("file://")
        or ABSOLUTE_POSIX_PATH.match(value)
        or ABSOLUTE_WINDOWS_PATH.match(value)
    )


def _record_errors(record: dict, schema: dict, line_number: int) -> list[str]:
    prefix = f"Line {line_number}"
    errors = _schema_errors(record, schema, schema, prefix)
    basis = record.get("description_basis")
    if isinstance(basis, dict):
        kind = basis.get("kind")
        minimum = DESCRIPTION_MINIMUM_REVIEW.get(kind)
        actual = record.get("review_extent")
        if kind == "none" and actual != "not_reviewed":
            errors.append(
                f"{prefix}: unsupported description evidence; "
                "'none' requires 'not_reviewed'"
            )
        elif kind == "none":
            pass
        elif minimum is None:
            errors.append(
                f"{prefix}: unsupported description evidence; unknown basis {kind!r}"
            )
        elif (
            actual not in REVIEW_RANK or REVIEW_RANK[actual] < REVIEW_RANK[minimum]
        ):
            errors.append(
                f"{prefix}: unsupported description evidence; {kind!r} requires {minimum!r}"
            )
    for route in record.get("acquisition_routes", []):
        if isinstance(route, dict) and _is_local_path(route.get("local_path")):
            if route.get("externalizable") is not False:
                errors.append(f"{prefix}: externalizable local paths are prohibited")
    for provenance in record.get("discovery_provenance", []):
        if isinstance(provenance, dict) and provenance.get("externalizable") is True:
            if _is_local_path(provenance.get("locator")):
                errors.append(f"{prefix}: externalizable local paths are prohibited")
    return errors


def validate_source_ledger(path: Path) -> list[str]:
    """Return deterministic schema and cross-record errors for one JSONL ledger."""

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LedgerReadError(f"Unable to read source schema: {exc}") from exc

    records = _read_records(Path(path))
    errors = []
    source_keys = {}
    strong_identities = {}
    for line_number, record, parse_error in records:
        if parse_error is not None:
            errors.append(f"Line {line_number}: invalid JSON: {parse_error}")
            continue
        if not isinstance(record, dict):
            errors.append(f"Line {line_number}: each JSONL item must be an object")
            continue
        errors.extend(_record_errors(record, schema, line_number))
        source_key = record.get("source_key")
        if isinstance(source_key, str):
            if source_key in source_keys:
                errors.append(
                    f"Line {line_number}: duplicate source_key {source_key!r}; "
                    f"first seen on line {source_keys[source_key]}"
                )
            else:
                source_keys[source_key] = line_number
        for identity in LEDGER_OPS.normalized_identity_keys(record):
            if identity.startswith("metadata:"):
                continue
            if identity in strong_identities:
                errors.append(
                    f"Line {line_number}: duplicate strong identity {identity!r}; "
                    f"first seen on line {strong_identities[identity]}"
                )
            else:
                strong_identities[identity] = line_number
    return errors


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Validate a Standard source ledger.")
    parser.add_argument("path", type=Path)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        errors = validate_source_ledger(args.path)
    except LedgerReadError as exc:
        print(exc, file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print("Source ledger is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
