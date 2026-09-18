from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/user-centered"
sys.path.insert(0, str(ROOT / "scripts"))

from validate_reader_report import validate_report


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def markdown_headings(text: str) -> list[str]:
    return [
        line.removeprefix("## ").strip()
        for line in text.splitlines()
        if line.startswith("## ")
    ]


class ReaderFirstReportContractTests(unittest.TestCase):
    def test_archive_has_a_repeatable_source_item_and_mixed_request_response(self):
        template = (ROOT / "templates/reader-report.md").read_text(encoding="utf-8")
        deliverables = (ROOT / "references/deliverables.md").read_text(
            encoding="utf-8"
        )
        archive = template.split("# 国际法检索档案", 1)[1]
        for field in [
            "{{normalized_citation_and_stable_link}}",
            "{{reader_facing_availability_label}}",
            "{{reader_facing_review_extent_label}}",
            "{{description_supported_by_reviewed_material}}",
            "{{inclusion_reason}}",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, archive)
        self.assertIn("## Mixed requests", deliverables)
        self.assertIn("neutral argument paths", deliverables)
        self.assertIn("user chooses the position", deliverables)

    def test_deliverable_contract_supports_reader_choices_and_report_boundaries(self):
        contract = (ROOT / "references/deliverables.md").read_text(encoding="utf-8")

        for value in ["Word", "Markdown", "HTML", "OSCOLA", "Bluebook", "Chicago", "GB/T 7714"]:
            with self.subTest(value=value):
                self.assertIn(value, contract)
        for ordering in ["theme", "chronology", "authority", "relevance", "priority", "position", "source type"]:
            with self.subTest(ordering=ordering):
                self.assertIn(ordering, contract.lower())
        self.assertIn("theme plus reading priority", contract.lower())
        self.assertIn("retrieval archive", contract.lower())
        self.assertIn("research report", contract.lower())
        self.assertIn("source-grounded descriptive synthesis", contract.lower())
        self.assertIn("scripts/validate_reader_report.py", contract)

    def test_chinese_template_leads_with_field_understanding(self):
        report = (ROOT / "templates/reader-report.md").read_text(encoding="utf-8")
        headings = markdown_headings(report)

        self.assertEqual(["问题界定", "研究脉络", "主要立场与争论"], headings[:3])
        self.assertLess(headings.index("推荐阅读路径"), headings.index("检索范围与限制"))

    def test_paired_reports_preserve_distinct_synthesis_boundaries(self):
        research_report = fixture("research-report.md")
        archive = fixture("retrieval-archive.md")

        headings = markdown_headings(research_report)
        self.assertEqual(["问题界定", "研究脉络", "主要立场与争论"], headings[:3])
        self.assertLess(headings.index("推荐阅读路径"), headings.index("检索范围与限制"))
        for label in ["来源陈述（依据：", "多来源趋势（依据：", "谨慎归纳（依据："]:
            self.assertIn(label, research_report)

        self.assertNotIn("多项来源共同显示", archive)
        self.assertNotIn("多来源趋势", archive)
        self.assertNotIn("谨慎归纳", archive)

    def test_paired_final_reports_pass_deterministic_validation(self):
        for name in ["research-report.md", "retrieval-archive.md"]:
            with self.subTest(name=name):
                self.assertEqual([], validate_report(fixture(name), language="zh", final=True))

    def test_validator_rejects_unresolved_markers_and_manual_review(self):
        report = "# Report\n\n## 问题界定\n\n{{scope}}\n\nmanual review required\n\nTODO"
        errors = validate_report(report, language="zh", final=True)

        self.assertTrue(any("Unresolved marker" in error for error in errors))
        self.assertIn("Final report contains unresolved manual-review items", errors)

    def test_validator_requires_citations_on_declared_synthesis(self):
        report = (
            "# Report\n\n## 问题界定\n\n范围。\n\n"
            "## 研究脉络\n\n- 多来源趋势：若干材料呈现某趋势。\n\n"
            "## 主要立场与争论\n\n尚待比较。"
        )
        errors = validate_report(report, language="zh", final=True)

        self.assertTrue(any("lacks source citation" in error for error in errors))

    def test_validator_rejects_machine_state_as_chinese_opening(self):
        report = "# Report\n\n## 检索范围与限制\n\n范围。\n\n## 问题界定\n\n问题。"
        errors = validate_report(report, language="zh", final=True)

        self.assertTrue(any("machine-state section" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
