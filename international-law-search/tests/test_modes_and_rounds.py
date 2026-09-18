import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/benchmark_cases.json"
USER_CENTERED_FIXTURES = ROOT / "tests/fixtures/user-centered"
MODES_AND_ROUNDS = ROOT / "references/modes-and-rounds.md"
MULTILINGUAL_RETRIEVAL = ROOT / "references/multilingual-retrieval.md"
SCOPE_CARD = ROOT / "templates/scope-card.md"
BREADTH_CHECKPOINT = ROOT / "templates/breadth-checkpoint.md"


def user_centered_fixture(name):
    return (USER_CENTERED_FIXTURES / name).read_text(encoding="utf-8")


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

    def test_chinese_branch_has_its_own_purpose_vocabulary_platforms_and_budget(self):
        branch = json.loads(user_centered_fixture("chinese-branch.json"))

        self.assertEqual(branch["language"], "zh")
        self.assertTrue(branch["purpose"])
        self.assertTrue(branch["local_vocabulary"])
        self.assertGreaterEqual(set(branch["platforms"]), {"CNKI", "PKULaw", "Wanfang"})
        self.assertGreaterEqual(
            set(branch["budget"]),
            {"queries", "candidates", "full_text_reviews"},
        )

    def test_each_substantive_language_is_an_independent_retrieval_branch(self):
        text = MULTILINGUAL_RETRIEVAL.read_text(encoding="utf-8").lower()

        for required in [
            "research purpose",
            "local vocabulary",
            "platforms",
            "access assumptions",
            "budget",
            "authority relationship",
            "actual contribution",
            "remaining gap",
        ]:
            with self.subTest(required=required):
                self.assertIn(required, text)
        self.assertIn("no fixed english baseline", text)
        self.assertRegex(text, r"auxiliary language.*isolated verification")

    def test_regional_and_global_south_coverage_is_planned_and_measured(self):
        scope = SCOPE_CARD.read_text(encoding="utf-8").lower()
        checkpoint = BREADTH_CHECKPOINT.read_text(encoding="utf-8").lower()
        contract = MULTILINGUAL_RETRIEVAL.read_text(encoding="utf-8").lower()

        for dimension in ["regions", "languages", "platforms", "perspectives"]:
            with self.subTest(dimension=dimension):
                self.assertIn(dimension, scope)
        self.assertIn("global south", scope)
        self.assertIn("coverage targets", scope)

        self.assertIn("actual additions", checkpoint)
        self.assertIn("remaining coverage gaps", checkpoint)
        self.assertIn("global south", checkpoint)
        self.assertRegex(contract, r"one non-english source.*(?:not|never).*representative")

    def test_mode_contract_routes_substantive_language_work_to_branch_contract(self):
        text = self.read_contract().lower()

        self.assertIn("multilingual-retrieval.md", text)
        self.assertRegex(text, r"substantive language.*(?:branch|purpose).*(?:budget|approval)")


if __name__ == "__main__":
    unittest.main()
