#!/usr/bin/env python3
from copy import deepcopy
import re
from typing import Optional
import unicodedata


ACCESS_RANK = {
    "Access failed": 0,
    "Full text not read": 1,
    "Metadata only": 2,
    "Abstract only": 3,
    "Full text read": 4,
}

IDENTITY_FIELDS = {"title", "creators", "date", "publication"}
UNION_FIELDS = (
    "aliases",
    "fields",
    "subquestions",
    "discovery_history",
)
DESCRIPTION_FIELDS = (
    "access_status",
    "description",
    "description_basis",
    "description_retrieval_id",
)


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").casefold()
    value = "".join(char if char.isalnum() else " " for char in value)
    return " ".join(value.split())


def normalize_doi(value: str) -> str:
    value = value.strip().casefold()
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", value)


def identity_key(record: dict) -> Optional[str]:
    external_ids = {
        key.casefold(): value
        for key, value in record.get("external_ids", {}).items()
    }
    if external_ids.get("doi"):
        doi = normalize_doi(external_ids["doi"])
        if doi:
            return f"doi:{doi}"
    for key in (
        "formal_citation",
        "case_number",
        "treaty_number",
        "document_number",
    ):
        if external_ids.get(key):
            publication = normalize_text(str(record.get("publication", "") or ""))
            creators = normalize_text(" ".join(record.get("creators", [])))
            namespace = publication or creators
            identifier = normalize_text(str(external_ids[key]))
            if namespace and identifier:
                return f"{key}:{namespace}:{identifier}"
    title = normalize_text(str(record.get("title", "")))
    date = normalize_text(str(record.get("date", "") or ""))
    creators = normalize_text(" ".join(record.get("creators", [])))
    if title and date and creators:
        return f"meta:{title}|{date}|{creators}"
    return None


def validate_retrieval_links(record: dict) -> None:
    has_history = "retrieval_history" in record
    has_description_link = "description_retrieval_id" in record
    if not has_history and not has_description_link:
        return
    if not has_history or not has_description_link:
        raise ValueError(
            "retrieval_history and description_retrieval_id must appear together"
        )

    events_by_id = {}
    for event in record["retrieval_history"]:
        event_id = event.get("event_id")
        if event_id in events_by_id:
            raise ValueError(f"Duplicate retrieval event_id: {event_id!r}")
        events_by_id[event_id] = event

    description_id = record["description_retrieval_id"]
    event = events_by_id.get(description_id)
    if event is None:
        raise ValueError(
            "description_retrieval_id must resolve to exactly one retrieval event"
        )
    if event.get("access_status") != record.get("access_status"):
        raise ValueError(
            "Description retrieval access_status must equal canonical access_status"
        )

    basis = record.get("description_basis")
    access_status = record.get("access_status")
    if basis == "full_text" and access_status != "Full text read":
        raise ValueError("full_text descriptions require Full text read access")
    if basis == "abstract" and access_status not in {
        "Abstract only",
        "Full text read",
    }:
        raise ValueError(
            "abstract descriptions require Abstract only or Full text read access"
        )


def _append_unique(target: list, values: list) -> None:
    for value in values:
        if value not in target:
            target.append(deepcopy(value))


def _conflict_candidate(value, record_id: str) -> dict:
    return {"value": deepcopy(value), "source_record_id": record_id}


def _add_conflict(
    merged: dict,
    field: str,
    left_value,
    left_id: str,
    right_value,
    right_id: str,
) -> None:
    candidates = merged.setdefault("merge_conflicts", {}).setdefault(field, [])
    _append_unique(
        candidates,
        [
            _conflict_candidate(left_value, left_id),
            _conflict_candidate(right_value, right_id),
        ],
    )


def _external_id_value(key: str, value: str) -> str:
    if key.casefold() == "doi":
        return normalize_doi(str(value))
    return normalize_text(str(value))


