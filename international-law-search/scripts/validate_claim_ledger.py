#!/usr/bin/env python3
"""Validate evidence and revision invariants across claim and source ledgers."""

import argparse
import json
from pathlib import Path
import sys


SUBSTANTIVE_REVIEW_EXTENTS = {
    "full_text_substantively_reviewed",
    "selected_sections_reviewed",
}
CLAIM_STATUSES = {
    "provisional",
    "supported",
    "contested",
    "revised",
    "superseded",
}
EVIDENCE_FUNCTIONS = {
    "direct_support",
    "interpretive_support",
    "qualification",
    "contrary_authority",
    "counterexample",
    "context",
}
EVIDENCE_FIELDS = {
    "source_key",
    "locator",
    "evidence_function",
    "review_basis",
}
REVIEW_RANK = {
    "not_reviewed": 0,
    "metadata_verified": 1,
    "abstract_reviewed": 2,
    "selected_sections_reviewed": 3,
    "full_text_substantively_reviewed": 4,
}
REQUIRED_CLAIM_FIELDS = (
    "claim_id",
    "claim_text",
    "claim_type",
    "scope",
    "status",
    "first_seen_round",
    "last_verified_round",
    "supporting_evidence",
    "contrary_evidence",
    "predecessor_claim_ids",
    "successor_claim_ids",
    "reader_qualification",
)
NONEMPTY_CLAIM_STRING_FIELDS = (
    "claim_text",
    "claim_type",
    "scope",
    "first_seen_round",
    "reader_qualification",
)
CLAIM_ID_LIST_FIELDS = (
    "predecessor_claim_ids",
    "successor_claim_ids",
)


