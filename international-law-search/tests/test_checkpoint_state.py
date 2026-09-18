from pathlib import Path
import importlib.util
import json
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "checkpoint_state.py"


def load_module():
    spec = importlib.util.spec_from_file_location("checkpoint_state", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def base_state():
    return {
        "schema_version": 2,
        "graph_enabled": False,
        "saturation_enabled": False,
        "project_id": "project",
        "status": "retrieving",
        "decision_log": [],
        "branches": [
            {
                "branch_id": "breadth",
                "retrieval_mode": "horizontal",
                "status": "active",
                "authorization_decision_id": None,
            }
        ],
    }


def vertical_branch():
    return {
        "branch_id": "vertical-1",
        "source_track": "secondary",
        "retrieval_mode": "vertical",
        "authorization_decision_id": None,
        "approved_budget": {"depth_cap": 2},
        "vertical_seed_id": "source-1",
        "tracing_direction": "backward",
        "known_id_snapshot": ["source-1"],
        "status": "pending",
        "assignment": "Trace backward citations from the approved seed.",
        "scope": "One approved backward-tracing branch.",
        "exclusions": [],
        "source_types": ["journal_article"],
        "period": {"start": None, "end": None},
        "privacy_constraints": [],
        "last_checkpoint": None,
        "platform_errors": [],
        "unresolved_items": [],
        "current_depth": 0,
        "max_authorized_depth": 2,
        "queries": [],
        "platforms": ["Crossref"],
        "languages": ["English"],
        "pending_items": [],
        "open_paths": [],
        "status_reason": None,
        "status_changed_at": None,
    }


def round_evidence(round_id, budget_status):
    return {
        "round_id": round_id,
        "timestamp": "2026-09-18T00:00:00Z",
        "budget_status": budget_status,
        "decision": "pause_for_user",
        "decision_reason": "Checkpoint recorded for recovery.",
        "unresolved_gaps": [],
        "branch_depth": {"breadth": 0},
        "attempted_queries_or_paths": ["approved path"],
        "access_failures": [],
        "counts": {
            "candidate_count": 0,
            "new_candidate_count": 0,
            "new_high_relevance_count": 0,
            "new_core_material_count": 0,
            "duplicate_count": 0,
            "duplicate_ratio": 0,
        },
        "coverage_additions": {
            "source_types": [],
            "themes": [],
            "languages": [],
            "platforms": [],
        },
        "access_gaps": [],
        "open_high_value_branches": ["resume:breadth"],
    }


class CheckpointStateTests(unittest.TestCase):
    def write_state(self, root, state):
        path = root / "state.json"
        path.write_text(json.dumps(state) + "\n", encoding="utf-8")
        return path

    def test_breadth_pause_and_seed_approval_are_atomic_and_resumable(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = self.write_state(root, base_state())
            module.checkpoint(
                path,
                "breadth_pause",
                {
                    "decision_id": "pause-1",
                    "decided_by": "user",
                    "decided_at": "2026-09-18T00:00:00Z",
                    "round_id": "round-1",
                },
            )
            paused = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("paused", paused["status"])
            self.assertEqual("pause", paused["decision_log"][-1]["kind"])

            module.checkpoint(
                path,
                "seed_approval",
                {
                    "decision_id": "trace-1",
                    "decided_by": "user",
                    "decided_at": "2026-09-18T00:05:00Z",
                    "round_id": "round-1",
                    "branch_id": "vertical-1",
                    "seed_id": "source-1",
                    "directions": ["backward"],
                    "budget": {"depth_cap": 2},
                    "branch": vertical_branch(),
                },
            )
            approved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("retrieving", approved["status"])
            self.assertEqual("approve_trace", approved["decision_log"][-1]["kind"])
            created = next(
                branch
                for branch in approved["branches"]
                if branch["branch_id"] == "vertical-1"
            )
            self.assertEqual("active", created["status"])
            self.assertEqual("trace-1", created["authorization_decision_id"])
            schema = json.loads(
                (ROOT / "schemas" / "project-state.schema.json").read_text(
                    encoding="utf-8"
                )
            )
            branch_schema = schema["properties"]["branches"]["items"]
            self.assertEqual(set(branch_schema["required"]), set(created))
            self.assertIn(
                created["tracing_direction"],
                branch_schema["properties"]["tracing_direction"]["enum"],
            )
            self.assertEqual([], list(root.glob(".state.json.*.tmp")))

    def test_seed_approval_cannot_authorize_a_missing_uncreated_branch(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = base_state()
            state["status"] = "paused"
            path = self.write_state(root, state)
            before = path.read_text(encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "branch object"):
                module.checkpoint(
                    path,
                    "seed_approval",
                    {
                        "decision_id": "trace-1",
                        "decided_by": "user",
                        "decided_at": "2026-09-18T00:05:00Z",
                        "round_id": "round-1",
                        "branch_id": "missing-vertical",
                        "seed_id": "source-1",
                        "directions": ["backward"],
                        "budget": {"depth_cap": 2},
                    },
                )

            self.assertEqual(before, path.read_text(encoding="utf-8"))

    def test_seed_approval_rejects_an_existing_branch_with_unapproved_depth(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = base_state()
            state["status"] = "paused"
            state["branches"].append(vertical_branch())
            path = self.write_state(root, state)
            before = path.read_text(encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "depth"):
                module.checkpoint(
                    path,
                    "seed_approval",
                    {
                        "decision_id": "trace-depth-mismatch",
                        "decided_by": "user",
                        "decided_at": "2026-09-18T00:05:00Z",
                        "round_id": "round-1",
                        "branch_id": "vertical-1",
                        "seed_id": "source-1",
                        "directions": ["backward"],
                        "budget": {"depth_cap": 3},
                    },
                )

            self.assertEqual(before, path.read_text(encoding="utf-8"))

    def test_budget_pause_failure_and_resume_reject_illegal_transitions(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = base_state()
            state["branches"][0]["retrieval_mode"] = "horizontal"
            path = self.write_state(root, state)
            common = {
                "decision_id": "pause-budget",
                "decided_by": "system",
                "decided_at": "2026-09-18T00:00:00Z",
                "round_id": "round-1",
                "branch_id": "breadth",
                "last_checkpoint": "cursor-10",
                "pending_items": ["source-next"],
                "unresolved_items": ["citation-next"],
                "platform_errors": [],
                "open_paths": ["forward:source-next"],
                "reason": "Approved source cap reached.",
                "occurred_at": "2026-09-18T00:00:00Z",
                "round": round_evidence("round-1", "budget_paused"),
            }
            module.checkpoint(path, "budget_paused", common)
            budget_paused = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("budget_paused", budget_paused["branches"][0]["status"])
            self.assertEqual("cursor-10", budget_paused["branches"][0]["last_checkpoint"])
            self.assertEqual("budget_paused", budget_paused["rounds"][-1]["budget_status"])

            resume = dict(common, decision_id="resume-1", decided_by="user")
            module.checkpoint(path, "resume", resume)
            resumed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("active", resumed["branches"][0]["status"])
            self.assertEqual("resume", resumed["decision_log"][-1]["kind"])

            module.checkpoint(
                path,
                "failed",
                {
                    "branch_id": "breadth",
                    "last_checkpoint": "cursor-11",
                    "pending_items": ["source-retry"],
                    "unresolved_items": ["platform outage"],
                    "platform_errors": [
                        {
                            "platform": "Index",
                            "error": "timeout",
                            "occurred_at": "2026-09-18T00:10:00Z",
                        }
                    ],
                    "open_paths": ["retry:index"],
                    "reason": "Index timed out.",
                    "occurred_at": "2026-09-18T00:10:00Z",
                    "round": round_evidence("round-2", "within_budget"),
                },
            )
            failed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("failed", failed["branches"][0]["status"])

            before = path.read_text(encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Illegal transition"):
                module.checkpoint(path, "failed", {"branch_id": "breadth"})
            self.assertEqual(before, path.read_text(encoding="utf-8"))

    def test_budget_pause_rejects_missing_recovery_evidence(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_state(Path(directory), base_state())
            before = path.read_text(encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "recovery fields"):
                module.checkpoint(
                    path,
                    "budget_paused",
                    {
                        "decision_id": "pause-1",
                        "decided_by": "system",
                        "decided_at": "2026-09-18T00:00:00Z",
                        "round_id": "round-1",
                        "branch_id": "breadth",
                    },
                )

            self.assertEqual(before, path.read_text(encoding="utf-8"))
