from pathlib import Path
import importlib.util
import json
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "round_ops.py"
ROOT = SCRIPT.parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location("round_ops", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def research_budget(**overrides):
    budget = {
        "bibliographic_discovery": 20,
        "full_text_acquisition": 8,
        "substantive_review": 5,
        "platforms": [
            {"name": "Example Index", "purpose": "Discover scholarship"}
        ],
        "query_cap": 10,
        "time_cap_minutes": 120,
        "tracing_depth": 0,
        "seeds": [],
        "language_allocations": [
            {
                "language": "en",
                "purpose": "Map the general literature",
                "bibliographic_discovery": 20,
                "full_text_acquisition": 8,
                "substantive_review": 5,
            }
        ],
    }
    budget.update(overrides)
    return budget


def round_record(round_id, round_type, *, kind="main", parent_round_id=None):
    return {
        "round_id": round_id,
        "kind": kind,
        "parent_round_id": parent_round_id,
        "round_type": round_type,
        "status": "completed",
        "authorization_decision_id": f"DEC-{round_id}",
        "research_question": "What sources address the issue?",
        "exclusions": ["Domestic law without an international-law connection"],
        "planned_budget": research_budget(),
        "actual_budget": research_budget(
            bibliographic_discovery=12,
            full_text_acquisition=5,
            substantive_review=4,
            query_cap=7,
            time_cap_minutes=90,
        ),
        "methods": ["Database query"],
        "added_source_keys": [],
        "updated_source_keys": [],
        "duplicate_source_keys": [],
        "unresolved_source_keys": [],
        "added_claim_ids": [],
        "revised_claim_ids": [],
        "report_path": f"reports/{round_id}.md",
        "synthesis_version": None,
        "presentation_version": None,
        "next_round_options": [],
        "budget_extension_decision_id": None,
    }


class RoundOperationTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._temporary_directory.name)

    def tearDown(self):
        self._temporary_directory.cleanup()

    def test_breadth_may_be_followed_by_breadth_expansion(self):
        result = self.module.allocate_round(
            [round_record("R1", "breadth")],
            kind="main",
            round_type="breadth_expansion",
        )

        self.assertEqual(
            ("R2", "breadth_expansion"),
            (result["round_id"], result["round_type"]),
        )

    def test_side_round_does_not_advance_main_counter(self):
        records = [round_record("R1", "breadth")]
        side = self.module.allocate_round(
            records,
            kind="side",
            round_type="verification",
            parent_round_id="R1",
        )
        main = self.module.allocate_round(
            records + [side], kind="main", round_type="depth"
        )

        self.assertEqual("R1.S1", side["round_id"])
        self.assertEqual("R2", main["round_id"])

    def test_allocate_round_rejects_an_inconsistent_existing_index(self):
        records = [round_record("R2", "breadth")]

        with self.assertRaisesRegex(ValueError, "main-round gap"):
            self.module.allocate_round(records, kind="main", round_type="depth")

    def test_allocate_round_rejects_a_side_round_gap(self):
        records = [
            round_record("R1", "breadth"),
            round_record(
                "R1.S2", "verification", kind="side", parent_round_id="R1"
            ),
        ]

        with self.assertRaisesRegex(ValueError, "side-round gap"):
            self.module.allocate_round(
                records,
                kind="side",
                round_type="verification",
                parent_round_id="R1",
            )

    def test_append_round_writes_a_valid_record(self):
        path = self.tmp_path / "rounds.jsonl"
        record = round_record("R1", "breadth")

        self.module.append_round(path, record)

        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([record], rows)

    def test_append_round_rejects_duplicate_ids_without_changing_the_ledger(self):
        path = self.tmp_path / "rounds.jsonl"
        original = round_record("R1", "breadth")
        self.module.append_round(path, original)

        with self.assertRaisesRegex(ValueError, "Duplicate round_id"):
            self.module.append_round(path, round_record("R1", "verification"))

        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([original], rows)

    def test_append_round_rejects_a_gap_in_main_round_ids(self):
        path = self.tmp_path / "rounds.jsonl"
        self.module.append_round(path, round_record("R1", "breadth"))

        with self.assertRaisesRegex(ValueError, "next main round must be R2"):
            self.module.append_round(path, round_record("R3", "depth"))

    def test_append_round_rejects_missing_or_side_round_parents(self):
        path = self.tmp_path / "rounds.jsonl"
        self.module.append_round(path, round_record("R1", "breadth"))
        first_side = round_record(
            "R1.S1", "verification", kind="side", parent_round_id="R1"
        )
        self.module.append_round(path, first_side)
        nested_side = round_record(
            "R1.S2", "verification", kind="side", parent_round_id="R1.S1"
        )

        with self.assertRaisesRegex(ValueError, "parent must be an existing main round"):
            self.module.append_round(path, nested_side)

    def test_actual_budget_requires_an_extension_decision_to_exceed_a_cap(self):
        path = self.tmp_path / "rounds.jsonl"
        over_budget = round_record("R1", "breadth")
        over_budget["actual_budget"]["substantive_review"] = 6

        with self.assertRaisesRegex(ValueError, "substantive_review exceeds"):
            self.module.append_round(path, over_budget)

        over_budget["budget_extension_decision_id"] = "DEC-EXT-1"
        self.module.append_round(path, over_budget)

    def test_append_round_requires_complete_named_budget_dimensions(self):
        path = self.tmp_path / "rounds.jsonl"
        incomplete = round_record("R1", "breadth")
        del incomplete["planned_budget"]["platforms"]

        with self.assertRaisesRegex(ValueError, "planned_budget is missing"):
            self.module.append_round(path, incomplete)

    def test_append_round_rejects_fields_outside_the_closed_schema(self):
        path = self.tmp_path / "rounds.jsonl"
        record = round_record("R1", "breadth")
        record["silent_scope_expansion"] = True

        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            self.module.append_round(path, record)

    def test_append_round_rejects_an_unknown_status(self):
        path = self.tmp_path / "rounds.jsonl"
        record = round_record("R1", "breadth")
        record["status"] = "silently_expanded"

        with self.assertRaisesRegex(ValueError, "Unsupported round status"):
            self.module.append_round(path, record)

    def test_actual_budget_cannot_add_an_unapproved_platform(self):
        path = self.tmp_path / "rounds.jsonl"
        record = round_record("R1", "breadth")
        record["actual_budget"]["platforms"].append(
            {"name": "Unapproved Database", "purpose": "Expand discovery"}
        )

        with self.assertRaisesRegex(ValueError, "unapproved platform"):
            self.module.append_round(path, record)

    def test_round_schema_defines_round_types_and_three_axis_budgets(self):
        schema = json.loads(
            (ROOT / "schemas" / "round-record.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            self.module.ROUND_TYPES,
            set(schema["properties"]["round_type"]["enum"]),
        )
        for field in (
            "bibliographic_discovery",
            "full_text_acquisition",
            "substantive_review",
            "platforms",
            "query_cap",
            "time_cap_minutes",
            "tracing_depth",
            "seeds",
            "language_allocations",
        ):
            self.assertIn(field, schema["$defs"]["research_budget"]["required"])

    def test_readiness_schema_requires_status_and_evidence_for_each_topic(self):
        schema = json.loads(
            (ROOT / "schemas" / "readiness-matrix.schema.json").read_text(
                encoding="utf-8"
            )
        )
        topic = schema["properties"]["topics"]["items"]

        self.assertEqual(
            {"known", "default_accepted", "deferred", "not_applicable"},
            set(topic["properties"]["status"]["enum"]),
        )
        self.assertTrue({"topic", "status", "value", "evidence"}.issubset(topic["required"]))
        self.assertEqual(
            {"user", "existing_context"},
            set(topic["properties"]["evidence"]["properties"]["origin"]["enum"]),
        )

    def test_guidance_stops_readiness_when_one_bounded_round_is_designable(self):
        readiness = (ROOT / "references" / "readiness-and-scale.md").read_text(
            encoding="utf-8"
        )
        rounds = (ROOT / "references" / "research-rounds.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Ask one material question at a time", readiness)
        self.assertIn("Do not ask again", readiness)
        self.assertIn("next bounded round is designable", readiness)
        for profile in (
            "Orientation",
            "Seminar paper",
            "Thesis chapter",
            "Doctoral corpus",
        ):
            self.assertIn(profile, readiness)
        self.assertIn("expectations, not quotas", readiness)
        self.assertIn("repeatable main rounds", rounds)
        self.assertIn("Side rounds", rounds)

    def test_scope_card_exposes_scale_round_type_and_separate_budget_axes(self):
        scope = (ROOT / "templates" / "scope-card.md").read_text(encoding="utf-8")

        for field in (
            "Research scale",
            "Round kind and type",
            "Bibliographic discovery",
            "Full-text acquisition",
            "Substantive review",
            "Named platforms and purposes",
            "Stopping checkpoint",
        ):
            self.assertIn(field, scope)


if __name__ == "__main__":
    unittest.main()