def _load_jsonl(path):
    records = []
    errors = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return records, [f"{path}: unable to read file: {exc}"]

    for line_number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip():
            continue
        location = f"{path.name}:{line_number}"
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append(f"{location}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"{location}: each JSONL record must be an object")
            continue
        records.append(record)
    return records, errors


def current_claim_ids(claims) -> set[str]:
    """Return IDs of claims eligible to appear as current conclusions."""

    return {
        claim.get("claim_id")
        for claim in claims
        if claim.get("status") not in {"revised", "superseded"}
        and isinstance(claim.get("claim_id"), str)
        and claim.get("claim_id").strip()
    }


def validate_records(claims, sources, claim_name="claims.jsonl") -> list[str]:
    """Return claim-ledger errors for already parsed records."""

    errors = []
    sources_by_key = {
        source.get("source_key"): source
        for source in sources
        if isinstance(source.get("source_key"), str)
    }

    seen_claim_ids = set()
    for index, claim in enumerate(claims, start=1):
        location = f"{claim_name}:{index}"
        additional_fields = sorted(set(claim) - set(REQUIRED_CLAIM_FIELDS))
        if additional_fields:
            errors.append(
                f"{location}: unsupported claim fields: "
                f"{', '.join(additional_fields)}"
            )
        for field in REQUIRED_CLAIM_FIELDS:
            if field not in claim:
                errors.append(f"{location}: {field} is required")
        for field in NONEMPTY_CLAIM_STRING_FIELDS:
            value = claim.get(field)
            if field in claim and (
                not isinstance(value, str) or not value.strip()
            ):
                errors.append(
                    f"{location}: {field} must be a non-empty string"
                )
        for field in CLAIM_ID_LIST_FIELDS:
            values = claim.get(field)
            if field in claim and not isinstance(values, list):
                errors.append(f"{location}: {field} must be an array")
            elif isinstance(values, list):
                seen_values = set()
                for value in values:
                    if not isinstance(value, str) or not value.strip():
                        errors.append(
                            f"{location}: {field} items must be non-empty strings"
                        )
                    elif value in seen_values:
                        errors.append(
                            f"{location}: {field} must contain unique IDs"
                        )
                    else:
                        seen_values.add(value)
        if claim.get("status") not in CLAIM_STATUSES:
            errors.append(
                f"{location}: unsupported status {claim.get('status')!r}"
            )
        last_verified_round = claim.get("last_verified_round")
        if last_verified_round is not None and (
            not isinstance(last_verified_round, str)
            or not last_verified_round.strip()
        ):
            errors.append(
                f"{location}: last_verified_round must be a string or null"
            )
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id.strip():
            errors.append(f"{location}: claim_id must be a non-empty string")
        elif claim_id in seen_claim_ids:
            errors.append(
                f"{claim_name}:{index}: duplicate claim_id {claim_id!r}"
            )
        else:
            seen_claim_ids.add(claim_id)

    claims_by_id = {
        claim.get("claim_id"): claim
        for claim in claims
        if isinstance(claim.get("claim_id"), str)
        and claim.get("claim_id").strip()
    }
    for index, claim in enumerate(claims, start=1):
        location = f"{claim_name}:{index}"
        claim_id = claim.get("claim_id")
        successor_ids = claim.get("successor_claim_ids", [])
        if not isinstance(successor_ids, list):
            successor_ids = []
        else:
            successor_ids = [
                value
                for value in successor_ids
                if isinstance(value, str) and value.strip()
            ]
        predecessor_ids = claim.get("predecessor_claim_ids", [])
        if not isinstance(predecessor_ids, list):
            predecessor_ids = []
        else:
            predecessor_ids = [
                value
                for value in predecessor_ids
                if isinstance(value, str) and value.strip()
            ]
        if claim.get("status") in {"revised", "superseded"} and not successor_ids:
            errors.append(
                f"{location}: {claim.get('status')} claim requires a successor"
            )
        for successor_id in successor_ids:
            successor = claims_by_id.get(successor_id)
            if successor is None:
                errors.append(
                    f"{location}: unknown successor claim_id {successor_id!r}"
                )
            else:
                reciprocal_ids = successor.get("predecessor_claim_ids", [])
                if not isinstance(reciprocal_ids, list):
                    reciprocal_ids = []
                if claim_id in reciprocal_ids:
                    continue
                errors.append(
                    f"{location}: successor link to {successor_id!r} is not reciprocal"
                )
        for predecessor_id in predecessor_ids:
            predecessor = claims_by_id.get(predecessor_id)
            if predecessor is None:
                errors.append(
                    f"{location}: unknown predecessor claim_id {predecessor_id!r}"
                )
            else:
                reciprocal_ids = predecessor.get("successor_claim_ids", [])
                if not isinstance(reciprocal_ids, list):
                    reciprocal_ids = []
                if claim_id in reciprocal_ids:
                    continue
                errors.append(
                    f"{location}: predecessor link to {predecessor_id!r} is not reciprocal"
                )

    visited = set()
    active = set()

    def visit(claim_id):
        if claim_id in active:
            return claim_id
        if claim_id in visited:
            return None
        active.add(claim_id)
        successor_ids = claims_by_id[claim_id].get("successor_claim_ids", [])
        if not isinstance(successor_ids, list):
            successor_ids = []
        for successor_id in successor_ids:
            if successor_id in claims_by_id:
                cycle_at = visit(successor_id)
                if cycle_at is not None:
                    return cycle_at
        active.remove(claim_id)
        visited.add(claim_id)
        return None

    for claim_id in claims_by_id:
        cycle_at = visit(claim_id)
        if cycle_at is not None:
            errors.append(
                f"{claim_name}: revision cycle detected at {cycle_at!r}"
            )
            break

    for index, claim in enumerate(claims, start=1):
        location = f"{claim_name}:{index}"
        status = claim.get("status")
        if status in {"supported", "contested"} and (
            not isinstance(claim.get("last_verified_round"), str)
            or not claim.get("last_verified_round").strip()
        ):
            errors.append(
                f"{location}: {status} claim requires last_verified_round"
            )
        supporting_evidence = claim.get("supporting_evidence", [])
        if not isinstance(supporting_evidence, list):
            errors.append(f"{location}: supporting_evidence must be an array")
            supporting_evidence = []
        contrary_evidence = claim.get("contrary_evidence", [])
        if not isinstance(contrary_evidence, list):
            errors.append(f"{location}: contrary_evidence must be an array")
            contrary_evidence = []
        if status in {"supported", "contested"} and not supporting_evidence:
            errors.append(
                f"{location}: {status} claim requires supporting evidence"
            )
        if status == "contested" and not contrary_evidence:
            errors.append(
                f"{location}: contested claim requires contrary evidence"
            )
        for item in supporting_evidence + contrary_evidence:
            if not isinstance(item, dict):
                errors.append(f"{location}: evidence must be an object")
                continue
            for field in sorted(EVIDENCE_FIELDS):
                if field not in item:
                    errors.append(f"{location}: evidence {field} is required")
            additional_fields = sorted(set(item) - EVIDENCE_FIELDS)
            if additional_fields:
                errors.append(
                    f"{location}: unsupported evidence fields: "
                    f"{', '.join(additional_fields)}"
                )
            source_key = item.get("source_key")
            if not isinstance(source_key, str) or not source_key.strip():
                errors.append(
                    f"{location}: evidence source_key must be a non-empty string"
                )
            locator = item.get("locator")
            if not isinstance(locator, str) or not locator.strip():
                errors.append(
                    f"{location}: claim evidence requires a precise locator"
                )
            review_basis = item.get("review_basis")
            if review_basis not in SUBSTANTIVE_REVIEW_EXTENTS:
                errors.append(
                    f"{location}: evidence has invalid review_basis {review_basis!r}"
                )
            evidence_function = item.get("evidence_function")
            if evidence_function not in EVIDENCE_FUNCTIONS:
                errors.append(
                    f"{location}: evidence has invalid evidence_function "
                    f"{evidence_function!r}"
                )
            source = sources_by_key.get(source_key)
            if source is None:
                errors.append(
                    f"{location}: evidence references unknown source_key "
                    f"{source_key!r}"
                )
            elif source.get("review_extent") not in SUBSTANTIVE_REVIEW_EXTENTS:
                errors.append(
                    f"{location}: claim evidence requires reviewed evidence "
                    "from substantive source content"
                )
            elif REVIEW_RANK.get(review_basis, -1) > REVIEW_RANK.get(
                source.get("review_extent"), -1
            ):
                errors.append(
                    f"{location}: evidence review_basis overstates source review_extent"
                )
    return errors


def validate_claim_ledger(claim_path: Path, source_path: Path) -> list[str]:
    """Return deterministic evidence and revision errors without mutation."""

    claims, errors = _load_jsonl(claim_path)
    sources, source_errors = _load_jsonl(source_path)
    errors.extend(source_errors)
    errors.extend(validate_records(claims, sources, claim_path.name))
    return errors


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate claim evidence against a source ledger."
    )
    parser.add_argument("--claims", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    errors = validate_claim_ledger(args.claims, args.sources)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print("Claim ledger is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
