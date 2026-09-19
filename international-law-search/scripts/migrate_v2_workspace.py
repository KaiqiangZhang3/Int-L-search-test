#!/usr/bin/env python3
"""Migrate a version-2 search workspace into an additive version-3 copy."""

from __future__ import annotations

from argparse import ArgumentParser
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile


BIBLIOGRAPHY_FIELDS = [
    "source_key",
    "citation",
    "source_type",
    "language",
    "scholarly_importance",
    "acquisition_priority",
    "availability",
    "review_extent",
    "reading_priority",
    "stable_links",
    "round_membership",
]


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Unable to read JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid JSON in {path} on line {line_number}: {error.msg}"
            ) from error
        if not isinstance(record, dict):
            raise ValueError(f"Expected an object in {path} on line {line_number}")
        records.append(record)
    return records


def _write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


def _copy_directory(source: Path, target: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True)


def _identity_evidence(record: dict) -> dict:
    verification = record.get("verification") or {}
    identity_status = verification.get("identity", "candidate")
    if identity_status not in {"verified", "candidate", "conflict"}:
        identity_status = "candidate"
    evidence_value = record.get("stable_url") or record.get("title") or record["id"]
    result = {
        "normalized_title": record.get("title") or record["id"],
        "creators": list(record.get("creators") or []),
        "publication_date": record.get("date"),
        "publication": record.get("publication"),
        "raw_citation": record.get("citation"),
        "identity_status": identity_status,
        "evidence": [
            {
                "kind": "publisher_record"
                if record.get("stable_url")
                else "other",
                "value": evidence_value,
                "locator": record.get("stable_url"),
                "checked_at": None,
            }
        ],
    }
    return result


def _description_basis(record: dict) -> dict:
    basis = record.get("description_basis")
    if isinstance(basis, dict):
        return basis
    kind = basis if basis in {"full_text", "selected_sections", "abstract", "metadata"} else "metadata"
    return {
        "kind": kind,
        "locations": ["Preserved from version-2 source record"],
    }


def _discovery_provenance(record: dict) -> list[dict]:
    provenance = []
    for item in record.get("discovery_history") or []:
        if not isinstance(item, dict):
            continue
        method = item.get("method", "query")
        if method not in {
            "query",
            "platform",
            "source",
            "footnote",
            "reference",
            "cited_by",
            "subagent",
            "local_seed",
        }:
            method = "query"
        migrated = {"method": method, "value": str(item.get("value") or "legacy")}
        for field in (
            "platform",
            "branch_id",
            "parent_source_key",
            "locator",
            "discovered_at",
            "privacy_classification",
            "externalizable",
        ):
            if field in item:
                migrated[field] = item[field]
        provenance.append(migrated)
    if not provenance:
        provenance.append(
            {
                "method": "query",
                "value": "Preserved from version-2 workspace",
            }
        )
    return provenance


def _retrieval_history(record: dict) -> list[dict]:
    history = []
    for event in record.get("retrieval_history") or []:
        if not isinstance(event, dict):
            continue
        history.append(
            {
                "event_id": str(event.get("event_id") or f"legacy-{len(history) + 1}"),
                "platform": str(event.get("platform") or "Legacy workspace"),
                "retrieved_at": str(event.get("retrieved_at") or "unknown"),
                "result": event.get("result") or event.get("availability"),
                "link": event.get("link") or event.get("stable_url"),
                "local_path": event.get("local_path"),
            }
        )
    return history


def _migrate_source(
    record: dict, round_map: dict[str, str], source_rounds: dict[str, list[str]]
) -> dict:
    source_key = record.get("source_key") or record.get("id")
    if not isinstance(source_key, str) or not source_key.strip():
        raise ValueError("Every version-2 source requires an id or source_key")
    source_key = source_key.strip()
    stable_url = record.get("stable_url")
    links = []
    if stable_url:
        links.append({"kind": "publisher", "url": stable_url})
    local_paths = [record["local_path"]] if record.get("local_path") else []
    migrated = {
        "source_key": source_key,
        "identity_evidence": _identity_evidence(record),
        "identifiers": dict(record.get("identifiers") or record.get("external_ids") or {}),
        "source_key_aliases": [record["id"]]
        if record.get("id") and record["id"] != source_key
        else [],
        "citation_aliases": list(record.get("citation_aliases") or []),
        "links": links,
        "local_paths": local_paths,
        "source_type": record.get("source_type"),
        "language": record.get("language"),
        "discovery_provenance": _discovery_provenance(record),
        "availability": record.get("availability", "metadata_only"),
        "review_extent": record.get("review_extent", "not_reviewed"),
        "description_basis": _description_basis(record),
        "description": record.get("description") or "Description not available in the version-2 record.",
        "inclusion_reason": record.get("inclusion_reason") or "Preserved from the version-2 workspace.",
        "scholarly_importance": {
            "level": "not_assessed",
            "reason": "Not assessed during version-2 migration.",
        },
        "acquisition_priority": "not_assessed",
        "acquisition_routes": [],
        "round_membership": [],
        "user_decisions": list(record.get("user_decisions") or []),
        "retrieval_history": _retrieval_history(record),
    }
    if record.get("publication") and record.get("source_type") == "journal_article":
        migrated["source_details"] = {"journal": record["publication"]}
    for round_id in source_rounds.get(source_key, []):
        migrated["round_membership"].append(
            {"round_id": round_id, "functions": ["discovered"]}
        )
    return migrated


