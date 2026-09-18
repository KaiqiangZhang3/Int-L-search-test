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
    for relative in ["plan", "corpus", "logs", "exports"]:
        (target / relative).mkdir(parents=True, exist_ok=False)

    state = {
        "schema_version": 2,
        "graph_enabled": graph_enabled,
        "saturation_enabled": False,
        "project_id": project_id,
        "created_at": now,
        "updated_at": now,
        "status": "planning",
        "approved_plan": None,
        "branches": [],
        "rounds": [],
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
        "corpus/sources.jsonl",
        "logs/retrieval.jsonl",
        "exports/.gitkeep",
    ]:
        (target / relative).touch()
    if graph_enabled:
        (target / "corpus" / "edges.jsonl").touch()


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
