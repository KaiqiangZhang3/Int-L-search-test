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
        }

        kinds = {case["kind"] for case in self.cases}
        self.assertTrue(required_kinds.issubset(kinds))

    def test_each_case_has_an_evaluable_behavioral_contract(self):
        allowed_modes = {"behavioral_review", "retrieval_benchmark"}
        required_fields = {
            "id",
            "kind",
            "prompt",
            "expected_behaviors",
            "forbidden_behaviors",
            "evaluation_mode",
        }

        self.assertIsInstance(self.cases, list)
        self.assertGreaterEqual(len(self.cases), 10)
        self.assertEqual(len(self.cases), len({case["id"] for case in self.cases}))

        for case in self.cases:
            with self.subTest(case=case.get("id")):
                self.assertEqual(required_fields, set(case))
                self.assertIsInstance(case["id"], str)
                self.assertTrue(case["id"].strip())
                self.assertIsInstance(case["kind"], str)
                self.assertTrue(case["kind"].strip())
                self.assertIsInstance(case["prompt"], str)
                self.assertTrue(case["prompt"].strip())
                self.assertIsInstance(case["expected_behaviors"], list)
                self.assertTrue(case["expected_behaviors"])
                self.assertTrue(all(item.strip() for item in case["expected_behaviors"]))
                self.assertIsInstance(case["forbidden_behaviors"], list)
                self.assertTrue(case["forbidden_behaviors"])
                self.assertTrue(all(item.strip() for item in case["forbidden_behaviors"]))
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


if __name__ == "__main__":
    unittest.main()
