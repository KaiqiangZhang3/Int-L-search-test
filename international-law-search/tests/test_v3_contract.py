from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class V3ContractTests(unittest.TestCase):
    def test_repeatable_rounds_replace_fixed_stage_progression(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        rounds = (ROOT / "references" / "research-rounds.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("repeatable main rounds", skill.lower())
        self.assertIn("side round", skill.lower())
        self.assertNotIn("Stage 2 cannot begin", skill)
        for value in (
            "breadth_expansion",
            "primary_materials",
            "state_practice",
            "verification",
        ):
            with self.subTest(round_type=value):
                self.assertIn(value, rounds)

    def test_three_budget_axes_and_cumulative_outputs_are_required(self):
        rounds = (ROOT / "references" / "research-rounds.md").read_text(
            encoding="utf-8"
        )
        delivery = (ROOT / "references" / "deliverables.md").read_text(
            encoding="utf-8"
        )

        for value in (
            "bibliographic_discovery",
            "full_text_acquisition",
            "substantive_review",
        ):
            with self.subTest(budget_axis=value):
                self.assertIn(value, rounds)
        for value in (
            "immutable round report",
            "living synthesis",
            "bibliography.csv",
            "index.html",
        ):
            with self.subTest(output=value):
                self.assertIn(value, delivery.lower())


if __name__ == "__main__":
    unittest.main()
