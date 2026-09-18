#!/usr/bin/env python3
"""Deterministic identity and upsert operations for the source ledger."""

from copy import deepcopy
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata


DOI_PREFIX = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)
ISBN_LABEL = re.compile(r"^isbn(?:-1[03])?:?", re.IGNORECASE)

AVAILABILITY_RANK = {
    "access_failure": 0,
    "metadata_only": 1,
    "abstract_available": 2,
    "identified_inaccessible": 3,
    "subscription_full_text": 4,
    "open_full_text": 5,
}
REVIEW_RANK = {
    "not_reviewed": 0,
    "metadata_verified": 1,
    "abstract_reviewed": 2,
    "selected_sections_reviewed": 3,
    "full_text_substantively_reviewed": 4,
}


def _normalize_text(value) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = "".join(character if character.isalnum() else " " for character in text)
    return " ".join(text.split())


def _normalize_doi(value) -> str:
    return DOI_PREFIX.sub("", str(value or "").strip()).rstrip(". ").casefold()


def _normalize_isbn(value) -> str:
    value = ISBN_LABEL.sub("", str(value or "").strip())
    normalized = "".join(
        character
        for character in value.upper()
        if character.isdigit() or character == "X"
    )
    if (
        len(normalized) == 10
        and normalized[:9].isdigit()
        and (normalized[9].isdigit() or normalized[9] == "X")
    ):
        stem = f"978{normalized[:9]}"
        checksum = (10 - sum(
            int(character) * (1 if index % 2 == 0 else 3)
            for index, character in enumerate(stem)
        ) % 10) % 10
        return f"{stem}{checksum}"
    return normalized


def _identifier(record: dict, *names: str):
    identifiers = record.get("identifiers") or {}
    folded = {str(key).casefold(): value for key, value in identifiers.items()}
    for name in names:
        value = folded.get(name.casefold())
        if value not in (None, ""):
            return value
    details = record.get("source_details") or {}
    detail_fields = {str(key).casefold(): value for key, value in details.items()}
    for name in names:
        value = detail_fields.get(name.casefold())
        if value not in (None, ""):
            return value
    return None


def _identity_field(record: dict, field: str):
    identity = record.get("identity_evidence") or {}
    return identity.get(field)


def _source_namespace(record: dict, *detail_fields: str) -> str:
    details = record.get("source_details") or {}
    context = record.get("legal_status_context") or {}
    candidates = [
        *(details.get(field) for field in detail_fields),
        context.get("issuing_authority"),
        _identity_field(record, "publication"),
    ]
    return next((_normalize_text(value) for value in candidates if _normalize_text(value)), "")


def normalized_identity_keys(record: dict) -> list[str]:
    """Return strongest-first, type-aware normalized identity keys."""

    keys = []
    doi = _normalize_doi(_identifier(record, "doi"))
    if doi:
        keys.append(f"doi:{doi}")

    source_type = _normalize_text(record.get("source_type")) or "unknown"
    strong_specs = (
        ("official_document", ("official_document_number", "document_number"), ("organization", "organ")),
        ("case", ("case_number",), ("court",)),
        ("treaty", ("treaty_number", "treaty_identifier"), ("depositary",)),
        ("publisher", ("publisher_id", "stable_publisher_id"), ("publisher", "journal")),
    )
    for label, names, namespace_fields in strong_specs:
        value = _identifier(record, *names)
        if value in (None, ""):
            continue
        namespace = _source_namespace(record, *namespace_fields)
        normalized_value = _normalize_text(value)
        if namespace and normalized_value:
            keys.append(f"{label}:{namespace}:{normalized_value}")

    isbn = _normalize_isbn(_identifier(record, "isbn", "isbn_10", "isbn_13"))
    if isbn:
        details = record.get("source_details") or {}
        edition = _normalize_text(details.get("edition")) or "unspecified"
        keys.append(f"isbn:{isbn}:edition:{edition}")

    title = _normalize_text(_identity_field(record, "normalized_title"))
    creators = sorted(
        filter(None, (_normalize_text(value) for value in (_identity_field(record, "creators") or [])))
    )
    date = _normalize_text(_identity_field(record, "publication_date"))
    if title and creators and date and source_type != "unknown":
        keys.append(f"metadata:{source_type}:{title}|{'|'.join(creators)}|{date}")

    return list(dict.fromkeys(keys))


