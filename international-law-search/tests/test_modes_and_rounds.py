import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/benchmark_cases.json"
MODES_AND_ROUNDS = ROOT / "references/modes-and-rounds.md"


class UserCenteredBenchmarkContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cases = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.cases = {case["id"]: case for case in cases}

    def test_user_centered_cases_define_mode_and_observable_behavior(self):
        expected_ids = {
            "vague-corporate-role-readiness",
            "standard-round-1-checkpoint",
            "user-selected-seeds",
            "quick-mode-upgrade",
            "independent-chinese-branch",
            "reader-first-report",
            "retrieval-archive-boundary",
            "research-report-boundary",
        }
        self.assertTrue(expected_ids.issubset(self.cases))

        for case_id in expected_ids:
            with self.subTest(case=case_id):
                case = self.cases[case_id]
                self.assertIn(
                    case["approved_mode"],
                    {"quick", "standard_interactive", "deep_audit"},
                )
                self.assertTrue(case["prompt"].strip())
                self.assertTrue(case["required"])
                self.assertTrue(case["prohibited"])
                self.assertTrue(all(item.strip() for item in case["required"]))
                self.assertTrue(all(item.strip() for item in case["prohibited"]))

    def test_archive_and_report_are_paired_boundaries(self):
        archive = self.cases["retrieval-archive-boundary"]
        report = self.cases["research-report-boundary"]

        self.assertEqual(archive["approved_mode"], report["approved_mode"])
        self.assertTrue(
            any("Omits cross-source synthesis" in item for item in archive["required"])
        )
        self.assertTrue(
            any("cited descriptive synthesis" in item for item in report["required"])
        )


class ModesAndRoundsContractTests(unittest.TestCase):
    def read_contract(self):
        self.assertTrue(
            MODES_AND_ROUNDS.is_file(),
            "The public mode-and-round contract is missing",
        )
        return MODES_AND_ROUNDS.read_text(encoding="utf-8")

    def test_standard_mode_requires_user_seed_selection_before_depth(self):
        text = self.read_contract()
        lower = text.lower()

        self.assertIn("Stage 1", text)
        self.assertIn("must stop", lower)
        self.assertIn("user-confirmed seeds", lower)
        self.assertRegex(
            lower,
            r"stage 2.*(?:cannot|must not).*until.*user.*(?:selects|confirms)",
        )

    def test_depth_round_honors_branch_and_source_decisions(self):
        text = self.read_contract().lower()

        self.assertIn("delete", text)
        self.assertIn("review without tracing", text)
        self.assertRegex(text, r"trace only.*user-confirmed seeds")
        self.assertRegex(text, r"new(?:ly)? suggested seeds.*user confirmation")

    def test_quick_mode_is_upgradeable_without_restart(self):
        text = self.read_contract()
        lower = text.lower()

        self.assertIn("Quick mode", text)
        self.assertIn("reuse", lower)
        self.assertIn("existing source ledger", lower)
        self.assertIn("must not restart", lower)
        self.assertRegex(lower, r"quick.*(?:does not require|without).*(?:graph|audit workspace)")

    def test_rounds_expose_multidimensional_budget_and_actual_use(self):
        text = self.read_contract().lower()

        for dimension in [
            "search time",
            "platform",
            "query",
            "candidate",
            "full-text",
            "seed",
            "tracing depth",
            "language",
        ]:
            with self.subTest(dimension=dimension):
                self.assertIn(dimension, text)
        self.assertIn("planned and actual", text)
        self.assertRegex(text, r"budget[- ](?:limited|paused).*(?:not|cannot).*saturation")

    def test_closure_rules_preserve_user_control(self):
        text = self.read_contract().lower()

        self.assertRegex(
            text,
            r"quick.*scope.*approval.*authoriz(?:es|e).*delivery",
        )
        self.assertRegex(
            text,
            r"standard.*deep-audit.*(?:explicit|user).*authoriz.*closure",
        )
        self.assertIn("stop and deliver", text)


if __name__ == "__main__":
    unittest.main()