def _empty_budget() -> dict:
    return {
        "bibliographic_discovery": 0,
        "full_text_acquisition": 0,
        "substantive_review": 0,
        "platforms": [],
        "query_cap": 0,
        "time_cap_minutes": 0,
        "tracing_depth": 0,
        "seeds": [],
        "language_allocations": [],
    }


def _authorization_for_round(
    old_round_id: str, decisions: list[dict], generated: list[dict], timestamp: str
) -> str:
    for decision in decisions:
        if decision.get("round_id") == old_round_id and decision.get("decision_id"):
            return decision["decision_id"]
    decision_id = f"migration-authorize-{old_round_id}"
    generated.append(
        {
            "decision_id": decision_id,
            "kind": "legacy_round_authorization",
            "decided_by": "version-2 migration",
            "decided_at": timestamp,
            "round_id": old_round_id,
            "note": "Generated only because the legacy round had no authorization decision.",
        }
    )
    return decision_id


def _migrate_rounds(
    legacy_rounds: list[dict], decisions: list[dict], report_paths: list[str], timestamp: str
) -> tuple[list[dict], dict[str, str], list[dict]]:
    round_map = {
        str(record.get("round_id") or f"legacy-round-{index}"): f"R{index}"
        for index, record in enumerate(legacy_rounds, 1)
    }
    generated_decisions = []
    migrated = []
    for index, record in enumerate(legacy_rounds, 1):
        old_round_id = str(record.get("round_id") or f"legacy-round-{index}")
        counts = record.get("counts") or {}
        actual = _empty_budget()
        actual["bibliographic_discovery"] = int(counts.get("new_candidate_count", 0) or 0)
        attempted = [str(item) for item in record.get("attempted_queries_or_paths") or []]
        actual["query_cap"] = len(attempted)
        planned = _empty_budget()
        planned["query_cap"] = len(attempted)
        budget_decision = next(
            (
                decision
                for decision in decisions
                if decision.get("round_id") == old_round_id
                and isinstance(decision.get("budget"), dict)
            ),
            None,
        )
        if budget_decision:
            budget = budget_decision["budget"]
            planned["bibliographic_discovery"] = int(budget.get("source_cap", 0) or 0)
            planned["substantive_review"] = int(budget.get("full_text_review_cap", 0) or 0)
            planned["time_cap_minutes"] = int(budget.get("time_minutes", 0) or 0)
            planned["tracing_depth"] = int(budget.get("depth_cap", 0) or 0)
        report_path = report_paths[index - 1] if index <= len(report_paths) else None
        migrated.append(
            {
                "round_id": f"R{index}",
                "kind": "main",
                "parent_round_id": None,
                "round_type": "breadth" if index == 1 else "breadth_expansion",
                "status": "paused"
                if record.get("decision") == "pause_for_user"
                else "completed",
                "authorization_decision_id": _authorization_for_round(
                    old_round_id, decisions, generated_decisions, timestamp
                ),
                "research_question": "Preserved version-2 research round",
                "exclusions": [],
                "planned_budget": planned,
                "actual_budget": actual,
                "methods": attempted
                + [
                    f"Migrated from legacy round {old_round_id}.",
                    "Historic full-text acquisition and substantive-review counts are unknown unless separately recorded.",
                ],
                "added_source_keys": [],
                "updated_source_keys": [],
                "duplicate_source_keys": [],
                "unresolved_source_keys": [],
                "added_claim_ids": [],
                "revised_claim_ids": [],
                "report_path": report_path,
                "synthesis_version": None,
                "presentation_version": None,
                "next_round_options": [],
                "budget_extension_decision_id": None,
            }
        )
    return migrated, round_map, generated_decisions


def _write_bibliography(path: Path, sources: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BIBLIOGRAPHY_FIELDS)
        writer.writeheader()
        for source in sources:
            identity = source["identity_evidence"]
            citation = identity.get("raw_citation") or identity["normalized_title"]
            writer.writerow(
                {
                    "source_key": source["source_key"],
                    "citation": citation,
                    "source_type": source.get("source_type") or "",
                    "language": source.get("language") or "",
                    "scholarly_importance": source["scholarly_importance"]["level"],
                    "acquisition_priority": source["acquisition_priority"],
                    "availability": source["availability"],
                    "review_extent": source["review_extent"],
                    "reading_priority": source.get("reading_priority") or "",
                    "stable_links": "; ".join(link["url"] for link in source["links"]),
                    "round_membership": "; ".join(
                        item["round_id"] for item in source["round_membership"]
                    ),
                }
            )


