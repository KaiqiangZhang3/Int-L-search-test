#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
import copy
import json
import shutil
import tempfile


ACCESS_MAP = {
    "Full text read": (
        "subscription_full_text",
        "full_text_substantively_reviewed",
        True,
    ),
    "Full text not read": ("identified_inaccessible", "not_reviewed", True),
    "Abstract only": ("abstract_available", "abstract_reviewed", False),
    "Metadata only": ("metadata_only", "metadata_verified", False),
    "Access failed": ("access_failure", "not_reviewed", False),
}

FULL_TEXT_AVAILABILITY = {"open_full_text", "subscription_full_text"}


def _proven_full_text_route(record: dict) -> str | None:
    if record.get("local_path"):
        return "open_full_text"
    availability = record.get("availability")
    if availability in FULL_TEXT_AVAILABILITY:
        return availability
    route = record.get("access_route")
    if route in {"open", "open_full_text", "local", "local_full_text"}:
        return "open_full_text"
    if route in {"subscription", "subscription_full_text", "institutional"}:
        return "subscription_full_text"
    return None


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    content = "".join(
        json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        for record in records
    )
    path.write_text(content, encoding="utf-8")


def _migrate_source(record: dict) -> dict:
    migrated = copy.deepcopy(record)
    legacy_id = migrated["id"]
    access_status = migrated.pop("access_status")
    availability, review_extent, ambiguous = ACCESS_MAP[access_status]
    proven_route = _proven_full_text_route(migrated)
    migrated["availability"] = proven_route or availability
    migrated["review_extent"] = review_extent
    migrated["legacy_ids"] = [legacy_id]
    migrated["migration_review_required"] = ambiguous and proven_route is None

    for event in migrated.get("retrieval_history", []):
        event_status = event.pop("access_status")
        event_availability, event_review_extent, _ = ACCESS_MAP[event_status]
        event["availability"] = (
            _proven_full_text_route(event) or event_availability
        )
        event["review_extent"] = event_review_extent

    basis = migrated.get("description_basis")
    if isinstance(basis, str):
        migrated["description_basis"] = {
            "kind": basis,
            "locations": ["Preserved from version-1 source record"],
        }
    return migrated


def _migrate_retrieval_event(event: dict) -> dict:
    migrated = copy.deepcopy(event)
    access_status = migrated.pop("access_status", None)
    if access_status is not None:
        availability, review_extent, _ = ACCESS_MAP[access_status]
        migrated["availability"] = (
            _proven_full_text_route(migrated) or availability
        )
        migrated["review_extent"] = review_extent
    return migrated


def _migrate_edges(records: list[dict], sources: list[dict]) -> list[dict]:
    by_id = {record["id"]: record for record in sources}
    migrated = []
    for original in records:
        edge = copy.deepcopy(original)
        if edge.get("relation") == "discovered_from":
            source = by_id.get(edge.get("source_id"))
            if source is not None:
                evidence = edge.get("evidence") or {}
                value = edge.get("target_id", "unknown source")
                if evidence.get("location"):
                    value = f"{value} ({evidence['location']})"
                provenance = {"method": "source", "value": value}
                if provenance not in source["discovery_history"]:
                    source["discovery_history"].append(provenance)
            continue
        if edge.get("relation") != "cites" and not edge.get("evidence"):
            edge["status"] = "candidate"
            edge["record_scope"] = "candidate"
        migrated.append(edge)
    return migrated


def migrate(source: Path, destination: Path) -> Path:
    source = source.resolve()
    destination = destination.resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"Version-1 workspace does not exist: {source}")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing path: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
        )
    )
    try:
        shutil.copytree(source, staging, dirs_exist_ok=True)
        sources_path = staging / "corpus" / "sources.jsonl"
        sources = [_migrate_source(record) for record in _read_jsonl(sources_path)]
        edges_path = staging / "corpus" / "edges.jsonl"
        edges = _migrate_edges(_read_jsonl(edges_path), sources)
        _write_jsonl(sources_path, sources)
        _write_jsonl(edges_path, edges)

        retrieval_path = staging / "logs" / "retrieval.jsonl"
        _write_jsonl(
            retrieval_path,
            [_migrate_retrieval_event(event) for event in _read_jsonl(retrieval_path)],
        )

        state_path = staging / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["schema_version"] = 2
        state["graph_enabled"] = edges_path.exists()
        state_path.write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        review_required = [
            record["id"]
            for record in sources
            if record["migration_review_required"]
        ]
        report = {
            "source_schema_version": 1,
            "target_schema_version": 2,
            "review_required_source_ids": review_required,
            "ambiguous_conversion_count": len(review_required),
        }
        (staging / "migration-report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        staging.rename(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return destination


def main() -> None:
    parser = ArgumentParser(
        description="Migrate a version-1 international-law search workspace."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        migrate(args.source, args.destination)
    except (FileExistsError, FileNotFoundError, KeyError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
