from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
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

    def test_approval_survives_urgency_and_scope_stays_retrieval_only(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
        approval = re.search(r"(?m)^- .*approv.*search plan.*$", text)
        self.assertIsNotNone(approval)
        self.assertIn("urgency", approval.group(0))
        self.assertRegex(approval.group(0), r"(does not|must not|cannot).*(bypass|override)")

        boundaries = {
            "legal-rule synthesis": r"do not synthesize legal rules",
            "scholarly-dispute resolution": r"(do not|must not).*resolve scholarly disputes",
            "argument selection": r"(do not|must not).*(choose|select) an argument",
            "research drafting": r"(do not|must not).*draft.*(literature review|memorandum|article section|paper)",
        }
        for boundary, pattern in boundaries.items():
            with self.subTest(boundary=boundary):
                self.assertRegex(text, pattern)

        self.assertRegex(text, r"user-facing.*concise")
        self.assertRegex(text, r"structured (records|files|artifacts).*(provenance|detail)|provenance.*structured")
        self.assertIn("dynamic saturation", text)
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

    def test_access_status_and_description_basis_are_separate(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        access_section = re.search(
            r"## Access Records\n\n(.*?)(?=\n## )", text, re.DOTALL
        )
        self.assertIsNotNone(access_section)
        statuses = re.findall(r"(?m)^- `([^`]+)`$", access_section.group(1))
        self.assertEqual(
            [
                "Full text read",
                "Full text not read",
                "Abstract only",
                "Metadata only",
                "Access failed",
            ],
            statuses,
        )
        self.assertRegex(access_section.group(1), r"exactly one.*access status")
        self.assertRegex(access_section.group(1), r"separate.*description basis")
        self.assertIn("precedence", access_section.group(1).lower())
        self.assertIn("references/access-and-privacy.md", access_section.group(1))
        self.assertNotRegex(text, r"(?i)use `Full text not read` whenever")

    def test_references_are_routed_from_skill(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        routing = re.search(r"## Routing\n\n(.*?)(?=\n## )", text, re.DOTALL)
        self.assertIsNotNone(routing)
        entries = re.findall(
            r"(?m)^\d+\. Read \[([^]]+)\]\((references/[^)]+)\)([^\n]*)$",
            routing.group(1),
        )
        expected_targets = {
            "references/intake-and-approval.md",
            "references/source-strategy.md",
            "references/access-and-privacy.md",
            "references/orchestration.md",
            "references/graph-and-saturation.md",
            "references/deliverables.md",
        }
        self.assertEqual(expected_targets, {target for _, target, _ in entries})
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

    def test_intake_requires_adaptive_questions_and_explicit_approval(self):
        intake = (ROOT / "references/intake-and-approval.md").read_text(encoding="utf-8").lower()
        for phrase in [
            "ask one material question at a time",
            "topic, question, draft, or seed corpus",
            "read `access-and-privacy.md` before inspecting",
            "wait for explicit approval",
            "atomically set",
        ]:
            self.assertIn(phrase, intake)
        self.assertRegex(
            intake,
            r"do not begin external retrieval, database search(?:ing)?, or citation expansion before approval",
        )

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
        intake = (ROOT / "references/intake-and-approval.md").read_text(encoding="utf-8").lower()
        template = (ROOT / "templates/search-plan.md").read_text(encoding="utf-8").lower()

        for phrase in [
            "one coordinated checkpoint",
            "`state.json`",
            "`state.status` to `approved`",
            "`state.approved_plan`",
            "`approved_by`, `approved_at`, and `plan_path`",
            "re-read the plan artifact and `state.json`",
            "verify that both artifacts agree",
            "interrupted or inconsistent",
            "do not execute",
        ]:
            self.assertIn(phrase, intake)

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
            "user approval",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

        self.assertRegex(
            text,
            r"institutional reports.*working papers.*gray literature",
        )
        self.assertRegex(
            text,
            r"blogs, news, and ordinary (?:web pages|webpages).*discovery-only",
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
        definitions = re.findall(
            r"(?m)^(\d+)\. `([^`]+)`: ([^\n]+)$", access_section.group(1)
        )
        self.assertEqual(
            [
                ("1", "Full text read"),
                ("2", "Full text not read"),
                ("3", "Abstract only"),
                ("4", "Metadata only"),
                ("5", "Access failed"),
            ],
            [(number, status) for number, status, _ in definitions],
        )
        definition_text = {status: definition.lower() for _, status, definition in definitions}
        self.assertIn("substantive full text", definition_text["Full text read"])
        self.assertIn("full text was not examined", definition_text["Full text not read"])
        self.assertIn("unavailable or intentionally unopened", definition_text["Full text not read"])
        self.assertIn("no full text is identified or available", definition_text["Abstract only"])
        self.assertIn("abstract was examined", definition_text["Abstract only"])
        self.assertIn("neither full text nor abstract was examined", definition_text["Metadata only"])
        self.assertIn("usable metadata exists", definition_text["Metadata only"])
        self.assertIn("no usable source content", definition_text["Access failed"])
        self.assertIn("candidate or limited record", definition_text["Access failed"])

        self.assertIn("apply the first matching status in this precedence", lower)
        self.assertIn("most informative, highest-precedence outcome", lower)
        self.assertIn("preserves every route", lower)
        self.assertRegex(
            lower,
            r"full-text copy is identified.*abstract.*`full text not read`",
        )
        self.assertRegex(
            lower,
            r"no full text is identified.*abstract.*`abstract only`",
        )
        self.assertRegex(
            lower,
            r"broken discovery lead.*`access failed`",
        )

        for phrase in [
            "institutional wi-fi",
            "authorized browser sessions",
            "subscriptions",
            "authoritative public alternatives",
            "never bypass",
            "exactly one",
            "description basis",
            "separate field",
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

    def test_deliverable_policy_is_traceable_and_non_analytical(self):
        text = (ROOT / "references/deliverables.md").read_text(encoding="utf-8")
        lower = text.lower()

        for structured_format in ["csv", "jsonl", "bibtex", "ris", "log", "graph"]:
            with self.subTest(structured_format=structured_format):
                self.assertIn(structured_format, lower)

        for phrase in [
            "word, markdown, or html",
            "same corpus",
            "stable source ids",
            "approved subquestion",
            "chronology",
            "theme",
            "source type",
            "citation path",
            "what the source addresses",
            "why it was included",
            "access status",
            "description basis",
            "retrieval value",
            "searched and not searched",
            "full-text gaps",
            "verification gaps",
            "stopping reason",
            "approaches saturation within the approved scope",
            "must not claim exhaustive",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

        self.assertRegex(
            lower,
            r"each edge separately.*from id.*relation.*to id.*status.*evidence location",
        )
        self.assertRegex(
            lower,
            r"candidate status.*shown.*even when.*evidence",
        )
        self.assertIn("endpoint ids, relation, and status", lower)
        self.assertNotIn("stable relationship id", lower)
        self.assertRegex(
            lower,
            r"gap entr(?:y|ies).*stable source id.*endpoint ids, relation, and status",
        )

        for sentence in [
            "Do not synthesize legal rules.",
            "Do not resolve scholarly disputes.",
            "Do not recommend an argument.",
            "Do not draft academic prose.",
        ]:
            with self.subTest(sentence=sentence):
                self.assertIn(sentence, text)

    def test_reader_report_has_concise_review_fields(self):
        text = (ROOT / "templates/reader-report.md").read_text(encoding="utf-8")

        expected_sections = [
            "Scope, stopping reason, and coverage conclusion",
            "Retrieval-oriented navigation",
            "Core/canonical sources",
            "Supplementary/emerging sources",
            "Key citation paths",
            "Coverage and gaps",
        ]
        self.assertEqual(
            expected_sections,
            re.findall(r"(?m)^## (.+)$", text),
        )

        for field in [
            "{{coverage_conclusion}}",
            "{{approved_subquestion_navigation}}",
            "{{theme_navigation}}",
            "{{source_type_navigation}}",
            "{{chronology_navigation}}",
            "{{citation_path_navigation}}",
            "{{stable_id}}",
            "{{access_status}}",
            "{{description_basis}}",
            "{{source_description}}",
            "{{inclusion_reason}}",
            "{{from_id}}",
            "{{relation}}",
            "{{to_id}}",
            "{{edge_status}}",
            "{{evidence_location}}",
            "{{retrieval_value}}",
            "{{gap_source_id}}",
            "{{gap_from_id}}",
            "{{gap_relation}}",
            "{{gap_to_id}}",
            "{{gap_edge_status}}",
        ]:
            with self.subTest(field=field):
                self.assertIn(field, text)

        for dimension in [
            "Approved subquestion",
            "Platform",
            "Language",
            "Period / chronology",
            "Source class",
        ]:
            with self.subTest(dimension=dimension):
                self.assertRegex(text, rf"(?m)^\| {re.escape(dimension)} \|")

        self.assertIn(
            "Candidate status must remain visible even when an evidence location is present.",
            text,
        )
        self.assertIn("It must not claim exhaustive coverage.", text)


if __name__ == "__main__":
    unittest.main()
