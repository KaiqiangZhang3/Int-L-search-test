import json
from pathlib import Path
import unittest


FIXTURES = Path(__file__).resolve().parent / "fixtures/user-centered"


def load_json(relative_path):
    return json.loads((FIXTURES / relative_path).read_text(encoding="utf-8"))


def load_jsonl(relative_path):
    return [
        json.loads(line)
        for line in (FIXTURES / relative_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class UserCenteredE2ETests(unittest.TestCase):
    def test_quick_result_upgrades_without_losing_sources_or_user_decisions(self):
        quick = load_json("quick-upgrade/quick-session.json")
        standard = load_json("quick-upgrade/standard-session.json")

        self.assertTrue(
            set(quick["source_keys"]).issubset(standard["source_keys"])
        )
        self.assertEqual(
            quick["user_decisions"], standard["inherited_user_decisions"]
        )
        self.assertFalse(standard["restart_performed"])
        self.assertEqual([], standard["selected_seeds"])

    def test_quick_fixture_has_approved_scope_upgrade_checkpoint_and_ledger(self):
        session = load_json("quick-upgrade/quick-session.json")
        ledger = load_jsonl("quick-upgrade/source-ledger.jsonl")

        self.assertEqual("approved", session["scope_approval"]["status"])
        self.assertTrue(session["scope_approval"]["authorized_delivery"])
        self.assertTrue(session["upgrade_checkpoint"]["reuse_existing_ledger"])
        self.assertFalse(session["upgrade_checkpoint"]["restart_required"])
        self.assertGreaterEqual(len(ledger), 10)
        self.assertLessEqual(len(ledger), 15)
        self.assertEqual(
            set(session["source_keys"]),
            {record["source_key"] for record in ledger},
        )

        required = {
            "source_key",
            "identity_evidence",
            "discovery_provenance",
            "availability",
            "review_extent",
            "description_basis",
            "description",
            "inclusion_reason",
            "user_decisions",
        }
        for record in ledger:
            with self.subTest(source_key=record["source_key"]):
                self.assertTrue(required.issubset(record))

    def test_standard_fixture_requires_a_user_choice_before_any_next_round(self):
        round_1 = load_json("standard-corporate-role/round-1.json")

        self.assertEqual([], round_1["selected_seeds"])
        self.assertEqual([], round_1["vertical_branches"])
        self.assertTrue(
            {"select_seed", "expand_branch", "stop_and_deliver"}.issubset(
                round_1["decision_panel"]["allowed_actions"]
            )
        )

    def test_standard_breadth_result_is_bounded_and_reviewable(self):
        round_1 = load_json("standard-corporate-role/round-1.json")

        self.assertGreaterEqual(len(round_1["intake"]["ambiguities_presented"]), 5)
        self.assertFalse(round_1["scope_approval"]["systematic_citation_tracing"])
        self.assertGreaterEqual(len(round_1["candidate_seeds"]), 5)
        self.assertLessEqual(len(round_1["candidate_seeds"]), 10)
        self.assertEqual(
            set(round_1["candidate_seeds"]),
            {
                item["source_key"]
                for item in round_1["annotated_bibliography"]
            },
        )
        self.assertEqual(
            {"planned", "actual"}, set(round_1["budget"])
        )
        self.assertTrue(
            round_1["decision_panel"]["requires_user_response_before_depth"]
        )

    def test_standard_depth_round_respects_later_user_choices(self):
        decision = load_json("standard-corporate-role/user-decision.json")
        depth = load_json("standard-corporate-role/depth-round.json")

        selected = set(decision["selected_seeds"])
        traced = {branch["seed_key"] for branch in depth["vertical_branches"]}
        self.assertEqual(selected, traced)
        self.assertNotIn(
            decision["review_without_tracing"], traced
        )
        self.assertTrue(
            set(decision["deleted_branches"]).isdisjoint(depth["active_branches"])
        )
        self.assertEqual(decision["decision_id"], depth["authorization_id"])


if __name__ == "__main__":
    unittest.main()
