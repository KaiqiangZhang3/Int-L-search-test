from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_entrypoint_routes_references_by_stage_and_mode(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for target in [
            "references/modes-and-rounds.md",
            "references/source-ledger.md",
            "references/multilingual-retrieval.md",
        ]:
            with self.subTest(target=target):
                self.assertIn(target, text)
        self.assertIn("deep-audit", text.lower())

    def test_default_prompt_describes_user_controlled_research_assistance(self):
        text = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
        self.assertIn("user", text.lower())
        self.assertIn("research", text.lower())
        self.assertNotIn("without substantive legal synthesis", text)

    def test_required_package_files_exist(self):
        required = [
            "SKILL.md",
            "agents/openai.yaml",
            "references/intake-and-approval.md",
            "references/source-strategy.md",
            "references/access-and-privacy.md",
            "references/orchestration.md",
            "references/graph-and-saturation.md",
            "references/deliverables.md",
            "schemas/source-record.schema.json",
            "schemas/candidate-source-record.schema.json",
            "schemas/edge-record.schema.json",
            "schemas/project-state.schema.json",
            "templates/search-plan.md",
            "templates/reader-report.md",
            "templates/subagent-brief.md",
            "scripts/validate_corpus.py",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual([], missing)

    def test_final_corpus_validation_is_an_operational_gate(self):
        orchestration = (ROOT / "references/orchestration.md").read_text(encoding="utf-8")
        deliverables = (ROOT / "references/deliverables.md").read_text(encoding="utf-8")

        self.assertIn("scripts/validate_corpus.py", orchestration)
        self.assertIn("after each canonical merge", orchestration.lower())
        self.assertIn("at every checkpoint", orchestration.lower())
        self.assertIn("scripts/validate_corpus.py", deliverables)
        self.assertIn("before export", deliverables.lower())
        self.assertIn("schema validation alone", deliverables.lower())

    def test_frontmatter_is_minimal_and_trigger_is_specific(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match)
        frontmatter = match.group(1)
        self.assertEqual(2, len(frontmatter.splitlines()))
        self.assertIn("name: international-law-search", frontmatter)
        self.assertIn("description: Use when", frontmatter)
        self.assertIn("international law", frontmatter.lower())
        self.assertIn("retriev", frontmatter.lower())
        self.assertNotIn("research and write", frontmatter.lower())
        self.assertNotIn("approve", frontmatter.lower())
        self.assertNotIn("citation-network", frontmatter.lower())

    def test_scope_approval_survives_urgency_and_modes_preserve_boundaries(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
        approval = re.search(r"(?m)^- .*approv.*(?:scope|next round).*$", text)
        self.assertIsNotNone(approval)
        self.assertIn("urgency", approval.group(0))
        self.assertRegex(approval.group(0), r"(does not|must not|cannot).*(bypass|override)")

        for phrase in [
            "quick mode",
            "standard interactive mode",
            "deep-audit mode",
            "mode choice belongs to the user",
            "retrieval archive",
            "research report",
            "source-grounded descriptive synthesis",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

        self.assertRegex(text, r"research report.*(?:may|allows?).*descriptive synthesis")
        self.assertRegex(text, r"(?:do not|must not).*(?:choose|select).*(?:user(?:'s)? thesis|argumentative position)")
        self.assertRegex(text, r"(?:do not|must not).*draft.*argumentative academic prose")
        self.assertRegex(text, r"(?:do not|must not).*present.*disput.*settled")

        self.assertRegex(text, r"user-facing.*concise")
        self.assertRegex(text, r"structured (records|files|artifacts).*(provenance|detail)|provenance.*structured")
        self.assertIn("main agent", text)

    def test_approval_gate_allows_only_authorized_local_intake_inspection(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("authorized local intake inspection", text)
        self.assertRegex(
            text,
            r"do not begin external retrieval, database search(?:ing)?, or citation expansion before.*approv",
        )

        routing = re.search(r"## routing\n\n(.*?)(?=\n## )", text, re.DOTALL)
        self.assertIsNotNone(routing)
        access_position = routing.group(1).index("references/access-and-privacy.md")
        intake_position = routing.group(1).index("references/intake-and-approval.md")
        self.assertLess(access_position, intake_position)
        self.assertRegex(
            routing.group(1),
            r"access-and-privacy\.md.*before any local inspection",
        )

    def test_availability_review_extent_and_description_basis_are_separate(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        access_section = re.search(
            r"## Access Records\n\n(.*?)(?=\n## )", text, re.DOTALL
        )
        self.assertIsNotNone(access_section)
        for value in [
            "open_full_text",
            "subscription_full_text",
            "identified_inaccessible",
            "abstract_available",
            "metadata_only",
            "access_failure",
            "full_text_substantively_reviewed",
            "selected_sections_reviewed",
            "abstract_reviewed",
            "metadata_verified",
            "not_reviewed",
        ]:
            with self.subTest(value=value):
                self.assertIn(value, access_section.group(1))
        self.assertIn("two independent fields", access_section.group(1))
        self.assertIn("Do not derive one axis from the other", access_section.group(1))
        self.assertIn("description_basis", access_section.group(1))
        self.assertIn("references/access-and-privacy.md", access_section.group(1))

    def test_references_are_routed_from_skill(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        routing = re.search(r"## Routing\n\n(.*?)(?=\n## )", text, re.DOTALL)
        self.assertIsNotNone(routing)
        entries = re.findall(
            r"(?m)^\d+\. Read \[([^]]+)\]\((references/[^)]+)\)([^\n]*)$",
            routing.group(1),
        )
        required_targets = {
            "references/modes-and-rounds.md",
            "references/access-and-privacy.md",
            "references/orchestration.md",
            "references/deliverables.md",
        }
        self.assertTrue(required_targets.issubset({target for _, target, _ in entries}))
        for label, target, timing in entries:
            with self.subTest(target=target):
                self.assertEqual(label, Path(target).name)
                self.assertRegex(timing, r"^ before ")

    def test_openai_metadata_is_quoted_and_invokes_the_skill(self):
        text = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
        lines = [line for line in text.splitlines() if line.strip()]
        self.assertEqual("interface:", lines[0])
        self.assertFalse(any(not line.startswith("  ") for line in lines[1:]))

        values = {}
        for line in lines[1:]:
            match = re.fullmatch(r'  ([a-z_]+): "([^"\n]+)"', line)
            self.assertIsNotNone(match, f"Invalid interface value line: {line}")
            values[match.group(1)] = match.group(2)

        self.assertEqual(
            {"display_name", "short_description", "default_prompt"},
            set(values),
        )
        self.assertGreaterEqual(len(values["short_description"]), 25)
        self.assertLessEqual(len(values["short_description"]), 64)
        self.assertIn("$international-law-search", values["default_prompt"])

    def test_intake_compatibility_file_routes_to_mode_contract(self):
        intake = (ROOT / "references/intake-and-approval.md").read_text(encoding="utf-8").lower()
        for phrase in [
            "compatibility",
            "modes-and-rounds.md",
            "access-and-privacy.md",
        ]:
            self.assertIn(phrase, intake)

    def test_search_plan_separates_approved_choices_from_execution_detail(self):
        template = (ROOT / "templates/search-plan.md").read_text(encoding="utf-8")
        approved = re.search(
            r"## User-approved scope and method\n\n(.*?)(?=\n## )",
            template,
            re.DOTALL,
        )
        appendix = re.search(
            r"## Internal execution appendix\n\n(.*?)(?=\n## )",
            template,
            re.DOTALL,
        )
        approval = re.search(r"## Approval\n\n(.*)$", template, re.DOTALL)
        self.assertIsNotNone(approved)
        self.assertIsNotNone(appendix)
        self.assertIsNotNone(approval)

        for field in [
            "Source tracks:",
            "Languages and reasons:",
            "Access assumptions:",
            "Initial resource budget:",
            "Depth guardrail:",
            "Excluded issues:",
            "Output formats:",
        ]:
            self.assertIn(field, approved.group(1))

        self.assertIn("Exact query strings:", appendix.group(1))
        self.assertIn("Branch mechanics:", appendix.group(1))
        self.assertIn("within the approved envelope", appendix.group(1))
        for field in [
            "`source_track`:",
            "`retrieval_mode`:",
            "Starting depth:",
            "Maximum authorized depth:",
        ]:
            self.assertIn(field, appendix.group(1))

        self.assertIn("{{primary_secondary_or_mixed}}", appendix.group(1))

        self.assertIn("Status: `{{pending_or_approved}}`", approval.group(1))
        self.assertNotIn("Status: `pending`", approval.group(1))
        self.assertIn("Approved by: {{user}}", approval.group(1))
        self.assertIn("Approved at: {{timestamp}}", approval.group(1))
        self.assertIn("Update all three fields atomically before execution.", approval.group(1))

    def test_approval_checkpoint_requires_plan_and_workspace_state_agreement(self):
        template = (ROOT / "templates/search-plan.md").read_text(encoding="utf-8").lower()

        approval = re.search(r"## approval\n\n(.*)$", template, re.DOTALL)
        self.assertIsNotNone(approval)
        for phrase in [
            "workspace state: {{workspace_state_path}}",
            "plan path: {{plan_path}}",
            "one coordinated checkpoint",
            "`state.status=approved`",
            '"approved_by": "{{user}}"',
            '"approved_at": "{{timestamp}}"',
            '"plan_path": "{{plan_path}}"',
            "re-read both artifacts",
            "do not execute",
        ]:
            self.assertIn(phrase, approval.group(1))

    def test_source_strategy_defines_scope_tracks_ranking_and_language_gate(self):
        text = (ROOT / "references/source-strategy.md").read_text(encoding="utf-8").lower()

        for phrase in [
            "primary international-law materials",
            "secondary academic literature",
            "private international law",
            "conflict of laws",
            "general cross-border commercial law",
            "adaptive platform map",
            "direct relevance",
            "citation-network centrality",
            "unique provenance",
            "recency",
            "verifiability",
            "core/canonical",
            "supplementary/emerging",
            "regional",
            "minority",
            "global south",
            "user direction",
            "no fixed english baseline",
            "labeled commentary class",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

        self.assertRegex(
            text,
            r"institutional reports.*working papers.*gray literature",
        )
        self.assertRegex(
            text,
            r"blogs and practitioner analysis.*commentary.*news and ordinary "
            r"(?:web pages|webpages).*discovery-only",
        )

    def test_source_strategy_uses_schema_vocabulary_without_prestige_overload(self):
        text = (ROOT / "references/source-strategy.md").read_text(encoding="utf-8")
        lower = text.lower()

        self.assertRegex(
            lower,
            r"`source_track`.*retrieval branch.*`primary`.*`secondary`.*`mixed`",
        )
        self.assertRegex(lower, r"`source_type`.*document format")
        self.assertRegex(
            lower,
            r"`authority_class`.*corpus class.*`primary`.*`authoritative_secondary`"
            r".*`general_academic`.*`gray_literature`.*`discovery_only`",
        )
        self.assertIn("not a scalar prestige score", lower)
        self.assertRegex(
            lower,
            r"`collection_tier`.*separate.*`core/canonical`.*`supplementary/emerging`",
        )

    def test_access_policy_preserves_truthful_history_and_local_privacy(self):
        text = (ROOT / "references/access-and-privacy.md").read_text(encoding="utf-8")
        lower = text.lower()

        access_section = re.search(
            r"## Access attempts\n\n(.*?)(?=\n## )", text, re.DOTALL
        )
        self.assertIsNotNone(access_section)
        for value in [
            "open_full_text",
            "subscription_full_text",
            "identified_inaccessible",
            "abstract_available",
            "metadata_only",
            "access_failure",
            "full_text_substantively_reviewed",
            "selected_sections_reviewed",
            "abstract_reviewed",
            "metadata_verified",
            "not_reviewed",
        ]:
            with self.subTest(value=value):
                self.assertIn(value, access_section.group(1))

        self.assertIn("two independent evidence axes", lower)
        self.assertIn("do not derive either axis from the other", lower)
        self.assertIn("does not mean that the text was read", lower)
        self.assertIn("does not erase review completed through another route", lower)

        for phrase in [
            "institutional wi-fi",
            "authorized browser sessions",
            "subscriptions",
            "authoritative public alternatives",
            "never bypass",
            "description_basis",
            "separately",
            "every access attempt",
            "retrieval_history",
            "published citation information",
            "do not send unpublished",
            "private annotations",
            "confidential facts",
            "publication status is ambiguous",
            "keep the content local",
            "ask the user",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

        self.assertRegex(
            lower,
            r"before plan approval.*authorized local.*inspection",
        )
        self.assertRegex(
            lower,
            r"external (?:query|search).*only after.*approval",
        )

    def test_deliverable_policy_is_reader_first_and_mode_specific(self):
        text = (ROOT / "references/deliverables.md").read_text(encoding="utf-8")
        lower = text.lower()

        for structured_format in ["csv", "jsonl", "bibtex", "ris", "log", "graph"]:
            with self.subTest(structured_format=structured_format):
                self.assertIn(structured_format, lower)

        for phrase in [
            "word, markdown, or html",
            "same source records",
            "chronology",
            "theme",
            "source type",
            "what the source addresses",
            "why it is included",
            "actual review extent",
            "source-grounded descriptive synthesis",
            "source statement",
            "multi-source trend",
            "cautious inference",
            "research gap",
            "retrieval gap",
            "stopping reason",
            "never claim exhaustive",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

        self.assertIn("must not infer a shared trend", lower)
        self.assertIn("do not present a dispute as settled", lower)
        self.assertIn("choose the user's thesis", lower)
        self.assertIn("draft argumentative academic prose", lower)
        self.assertIn("scripts/validate_reader_report.py", lower)

    def test_reader_report_leads_with_research_understanding_and_reading_path(self):
        text = (ROOT / "templates/reader-report.md").read_text(encoding="utf-8")

        headings = re.findall(r"(?m)^## (.+)$", text)
        self.assertEqual(["问题界定", "研究脉络", "主要立场与争论"], headings[:3])
        self.assertLess(headings.index("推荐阅读路径"), headings.index("检索范围与限制"))
        for field in [
            "{{research_question_scope_and_exclusions}}",
            "{{source_id}}",
            "{{normalized_citation_and_stable_link}}",
            "{{reader_facing_availability_label}}",
            "{{reader_facing_review_extent_label}}",
            "{{description_supported_by_reviewed_material}}",
            "{{inclusion_reason}}",
            "{{reading_context}}",
            "{{searched_questions_platforms_languages_periods_and_source_classes}}",
            "{{unsearched_questions_platforms_languages_periods_and_source_classes}}",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, text)
        self.assertIn("国际法检索档案", text)
        self.assertIn("不作跨来源综合", text)


if __name__ == "__main__":
    unittest.main()
