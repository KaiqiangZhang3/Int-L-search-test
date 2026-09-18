#!/usr/bin/env python3
from copy import deepcopy
import re
from typing import Optional
import unicodedata


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

IDENTITY_FIELDS = {"title", "creators", "date", "publication"}
UNION_FIELDS = (
    "aliases",
    "fields",
    "subquestions",
    "discovery_history",
)
DESCRIPTION_FIELDS = (
    "description",
    "description_basis",
    "description_retrieval_id",
)
ACCESS_AXIS_FIELDS = ("availability", "review_extent")

DESCRIPTION_MINIMUM_REVIEW = {
    "metadata": "metadata_verified",
    "abstract": "abstract_reviewed",
    "selected_sections": "selected_sections_reviewed",
    "full_text": "full_text_substantively_reviewed",
}

ROUTE_MAXIMUM_REVIEW = {
    "access_failure": "not_reviewed",
    "metadata_only": "metadata_verified",
    "abstract_available": "abstract_reviewed",
    "identified_inaccessible": "abstract_reviewed",
    "subscription_full_text": "full_text_substantively_reviewed",
    "open_full_text": "full_text_substantively_reviewed",
}


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
        event_availability = event.get("availability")
        event_review = event.get("review_extent")
        maximum_review = ROUTE_MAXIMUM_REVIEW.get(event_availability)
        if (
            maximum_review is None
            or event_review not in REVIEW_RANK
            or REVIEW_RANK[event_review] > REVIEW_RANK[maximum_review]
        ):
            raise ValueError(
                f"Retrieval route {event_availability!r} cannot support "
                f"review extent {event_review!r}"
            )
        events_by_id[event_id] = event

    description_id = record["description_retrieval_id"]
    event = events_by_id.get(description_id)
    if event is None:
        raise ValueError(
            "description_retrieval_id must resolve to exactly one retrieval event"
        )
    event_availability = event.get("availability")
    canonical_availability = record.get("availability")
    if event_availability != canonical_availability and (
        event_availability not in AVAILABILITY_RANK
        or canonical_availability not in AVAILABILITY_RANK
        or AVAILABILITY_RANK[event_availability]
        > AVAILABILITY_RANK[canonical_availability]
    ):
        raise ValueError(
            "Description retrieval availability cannot exceed canonical availability"
        )

    event_review = event.get("review_extent")
    canonical_review = record.get("review_extent")
    if event_review != canonical_review and (
        event_review not in REVIEW_RANK
        or canonical_review not in REVIEW_RANK
        or REVIEW_RANK[event_review] > REVIEW_RANK[canonical_review]
    ):
        raise ValueError(
            "Description retrieval review_extent cannot exceed canonical review_extent"
        )

    basis = record.get("description_basis", {})
    basis_kind = basis.get("kind") if isinstance(basis, dict) else None
    minimum_review = DESCRIPTION_MINIMUM_REVIEW.get(basis_kind)
    if minimum_review is None:
        raise ValueError("description_basis must identify supported material")
    if event_review not in REVIEW_RANK or (
        REVIEW_RANK[event_review] < REVIEW_RANK[minimum_review]
    ):
        raise ValueError(
            f"{basis_kind} descriptions require matching reviewed evidence"
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

    left_availability_rank = AVAILABILITY_RANK.get(left.get("availability"), -1)
    right_availability_rank = AVAILABILITY_RANK.get(right.get("availability"), -1)
    if right_availability_rank > left_availability_rank:
        merged["availability"] = deepcopy(right["availability"])

    left_review_rank = REVIEW_RANK.get(left.get("review_extent"), -1)
    right_review_rank = REVIEW_RANK.get(right.get("review_extent"), -1)
    if right_review_rank > left_review_rank:
        merged["review_extent"] = deepcopy(right["review_extent"])
        right_description = right.get("description")
        if isinstance(right_description, str) and right_description.strip():
            for field in DESCRIPTION_FIELDS:
                if field in right:
                    merged[field] = deepcopy(right[field])

    for field, value in right.items():
        if (
            field in UNION_FIELDS
            or field in DESCRIPTION_FIELDS
            or field in ACCESS_AXIS_FIELDS
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
