#!/usr/bin/env python3
"""Apply recoverable project-state transitions with atomic replacement."""

from argparse import ArgumentParser
import copy
import json
import os
from pathlib import Path
import tempfile


USER_TRANSITIONS = {
    "breadth_pause": "pause",
    "seed_approval": "approve_trace",
    "budget_paused": "pause",
    "resume": "resume",
}

VERTICAL_BRANCH_REQUIRED = {
    "branch_id",
    "source_track",
    "retrieval_mode",
    "authorization_decision_id",
    "approved_budget",
    "vertical_seed_id",
    "tracing_direction",
    "known_id_snapshot",
    "status",
    "assignment",
    "scope",
    "exclusions",
    "source_types",
    "period",
    "privacy_constraints",
    "last_checkpoint",
    "platform_errors",
    "unresolved_items",
    "current_depth",
    "max_authorized_depth",
    "queries",
    "platforms",
    "languages",
    "pending_items",
    "open_paths",
    "status_reason",
    "status_changed_at",
}

RECOVERY_FIELDS = {
    "last_checkpoint",
    "pending_items",
    "unresolved_items",
    "platform_errors",
    "open_paths",
    "reason",
    "occurred_at",
    "round",
}
ROUND_REQUIRED = {
    "round_id",
    "timestamp",
    "budget_status",
    "decision",
    "decision_reason",
    "unresolved_gaps",
    "branch_depth",
    "attempted_queries_or_paths",
    "access_failures",
    "counts",
    "coverage_additions",
    "access_gaps",
    "open_high_value_branches",
}


def _branch(state: dict, branch_id: str) -> dict:
    for branch in state.get("branches", []):
        if branch.get("branch_id") == branch_id:
            return branch
    raise ValueError(f"Unknown branch: {branch_id!r}")


def _decision(payload: dict, kind: str) -> dict:
    required = ("decision_id", "decided_by", "decided_at", "round_id")
    missing = [field for field in required if not payload.get(field)]
    if missing:
        raise ValueError(f"Decision is missing required fields: {', '.join(missing)}")
    decision = {field: payload[field] for field in required}
    decision["kind"] = kind
    for field in ("branch_id", "seed_id", "directions", "budget"):
        if field in payload:
            decision[field] = copy.deepcopy(payload[field])
    return decision


def _prepare_vertical_branch(payload: dict, decision_id: str) -> dict:
    branch_id = payload.get("branch_id")
    seed_id = payload.get("seed_id")
    directions = payload.get("directions") or []
    budget = payload.get("budget")
    if not isinstance(budget, dict) or not budget:
        raise ValueError("Seed approval requires a non-empty budget")
    branch = copy.deepcopy(payload.get("branch"))
    if not isinstance(branch, dict):
        raise ValueError("Seed approval for a new branch requires a branch object")
    missing = sorted(VERTICAL_BRANCH_REQUIRED - set(branch))
    if missing:
        raise ValueError(
            f"Vertical branch is missing required fields: {', '.join(missing)}"
        )
    if branch.get("branch_id") != branch_id:
        raise ValueError("Vertical branch_id does not match the approval decision")
    if branch.get("retrieval_mode") != "vertical":
        raise ValueError("Seed approval requires a vertical branch")
    if branch.get("vertical_seed_id") != seed_id:
        raise ValueError("Vertical seed does not match the approval decision")
    if branch.get("tracing_direction") not in directions:
        raise ValueError("Vertical direction does not match the approval decision")
    if branch.get("status") != "pending":
        raise ValueError("Newly approved vertical branch must be pending")
    if branch.get("authorization_decision_id") not in (None, decision_id):
        raise ValueError("Vertical branch has a conflicting authorization")
    depth_cap = budget.get("depth_cap")
    if depth_cap is not None and branch.get("max_authorized_depth") != depth_cap:
        raise ValueError("Vertical branch depth does not match the approved budget")
    if branch.get("approved_budget") != budget:
        raise ValueError("Vertical branch approved_budget does not match the decision")
    branch["authorization_decision_id"] = decision_id
    branch["status"] = "active"
    return branch


def _record_recovery_checkpoint(
    state: dict, branch: dict, payload: dict, expected_budget_status: str | None
) -> None:
    missing = sorted(
        field
        for field in RECOVERY_FIELDS
        if field not in payload or payload[field] is None
    )
    if missing:
        raise ValueError(f"Missing recovery fields: {', '.join(missing)}")
    for field in ("pending_items", "unresolved_items", "platform_errors", "open_paths"):
        if not isinstance(payload[field], list):
            raise ValueError(f"Recovery field {field} must be an array")
    if not isinstance(payload["last_checkpoint"], str) or not payload["last_checkpoint"]:
        raise ValueError("Recovery field last_checkpoint must be non-empty")
    if not isinstance(payload["reason"], str) or not payload["reason"]:
        raise ValueError("Recovery field reason must be non-empty")
    if not isinstance(payload["occurred_at"], str) or not payload["occurred_at"]:
        raise ValueError("Recovery field occurred_at must be non-empty")
    round_record = payload["round"]
    if not isinstance(round_record, dict) or not round_record.get("round_id"):
        raise ValueError("Recovery round evidence requires round_id")
    missing_round_fields = sorted(ROUND_REQUIRED - set(round_record))
    if missing_round_fields:
        raise ValueError(
            "Recovery round evidence is missing fields: "
            + ", ".join(missing_round_fields)
        )
    if expected_budget_status is not None and round_record.get("budget_status") != expected_budget_status:
        raise ValueError(
            f"Recovery round budget_status must be {expected_budget_status}"
        )

    branch["last_checkpoint"] = payload["last_checkpoint"]
    branch["pending_items"] = copy.deepcopy(payload["pending_items"])
    branch["unresolved_items"] = copy.deepcopy(payload["unresolved_items"])
    branch["platform_errors"] = copy.deepcopy(payload["platform_errors"])
    branch["open_paths"] = copy.deepcopy(payload["open_paths"])
    branch["status_reason"] = payload["reason"]
    branch["status_changed_at"] = payload["occurred_at"]

    rounds = state.setdefault("rounds", [])
    for index, existing in enumerate(rounds):
        if existing.get("round_id") == round_record["round_id"]:
            rounds[index] = copy.deepcopy(round_record)
            break
    else:
        rounds.append(copy.deepcopy(round_record))


