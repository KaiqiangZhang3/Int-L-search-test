#!/usr/bin/env python3
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import tempfile


def _build_workspace(
    target: Path, project_id: str, now: str, graph_enabled: bool = False
) -> None:
    for relative in [
        "plan",
        "knowledge",
        "reports",
        "synthesis",
        "presentations",
        "logs",
        "exports",
    ]:
        (target / relative).mkdir(parents=True, exist_ok=False)

    state = {
        "schema_version": 3,
        "graph_enabled": graph_enabled,
        "saturation_enabled": False,
        "project_id": project_id,
        "created_at": now,
        "updated_at": now,
        "status": "planning",
        "current_checkpoint": None,
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
        "approved_plan": None,
        "decision_log": [],
        "branches": [],
        "coverage": {
            dimension: {"searched": [], "unsearched": []}
            for dimension in (
                "subquestions",
                "platforms",
                "languages",
                "periods",
                "authority_classes",
            )
        },
        "deduplication": {
            "identity_index": {},
            "unresolved_record_ids": [],
            "last_merged_at": None,
        },
        "stopping": {
            "decision": "continue",
            "reason": "Search plan has not yet been approved.",
            "open_high_value_branches": [],
        },
    }
    (target / "state.json").write_text(
        json.dumps(state, indent=2) + "\n", encoding="utf-8"
    )
    (target / "plan" / "search-plan.md").write_text(
        "# Search Plan\n\nStatus: `pending`\n", encoding="utf-8"
    )
    for relative in [
        "knowledge/sources.jsonl",
        "knowledge/claims.jsonl",
        "knowledge/rounds.jsonl",
        "knowledge/decisions.jsonl",
        "knowledge/terminology.jsonl",
        "logs/retrieval.jsonl",
    ]:
        (target / relative).touch()
    (target / "exports" / "bibliography.csv").write_text(
        "source_key,citation,source_type,language,scholarly_importance,"
        "acquisition_priority,availability,review_extent,reading_priority,"
        "stable_links,round_membership\n",
        encoding="utf-8",
    )
    if graph_enabled:
        (target / "knowledge" / "edges.jsonl").touch()


def initialize(
    target: Path, project_id: str, *, graph_enabled: bool = False, _builder=None
) -> None:
    project_id = project_id.strip()
    if not project_id:
        raise ValueError("Project ID must not be empty or whitespace.")

    target = target.resolve()
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite existing path: {target}")

    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
        )
    )
    try:
        now = datetime.now(timezone.utc).isoformat()
        if _builder is None:
            _build_workspace(staging, project_id, now, graph_enabled)
        else:
            _builder(staging, project_id, now)
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite existing path: {target}")
        staging.rename(target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main() -> None:
    parser = ArgumentParser(
        description="Initialize an international-law search workspace."
    )
    parser.add_argument("target", type=Path)
    parser.add_argument("--project-id", required=True)
    parser.add_argument(
        "--graph", action="store_true", help="Create optional graph storage."
    )
    args = parser.parse_args()
    try:
        initialize(args.target, args.project_id, graph_enabled=args.graph)
    except (FileExistsError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
