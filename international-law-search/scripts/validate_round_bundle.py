#!/usr/bin/env python3
"""Validate a shared research round bundle against its knowledge ledgers."""

import argparse
import json
from pathlib import Path
import re
import sys

from validate_source_ledger import _schema_errors


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "round-bundle.schema.json"
)
SUBSTANTIVE_REVIEW_EXTENTS = {
    "full_text_substantively_reviewed",
    "selected_sections_reviewed",
}
FILE_URI = re.compile(r"file://", re.IGNORECASE)
POSIX_ABSOLUTE_PATH = re.compile(
    r"(?<![:/A-Za-z0-9])/(?!/)[^\s<>()\[\]{}\"']+"
)
WINDOWS_ABSOLUTE_PATH = re.compile(
    r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|\\\\)[^\s<>()\[\]{}\"']+"
)


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


def _validate_schema(bundle: dict) -> list[str]:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"Unable to read round bundle schema: {exc}"]
    return _schema_errors(bundle, schema, schema, "Bundle")


def validate_bundle(
    bundle: dict,
    *,
    sources: list[dict],
    claims: list[dict],
    rounds: list[dict],
) -> list[str]:
    """Return schema, reference, evidence, privacy, and checkpoint errors."""

    errors = _validate_schema(bundle)
    if any(
        FILE_URI.search(value)
        or POSIX_ABSOLUTE_PATH.search(value)
        or WINDOWS_ABSOLUTE_PATH.search(value)
        for value in _strings(bundle)
    ):
        errors.append("Bundle contains a private local path")
    source_keys = {source.get("source_key") for source in sources}
    claim_ids = {claim.get("claim_id") for claim in claims}
    sources_by_key = {source.get("source_key"): source for source in sources}
    claims_by_id = {claim.get("claim_id"): claim for claim in claims}
    rounds_by_id = {
        round_record.get("round_id"): round_record
        for round_record in rounds
    }

    round_id = bundle.get("round_id")
    round_record = rounds_by_id.get(round_id)
    if round_record is None:
        errors.append(f"Unknown round_id {round_id!r} for bundle checkpoint")
    else:
        if bundle.get("research_question") != round_record.get("research_question"):
            errors.append(
                "Bundle research_question does not match the round checkpoint"
            )
        budget_fields = (
            "bibliographic_discovery",
            "full_text_acquisition",
            "substantive_review",
        )
        expected_budget = {
            field: round_record.get("actual_budget", {}).get(field)
            for field in budget_fields
        }
        if bundle.get("budget_summary") != expected_budget:
            errors.append(
                "Bundle budget_summary does not match the round actual_budget"
            )
        if bundle.get("next_round_options") != round_record.get(
            "next_round_options", []
        ):
            errors.append(
                "Bundle next_round_options do not match the round checkpoint"
            )

    referenced_source_keys = list(bundle.get("featured_source_keys", []))
    referenced_source_keys.extend(bundle.get("bibliography_selection", []))
    referenced_claim_ids = list(bundle.get("claim_ids", []))
    narrative_source_keys = []
    narrative_claim_ids = []
    for section in bundle.get("narrative_sections", []):
        if isinstance(section, dict):
            narrative_source_keys.extend(section.get("source_keys", []))
            narrative_claim_ids.extend(section.get("claim_ids", []))
    referenced_source_keys.extend(narrative_source_keys)
    referenced_claim_ids.extend(narrative_claim_ids)

    bibliography_selection = set(bundle.get("bibliography_selection", []))
    rendered_source_keys = set(bundle.get("featured_source_keys", [])) | set(
        narrative_source_keys
    )
    for source_key in sorted(rendered_source_keys - bibliography_selection):
        errors.append(
            f"Source {source_key!r} is used in the narrative but absent from "
            "bibliography_selection"
        )
    selected_claim_ids = set(bundle.get("claim_ids", []))
    for claim_id in sorted(set(narrative_claim_ids) - selected_claim_ids):
        errors.append(
            f"Narrative claim {claim_id!r} is absent from bundle claim_ids"
        )

    for source_key in dict.fromkeys(referenced_source_keys):
        if source_key not in source_keys:
            errors.append(f"Unknown source_key {source_key!r}")
    for claim_id in dict.fromkeys(referenced_claim_ids):
        if claim_id not in claim_ids:
            errors.append(f"Unknown claim_id {claim_id!r}")
            continue
        claim = claims_by_id[claim_id]
        status = claim.get("status")
        if status in {"revised", "superseded"}:
            errors.append(
                f"Claim {claim_id!r} is historical and cannot be a current bundle claim"
            )
        supporting = claim.get("supporting_evidence", [])
        contrary = claim.get("contrary_evidence", [])
        if (
            status in {"supported", "contested", "revised", "superseded"}
            and not supporting
        ):
            errors.append(f"Claim {claim_id!r} lacks sufficient supporting evidence")
        if status == "contested" and not contrary:
            errors.append(f"Claim {claim_id!r} lacks required contrary evidence")
        for evidence in [*supporting, *contrary]:
            if not isinstance(evidence, dict):
                errors.append(f"Claim {claim_id!r} contains malformed evidence")
                continue
            evidence_source_key = evidence.get("source_key")
            source = sources_by_key.get(evidence_source_key)
            if source is None:
                errors.append(
                    f"Claim {claim_id!r} evidence references unknown source_key "
                    f"{evidence_source_key!r}"
                )
            elif source.get("review_extent") not in SUBSTANTIVE_REVIEW_EXTENTS:
                errors.append(
                    f"Claim {claim_id!r} evidence source {evidence_source_key!r} "
                    "was not substantively reviewed"
                )
            locator = evidence.get("locator")
            if not isinstance(locator, str) or not locator.strip():
                errors.append(
                    f"Claim {claim_id!r} evidence requires a precise locator"
                )
    return errors


def _load_json_object(path: Path, label: str) -> tuple[dict | None, list[str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [f"Unable to read {label}: {exc}"]
    if not isinstance(value, dict):
        return None, [f"{label} must contain one JSON object"]
    return value, []


def _load_jsonl(path: Path, label: str) -> tuple[list[dict], list[str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return [], [f"Unable to read {label}: {exc}"]
    records = []
    errors = []
    for line_number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}:{line_number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"{path.name}:{line_number}: record must be an object")
            continue
        records.append(record)
    return records, errors


def validate_bundle_files(
    bundle_path: Path,
    *,
    source_path: Path,
    claim_path: Path,
    round_path: Path,
) -> list[str]:
    """Load and validate one bundle and its three JSONL knowledge ledgers."""

    bundle, errors = _load_json_object(Path(bundle_path), "round bundle")
    sources, source_errors = _load_jsonl(Path(source_path), "source ledger")
    claims, claim_errors = _load_jsonl(Path(claim_path), "claim ledger")
    rounds, round_errors = _load_jsonl(Path(round_path), "round ledger")
    errors.extend(source_errors)
    errors.extend(claim_errors)
    errors.extend(round_errors)
    if bundle is not None:
        errors.extend(
            validate_bundle(bundle, sources=sources, claims=claims, rounds=rounds)
        )
    return errors


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a shared research round bundle."
    )
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--claims", type=Path, required=True)
    parser.add_argument("--rounds", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    errors = validate_bundle_files(
        args.bundle,
        source_path=args.sources,
        claim_path=args.claims,
        round_path=args.rounds,
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print("Round bundle is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
