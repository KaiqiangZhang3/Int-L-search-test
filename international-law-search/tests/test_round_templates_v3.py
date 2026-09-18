from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class RoundTemplateV3Tests(unittest.TestCase):
    def read_template(self, name):
        return (TEMPLATES / name).read_text(encoding="utf-8")

    def test_round_report_saves_complete_next_round_designs(self):
        report = self.read_template("round-report.md")
        menu = self.read_template("next-round-menu.md")

        for field in (
            "Round purpose",
            "Knowledge changes",
            "Planned and actual budget",
            "Next-round menu",
        ):
            with self.subTest(report_field=field):
                self.assertIn(field, report)
        for field in (
            "Question addressed",
            "Retrieval objects",
            "Starting seeds",
            "Method",
            "Three-axis budget",
            "Expected output",
            "Exclusions",
        ):
            with self.subTest(menu_field=field):
                self.assertIn(field, menu)

    def test_side_round_report_starts_with_claim_support_package(self):
        text = self.read_template("side-round-report.md")
        headings = [
            line.removeprefix("## ")
            for line in text.splitlines()
            if line.startswith("## ")
        ]

        self.assertEqual("Support verdict", headings[0])
        for value in (
            "supported",
            "partially_supported",
            "unsupported",
            "counterevidence_found",
            "Safer formulation",
            "Evidence functions and locators",
            "Contrary evidence and limits",
            "Footnote-ready citations",
        ):
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_round_spec_requires_user_approval_and_three_budget_axes(self):
        text = self.read_template("round-spec.md")

        self.assertIn("Approval status", text)
        self.assertIn("pending_or_approved", text)
        for value in (
            "Bibliographic discovery",
            "Full-text acquisition",
            "Substantive review",
        ):
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_legacy_checkpoint_templates_route_without_forcing_progression(self):
        for name in ("breadth-checkpoint.md", "depth-checkpoint.md"):
            with self.subTest(template=name):
                text = self.read_template(name)
                self.assertIn("round-report.md", text)
                self.assertNotIn("Stage 2 must not begin", text)


if __name__ == "__main__":
    unittest.main()
