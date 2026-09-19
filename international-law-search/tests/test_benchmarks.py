import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/benchmark_cases.json"


class BenchmarkFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_covers_entry_paths_safety_and_review_quality(self):
        required_kinds = {
            "topic",
            "question",
            "draft",
            "seed_corpus",
            "privacy",
            "access_gap",
            "depth_guardrail",
            "known_benchmark",
            "retrieval_only_boundary",
            "concise_human_review",
            "doctoral_scale",
            "round_continuation",
            "side_round",
            "synthesis_round",
        }

        kinds = {case["kind"] for case in self.cases}
        self.assertTrue(required_kinds.issubset(kinds))

    def test_each_case_has_an_evaluable_behavioral_contract(self):
        allowed_modes = {"behavioral_review", "retrieval_benchmark"}
        legacy_fields = {
            "id",
            "kind",
            "prompt",
            "expected_behaviors",
            "forbidden_behaviors",
            "evaluation_mode",
        }
        user_centered_fields = {
            "id",
            "kind",
            "prompt",
            "approved_mode",
            "required",
            "prohibited",
            "evaluation_mode",
        }

        self.assertIsInstance(self.cases, list)
        self.assertGreaterEqual(len(self.cases), 10)
        self.assertEqual(len(self.cases), len({case["id"] for case in self.cases}))

        for case in self.cases:
            with self.subTest(case=case.get("id")):
                self.assertIn(set(case), [legacy_fields, user_centered_fields])
                self.assertIsInstance(case["id"], str)
                self.assertTrue(case["id"].strip())
                self.assertIsInstance(case["kind"], str)
                self.assertTrue(case["kind"].strip())
                self.assertIsInstance(case["prompt"], str)
                self.assertTrue(case["prompt"].strip())
                required = case.get("required", case.get("expected_behaviors"))
                prohibited = case.get("prohibited", case.get("forbidden_behaviors"))
                self.assertIsInstance(required, list)
                self.assertTrue(required)
                self.assertTrue(all(item.strip() for item in required))
                self.assertIsInstance(prohibited, list)
                self.assertTrue(prohibited)
                self.assertTrue(all(item.strip() for item in prohibited))
                self.assertIn(case["evaluation_mode"], allowed_modes)

    def test_known_nicaragua_case_requires_retrieval_without_legal_synthesis(self):
        case = next(
            case for case in self.cases if case["kind"] == "known_benchmark"
        )

        self.assertEqual("retrieval_benchmark", case["evaluation_mode"])
        self.assertTrue(
            any("1986 ICJ merits judgment" in item for item in case["expected_behaviors"])
        )
        self.assertTrue(
            any("Friendly Relations Declaration" in item for item in case["expected_behaviors"])
        )
        self.assertTrue(
            any("governing customary-law rule" in item for item in case["forbidden_behaviors"])
        )

    def test_v3_cases_replace_fixed_stages_with_repeatable_round_behaviors(self):
        by_id = {case["id"]: case for case in self.cases}

        self.assertIn("repeat-breadth-expansion", by_id)
        self.assertIn("writing-time-side-round", by_id)
        self.assertIn("inaccessible-foundational-book", by_id)
        self.assertIn("synthesis-only-round", by_id)
        serialized = json.dumps(self.cases)
        self.assertNotIn("Stage 1", serialized)
        self.assertNotIn("Stage 2", serialized)

    def test_v3_benchmarks_retain_safety_and_non_exhaustiveness_controls(self):
        by_id = {case["id"]: case for case in self.cases}

        privacy = by_id["mixed-local-corpus-privacy"]
        access = by_id["subscription-access-gap"]
        depth = by_id["depth-five-high-yield"]
        doctoral = by_id["doctoral-budget-separation"]
        self.assertTrue(any("confidential" in item for item in privacy["forbidden_behaviors"]))
        self.assertTrue(any("full-text review" in item for item in access["forbidden_behaviors"]))
        self.assertTrue(any("approved depth" in item for item in depth["forbidden_behaviors"]))
        self.assertTrue(any("saturation" in item for item in doctoral["prohibited"]))


if __name__ == "__main__":
    unittest.main()