def _append_unique(target: list, values: list) -> None:
    for value in values:
        if value not in target:
            target.append(deepcopy(value))


def _records_match(left: dict, right: dict) -> bool:
    left_keys = normalized_identity_keys(left)
    right_keys = normalized_identity_keys(right)
    for family in (
        "doi:",
        "official_document:",
        "case:",
        "treaty:",
        "isbn:",
        "publisher:",
    ):
        left_family = {key for key in left_keys if key.startswith(family)}
        right_family = {key for key in right_keys if key.startswith(family)}
        if left_family and right_family:
            return bool(left_family.intersection(right_family))
    left_metadata = {key for key in left_keys if key.startswith("metadata:")}
    right_metadata = {key for key in right_keys if key.startswith("metadata:")}
    return bool(left_metadata.intersection(right_metadata))


def _equivalent(field: str, left, right) -> bool:
    if field == "identifiers.doi":
        return _normalize_doi(left) == _normalize_doi(right)
    if field.startswith("identifiers.isbn"):
        return _normalize_isbn(left) == _normalize_isbn(right)
    if field == "identity_evidence.normalized_title":
        return _normalize_text(left) == _normalize_text(right)
    if field == "identity_evidence.creators":
        return sorted(_normalize_text(item) for item in left) == sorted(
            _normalize_text(item) for item in right
        )
    return left == right


def _add_conflict(
    merged: dict,
    field: str,
    left,
    left_key: str,
    right,
    right_key: str,
) -> None:
    candidates = merged.setdefault("metadata_conflicts", {}).setdefault(field, [])
    _append_unique(
        candidates,
        [
            {"value": deepcopy(left), "source_key": left_key},
            {"value": deepcopy(right), "source_key": right_key},
        ],
    )


def _merge_round_membership(merged: dict, incoming: dict) -> None:
    if "round_membership" not in incoming:
        return
    memberships = merged.setdefault("round_membership", [])
    by_round = {
        item.get("round_id"): item
        for item in memberships
        if isinstance(item, dict) and item.get("round_id")
    }
    for item in incoming["round_membership"]:
        round_id = item.get("round_id") if isinstance(item, dict) else None
        existing = by_round.get(round_id)
        if existing is None:
            copied = deepcopy(item)
            memberships.append(copied)
            if round_id:
                by_round[round_id] = copied
        else:
            _append_unique(existing.setdefault("functions", []), item.get("functions", []))


def _merge_existing_conflicts(merged: dict, incoming: dict) -> None:
    for field, candidates in (incoming.get("metadata_conflicts") or {}).items():
        _append_unique(
            merged.setdefault("metadata_conflicts", {}).setdefault(field, []),
            candidates,
        )


