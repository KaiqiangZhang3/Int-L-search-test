import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/benchmark_cases.json"
USER_CENTERED_FIXTURES = ROOT / "tests/fixtures/user-centered"
MODES_AND_ROUNDS = ROOT / "references/modes-and-rounds.md"
READINESS_AND_SCALE = ROOT / "references/readiness-and-scale.md"
RESEARCH_ROUNDS = ROOT / "references/research-rounds.md"
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
    def test_quick_mode_has_a_resumable_cross_session_handoff(self):
        text = MODES_AND_ROUNDS.read_text(encoding="utf-8").lower()
        self.assertIn("minimum resumable handoff", text)
        self.assertIn("session-handoff.md", text)
        self.assertIn("across sessions", text)
        self.assertIn("source ledger", text)
        self.assertIn("project-level decisions", text)

    def test_hard_deadline_uses_a_single_compact_approval_step(self):
        text = READINESS_AND_SCALE.read_text(encoding="utf-8").lower()
        self.assertIn("hard deadline", text)
        self.assertIn("one concise scope card", text)
        self.assertIn("discovery", text)
        self.assertIn("acquisition", text)
        self.assertIn("review", text)

    def test_scope_card_exposes_delivery_multilingual_and_access_choices(self):
        text = (ROOT / "templates/scope-card.md").read_text(encoding="utf-8")
        for field in [
            "Output type",
            "File format",
            "Citation style",
            "Branch purpose",
            "Local vocabulary",
            "Platforms",
            "Branch budget",
            "Branch access assumptions",
            "Text authority relationship",
            "Network context",
            "Authentication status",
            "Verified source access",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, text)

    def read_contract(self):
        self.assertTrue(
            MODES_AND_ROUNDS.is_file(),
            "The public mode-and-round contract is missing",
        )
        return MODES_AND_ROUNDS.read_text(encoding="utf-8")

    def test_main_rounds_do_not_silently_authorize_depth(self):
        text = RESEARCH_ROUNDS.read_text(encoding="utf-8")
        lower = text.lower()

        self.assertIn("repeatable main rounds", lower)
        self.assertIn("starting seeds", lower)
        self.assertIn("approval authorizes only that specification", lower)
        self.assertRegex(lower, r"new decision before changing.*seed")

    def test_depth_round_honors_branch_and_source_decisions(self):
        text = RESEARCH_ROUNDS.read_text(encoding="utf-8").lower()

        self.assertIn("depth", text)
        self.assertIn("review without new discovery", text)
        self.assertIn("selected-seed tracing", text)
        self.assertRegex(text, r"new(?:ly)? suggested seed.*requires approval")

    def test_quick_mode_is_upgradeable_without_restart(self):
        text = self.read_contract()
        lower = text.lower()

        self.assertIn("Quick", text)
        self.assertIn("reuse", lower)
        self.assertIn("existing source ledger", lower)
        self.assertIn("must not restart", lower)
        self.assertRegex(lower, r"quick.*(?:no durable|without).*(?:workspace|handoff)")

    def test_rounds_expose_multidimensional_budget_and_actual_use(self):
        text = RESEARCH_ROUNDS.read_text(encoding="utf-8").lower()

        for dimension in [
            "time cap",
            "platform",
            "query",
            "bibliographic_discovery",
            "full_text_acquisition",
            "substantive_review",
            "seed",
            "tracing depth",
            "language",
        ]:
            with self.subTest(dimension=dimension):
                self.assertIn(dimension, text)
        self.assertIn("planned and actual budgets", text)
        self.assertIn("actual counts", text)

    def test_closure_rules_preserve_user_control(self):
        text = self.read_contract().lower() + RESEARCH_ROUNDS.read_text(encoding="utf-8").lower()

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