def _merge_retrieval_history(merged: dict, right: dict) -> None:
    if "retrieval_history" not in right:
        return
    history = merged.setdefault("retrieval_history", [])
    events_by_id = {event.get("event_id"): event for event in history}
    for event in right["retrieval_history"]:
        event_id = event.get("event_id")
        existing = events_by_id.get(event_id)
        if existing is None:
            copied = deepcopy(event)
            history.append(copied)
            events_by_id[event_id] = copied
        elif existing != event:
            raise ValueError(f"retrieval event_id collision: {event_id!r}")


def merge_records(left: dict, right: dict) -> dict:
    validate_retrieval_links(left)
    validate_retrieval_links(right)

    left_key = identity_key(left)
    right_key = identity_key(right)
    if left_key is None or right_key is None:
        raise ValueError("Both records must have a sufficient identity key")
    if left_key != right_key:
        raise ValueError("Record identity keys do not match")

    merged = deepcopy(left)
    left_id = str(left["id"])
    right_id = str(right["id"])
    has_conflict = bool(merged.get("merge_conflicts"))
    has_identity_conflict = any(
        field in IDENTITY_FIELDS or field.startswith("external_ids.")
        for field in merged.get("merge_conflicts", {})
    )

    aliases = merged.setdefault("aliases", [])
    _append_unique(aliases, right.get("aliases", []))
    if right_id != left_id:
        _append_unique(aliases, [right_id])

    for field in UNION_FIELDS:
        if field == "aliases":
            continue
        if field in right:
            _append_unique(merged.setdefault(field, []), right[field])
    _merge_retrieval_history(merged, right)

    external_ids = merged.setdefault("external_ids", {})
    external_keys = {key.casefold(): key for key in external_ids}
    for right_name, right_value in right.get("external_ids", {}).items():
        folded_name = right_name.casefold()
        if folded_name not in external_keys:
            external_ids[right_name] = deepcopy(right_value)
            external_keys[folded_name] = right_name
            continue
        left_name = external_keys[folded_name]
        left_value = external_ids[left_name]
        if _external_id_value(folded_name, left_value) != _external_id_value(
            folded_name, right_value
        ):
            _add_conflict(
                merged,
                f"external_ids.{folded_name}",
                left_value,
                left_id,
                right_value,
                right_id,
            )
            has_conflict = True
            has_identity_conflict = True

    left_rank = ACCESS_RANK.get(left.get("access_status"), -1)
    right_rank = ACCESS_RANK.get(right.get("access_status"), -1)
    if right_rank > left_rank:
        for field in DESCRIPTION_FIELDS:
            if field in right:
                merged[field] = deepcopy(right[field])

    for field, value in right.items():
        if (
            field in UNION_FIELDS
            or field in DESCRIPTION_FIELDS
            or field
            in {
                "id",
                "external_ids",
                "merge_conflicts",
                "retrieval_history",
                "verification",
            }
        ):
            continue
        if field not in merged or merged[field] in (None, "", [], {}):
            merged[field] = deepcopy(value)
        elif field in {"stable_url", "local_path"}:
            continue
        elif merged[field] != value:
            has_conflict = True
            _add_conflict(
                merged,
                field,
                merged[field],
                left_id,
                value,
                right_id,
            )
            if field in IDENTITY_FIELDS:
                has_identity_conflict = True

    for field, candidates in right.get("merge_conflicts", {}).items():
        _append_unique(
            merged.setdefault("merge_conflicts", {}).setdefault(field, []),
            candidates,
        )
        has_conflict = True
        if field in IDENTITY_FIELDS or field.startswith("external_ids."):
            has_identity_conflict = True

    verification = merged.setdefault("verification", {})
    right_verification = right.get("verification", {})
    if right_verification.get("human_review_required"):
        verification["human_review_required"] = True
    if right_verification.get("identity") == "conflict":
        verification["identity"] = "conflict"
    if right_verification.get("metadata_cross_checked") is False:
        verification["metadata_cross_checked"] = False
    if has_conflict:
        verification["metadata_cross_checked"] = False
        verification["human_review_required"] = True
    if has_identity_conflict:
        verification["identity"] = "conflict"
    validate_retrieval_links(merged)
    return merged