def _merge_record(existing: dict, incoming: dict) -> dict:
    merged = deepcopy(existing)
    union_fields = (
        "discovery_provenance",
        "links",
        "local_paths",
        "user_decisions",
        "retrieval_history",
        "version_relationships",
        "acquisition_routes",
        "source_key_aliases",
        "citation_aliases",
    )
    for field in union_fields:
        if field in incoming:
            _append_unique(merged.setdefault(field, []), incoming[field])
    _merge_round_membership(merged, incoming)
    _merge_existing_conflicts(merged, incoming)

    incoming_key = incoming.get("source_key")
    if incoming_key and incoming_key != existing.get("source_key"):
        _append_unique(merged.setdefault("source_key_aliases", []), [incoming_key])

    incoming_citation = (incoming.get("identity_evidence") or {}).get("raw_citation")
    existing_citation = (existing.get("identity_evidence") or {}).get("raw_citation")
    if incoming_citation and incoming_citation != existing_citation:
        _append_unique(merged.setdefault("citation_aliases", []), [incoming_citation])

    existing_key = str(existing.get("source_key"))
    incoming_key = str(incoming.get("source_key"))
    incoming_identifiers = incoming.get("identifiers") or {}
    merged_identifiers = (
        merged.setdefault("identifiers", {})
        if incoming_identifiers
        else merged.get("identifiers", {})
    )
    for name, value in incoming_identifiers.items():
        existing_name = next(
            (candidate for candidate in merged_identifiers if candidate.casefold() == name.casefold()),
            None,
        )
        if existing_name is None:
            merged_identifiers[name] = deepcopy(value)
        elif not _equivalent(
            f"identifiers.{name.casefold()}",
            merged_identifiers[existing_name],
            value,
        ):
            _add_conflict(
                merged,
                f"identifiers.{name.casefold()}",
                merged_identifiers[existing_name],
                existing_key,
                value,
                incoming_key,
            )

    for field, value in incoming.items():
        if field in union_fields or field in {
            "source_key",
            "identity_evidence",
            "identifiers",
            "metadata_conflicts",
            "round_membership",
        }:
            continue
        if field not in merged or merged[field] in (None, "", [], {}):
            merged[field] = deepcopy(value)

    merged_identity = merged.setdefault("identity_evidence", {})
    incoming_identity = incoming.get("identity_evidence") or {}
    if "evidence" in incoming_identity:
        _append_unique(merged_identity.setdefault("evidence", []), incoming_identity["evidence"])
    for field, value in incoming_identity.items():
        if field == "evidence":
            continue
        if field not in merged_identity or merged_identity[field] in (None, "", [], {}):
            merged_identity[field] = deepcopy(value)
        elif not _equivalent(
            f"identity_evidence.{field}", merged_identity[field], value
        ):
            _add_conflict(
                merged,
                f"identity_evidence.{field}",
                merged_identity[field],
                existing_key,
                value,
                incoming_key,
            )

    if AVAILABILITY_RANK.get(incoming.get("availability"), -1) > AVAILABILITY_RANK.get(
        merged.get("availability"), -1
    ):
        merged["availability"] = incoming["availability"]
    if REVIEW_RANK.get(incoming.get("review_extent"), -1) > REVIEW_RANK.get(
        merged.get("review_extent"), -1
    ):
        merged["review_extent"] = incoming["review_extent"]
        for field in ("description_basis", "description"):
            if field in incoming:
                merged[field] = deepcopy(incoming[field])
    return merged


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f"Line {line_number}: source record must be an object")
        records.append(record)
    return records


def _atomic_write(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            for record in records:
                stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
                stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary_path.replace(path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def upsert_source(path: Path, incoming: dict) -> dict:
    """Atomically insert or merge one record and return action plus stable key."""

    path = Path(path)
    if not isinstance(incoming, dict):
        raise TypeError("incoming source must be an object")
    source_key = incoming.get("source_key")
    if not isinstance(source_key, str) or not source_key.strip():
        raise ValueError("incoming source_key must be a non-empty string")

    records = _read_jsonl(path)
    matches = [
        index
        for index, record in enumerate(records)
        if record.get("source_key") == source_key
        or _records_match(record, incoming)
    ]
    if len(matches) > 1:
        raise ValueError("Incoming source matches multiple ledger records")

    if matches:
        index = matches[0]
        merged = _merge_record(records[index], incoming)
        action = "unchanged" if merged == records[index] else "merged"
        records[index] = merged
        stable_key = merged["source_key"]
    else:
        records.append(deepcopy(incoming))
        action = "inserted"
        stable_key = source_key

    _atomic_write(path, records)
    return {"action": action, "source_key": stable_key}