def apply_transition(state: dict, transition: str, payload: dict) -> dict:
    """Return a transitioned copy or raise without mutating the input state."""
    updated = copy.deepcopy(state)
    updated.setdefault("decision_log", [])

    if transition == "breadth_pause":
        if updated.get("status") != "retrieving":
            raise ValueError("Illegal transition: breadth pause requires retrieving")
        updated["status"] = "paused"
    elif transition == "seed_approval":
        if updated.get("status") != "paused":
            raise ValueError("Illegal transition: seed approval requires paused")
        if (
            not payload.get("branch_id")
            or not payload.get("seed_id")
            or not payload.get("directions")
            or not isinstance(payload.get("budget"), dict)
            or not payload.get("budget")
        ):
            raise ValueError(
                "Seed approval requires branch_id, seed_id, directions, and budget"
            )
        branch_id = payload.get("branch_id")
        existing = next(
            (
                branch
                for branch in updated.get("branches", [])
                if branch.get("branch_id") == branch_id
            ),
            None,
        )
        if existing is None:
            updated.setdefault("branches", []).append(
                _prepare_vertical_branch(payload, payload.get("decision_id"))
            )
        else:
            if payload.get("branch") is not None:
                raise ValueError("Existing pending branch must not be replaced")
            if existing.get("retrieval_mode") != "vertical":
                raise ValueError("Seed approval requires a vertical branch")
            if existing.get("status") != "pending":
                raise ValueError("Existing vertical branch must be pending")
            if existing.get("vertical_seed_id") != payload.get("seed_id"):
                raise ValueError("Vertical seed does not match the approval decision")
            if existing.get("tracing_direction") not in payload.get("directions", []):
                raise ValueError("Vertical direction does not match the approval decision")
            if existing.get("authorization_decision_id") not in (
                None,
                payload.get("decision_id"),
            ):
                raise ValueError("Vertical branch has a conflicting authorization")
            depth_cap = payload["budget"].get("depth_cap")
            if (
                depth_cap is not None
                and existing.get("max_authorized_depth") != depth_cap
            ):
                raise ValueError(
                    "Vertical branch depth does not match the approved budget"
                )
            if existing.get("approved_budget") != payload.get("budget"):
                raise ValueError(
                    "Vertical branch approved_budget does not match the decision"
                )
            existing["authorization_decision_id"] = payload.get("decision_id")
            existing["status"] = "active"
        updated["status"] = "retrieving"
    elif transition == "budget_paused":
        branch = _branch(updated, payload.get("branch_id"))
        if branch.get("status") != "active":
            raise ValueError("Illegal transition: budget pause requires active branch")
        _record_recovery_checkpoint(updated, branch, payload, "budget_paused")
        branch["status"] = "budget_paused"
        updated["status"] = "paused"
    elif transition == "failed":
        branch = _branch(updated, payload.get("branch_id"))
        if branch.get("status") not in {"pending", "active"}:
            raise ValueError("Illegal transition: failed requires pending or active branch")
        _record_recovery_checkpoint(updated, branch, payload, None)
        branch["status"] = "failed"
        updated["status"] = "paused"
    elif transition == "resume":
        branch = _branch(updated, payload.get("branch_id"))
        if branch.get("status") not in {"paused", "budget_paused", "failed"}:
            raise ValueError("Illegal transition: resume requires a paused or failed branch")
        branch["status"] = "active"
        updated["status"] = "retrieving"
    else:
        raise ValueError(f"Unknown transition: {transition!r}")

    if transition in USER_TRANSITIONS:
        decision = _decision(payload, USER_TRANSITIONS[transition])
        if any(
            item.get("decision_id") == decision["decision_id"]
            for item in updated["decision_log"]
        ):
            raise ValueError(f"Duplicate decision_id: {decision['decision_id']!r}")
        updated["decision_log"].append(decision)
    updated["updated_at"] = payload.get("decided_at", payload.get("occurred_at", updated.get("updated_at")))
    return updated


def checkpoint(path: Path, transition: str, payload: dict) -> dict:
    """Apply a transition and atomically replace the state file."""
    state = json.loads(path.read_text(encoding="utf-8"))
    updated = apply_transition(state, transition, payload)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(updated, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return updated


def main() -> None:
    parser = ArgumentParser(description="Atomically checkpoint retrieval state.")
    parser.add_argument("state", type=Path)
    parser.add_argument("transition", choices=[*USER_TRANSITIONS, "failed"])
    parser.add_argument("--payload", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    try:
        checkpoint(args.state, args.transition, payload)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