def _build_migration(source: Path, staging: Path, state: dict) -> None:
    for relative in (
        "plan",
        "knowledge",
        "reports",
        "synthesis",
        "presentations",
        "logs",
        "exports",
    ):
        (staging / relative).mkdir(parents=True, exist_ok=True)
    for relative in ("plan", "reports", "logs", "exports"):
        _copy_directory(source / relative, staging / relative)

    report_paths = [
        path.relative_to(staging).as_posix()
        for path in sorted((staging / "reports").rglob("*"))
        if path.is_file()
    ]
    decisions = list(state.get("decision_log") or [])
    legacy_rounds = list(state.get("rounds") or [])
    migrated_rounds, round_map, generated_decisions = _migrate_rounds(
        legacy_rounds,
        decisions,
        report_paths,
        state.get("updated_at") or state.get("created_at") or "unknown",
    )
    source_rounds: dict[str, list[str]] = {}
    for event in _read_jsonl(source / "logs" / "retrieval.jsonl"):
        source_key = event.get("source_key") or event.get("source_id")
        round_id = round_map.get(str(event.get("round_id")))
        if isinstance(source_key, str) and round_id:
            memberships = source_rounds.setdefault(source_key, [])
            if round_id not in memberships:
                memberships.append(round_id)
    sources = [
        _migrate_source(record, round_map, source_rounds)
        for record in _read_jsonl(source / "corpus" / "sources.jsonl")
    ]
    for round_record in migrated_rounds:
        round_record["added_source_keys"] = [
            source["source_key"]
            for source in sources
            if any(
                membership["round_id"] == round_record["round_id"]
                for membership in source["round_membership"]
            )
        ]
    _write_jsonl(staging / "knowledge" / "sources.jsonl", sources)
    _write_jsonl(staging / "knowledge" / "claims.jsonl", [])
    _write_jsonl(staging / "knowledge" / "rounds.jsonl", migrated_rounds)
    _write_jsonl(staging / "knowledge" / "decisions.jsonl", decisions + generated_decisions)
    _write_jsonl(staging / "knowledge" / "terminology.jsonl", [])

    legacy_edges = source / "corpus" / "edges.jsonl"
    if legacy_edges.exists():
        shutil.copy2(legacy_edges, staging / "knowledge" / "edges.jsonl")

    now = datetime.now(timezone.utc).isoformat()
    migrated_state = {
        key: value for key, value in state.items() if key != "rounds"
    }
    migrated_state.update(
        {
            "schema_version": 3,
            "updated_at": now,
            "graph_enabled": legacy_edges.exists(),
            "saturation_enabled": bool(state.get("saturation_enabled", False)),
            "current_checkpoint": migrated_rounds[-1]["round_id"]
            if migrated_rounds
            else None,
            "artifacts": {
                "sources": "knowledge/sources.jsonl",
                "claims": "knowledge/claims.jsonl",
                "rounds": "knowledge/rounds.jsonl",
                "decisions": "knowledge/decisions.jsonl",
                "terminology": "knowledge/terminology.jsonl",
                "current_synthesis": None,
                "presentation_hub": None,
                "bibliography": "exports/bibliography.csv",
            },
        }
    )
    _write_json(staging / "state.json", migrated_state)
    _write_bibliography(staging / "exports" / "bibliography.csv", sources)
    _write_json(
        staging / "migration-report.json",
        {
            "source_schema_version": 2,
            "target_schema_version": 3,
            "migrated_at": now,
            "round_id_map": round_map,
            "registered_legacy_reports": report_paths,
            "unknown_historic_counts": {
                round_id: ["full_text_acquisition", "substantive_review"]
                for round_id in round_map.values()
            },
            "generated_decision_ids": [
                decision["decision_id"] for decision in generated_decisions
            ],
        },
    )


def migrate(source: Path, target: Path) -> Path:
    """Create an atomic version-3 copy without changing the version-2 source."""

    source = Path(source).resolve()
    target = Path(target).resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"Version-2 workspace does not exist: {source}")
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite existing path: {target}")
    state_path = source / "state.json"
    state = _read_json(state_path)
    version = state.get("schema_version")
    if version != 2:
        raise ValueError(
            f"Refusing migration: expected schema_version 2, found {version!r}"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
        )
    )
    try:
        _build_migration(source, staging, state)
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite existing path: {target}")
        staging.rename(target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return target


def main() -> None:
    parser = ArgumentParser(
        description="Migrate a version-2 international-law search workspace."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    try:
        migrate(args.source, args.target)
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
