# International Law Search Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-entry, retrieval-only international-law skill that obtains user approval for a search plan, searches primary and secondary sources, expands citation networks, preserves auditable project state, and exports concise reader-facing and structured results.

**Architecture:** Keep the user-facing `SKILL.md` short and route each workflow stage to focused reference files. Use JSON Schema as the canonical contract, small standard-library Python utilities for deterministic workspace creation, record merging, and round metrics, and contract/fixture tests to protect approval, access, privacy, provenance, and non-synthesis boundaries.

**Tech Stack:** Codex skill Markdown and YAML, JSON Schema Draft 2020-12, Python 3 standard library, `unittest`, Git.

---

## File map

Create one distributable skill directory at `international-law-search/`:

- `international-law-search/SKILL.md` — entry point, routing logic, stage gates, and hard boundaries.
- `international-law-search/agents/openai.yaml` — discoverable display metadata and default prompt.
- `international-law-search/references/intake-and-approval.md` — adaptive intake and plan approval protocol.
- `international-law-search/references/source-strategy.md` — primary/secondary source map, multilingual strategy, and ranking.
- `international-law-search/references/access-and-privacy.md` — access labels, local-material handling, and privacy rules.
- `international-law-search/references/orchestration.md` — branch design, subagent contracts, merge ownership, and failure isolation.
- `international-law-search/references/graph-and-saturation.md` — graph expansion, evidence-bearing edges, depth guardrail, and dynamic stopping.
- `international-law-search/references/deliverables.md` — raw exports and concise reader-facing presentation.
- `international-law-search/schemas/source-record.schema.json` — canonical source-node contract.
- `international-law-search/schemas/edge-record.schema.json` — relationship and evidence contract.
- `international-law-search/schemas/project-state.schema.json` — resumable run state and approved-plan contract.
- `international-law-search/templates/search-plan.md` — user approval artifact.
- `international-law-search/templates/reader-report.md` — concise human-review artifact.
- `international-law-search/templates/subagent-brief.md` — consistent delegated-branch instructions.
- `international-law-search/scripts/init_workspace.py` — initialize a safe, explicit run directory.
- `international-law-search/scripts/corpus_ops.py` — deterministic normalization, deduplication, and merge helpers.
- `international-law-search/scripts/round_metrics.py` — produce saturation evidence without making the stopping decision.
- `international-law-search/tests/test_skill_contract.py` — static workflow and boundary contract tests.
- `international-law-search/tests/test_workspace.py` — workspace initialization tests.
- `international-law-search/tests/test_corpus_ops.py` — canonicalization and merge tests.
- `international-law-search/tests/test_round_metrics.py` — marginal-yield metric tests.
- `international-law-search/tests/fixtures/benchmark_cases.json` — known workflow scenarios for later manual/e2e evaluation.
- `international-law-search/README.md` — installation, validation, and scope summary.

Do not create a general research engine, database-specific scraper, browser automation layer, citation-style formatter, or paper-writing module in version 1. Those are independent systems and are outside the approved design.

### Task 1: Scaffold the package and lock the behavioral contract

**Files:**
- Create: `international-law-search/tests/test_skill_contract.py`
- Create: `international-law-search/agents/openai.yaml`
- Create: `international-law-search/SKILL.md`

- [ ] **Step 1: Write the failing package-contract test**

Create `international-law-search/tests/test_skill_contract.py` with:

```python
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
            "schemas/edge-record.schema.json",
            "schemas/project-state.schema.json",
            "templates/search-plan.md",
            "templates/reader-report.md",
            "templates/subagent-brief.md",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual([], missing)

    def test_frontmatter_is_minimal_and_trigger_is_specific(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match)
        frontmatter = match.group(1)
        self.assertIn("name: international-law-search", frontmatter)
        self.assertIn("description:", frontmatter)
        self.assertIn("international law", frontmatter.lower())
        self.assertIn("retriev", frontmatter.lower())
        self.assertNotIn("research and write", frontmatter.lower())

    def test_approval_and_non_synthesis_gates_are_explicit(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
        required_phrases = [
            "do not begin retrieval before the user approves the search plan",
            "do not synthesize legal rules",
            "full text not read",
            "dynamic saturation",
            "main agent",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, text)

    def test_references_are_routed_from_skill(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for name in [
            "intake-and-approval.md",
            "source-strategy.md",
            "access-and-privacy.md",
            "orchestration.md",
            "graph-and-saturation.md",
            "deliverables.md",
        ]:
            self.assertIn(name, text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the contract test and verify it fails**

Run:

```bash
python3 -m unittest international-law-search/tests/test_skill_contract.py -v
```

Expected: failures listing the missing package files.

- [ ] **Step 3: Create the entry point and agent metadata**

Create `international-law-search/SKILL.md` with:

```markdown
---
name: international-law-search
description: Use when a user needs auditable international law source retrieval for academic writing or scholarship, including interactive search planning, primary and secondary source discovery, citation-network tracing, local seed materials, multilingual coverage, or resumable corpus exports. This skill retrieves and describes sources; it does not perform substantive legal synthesis or draft the user's research.
---

# International Law Search

Retrieve international-law materials through an approved, auditable search plan. Keep user-facing choices and reports concise. Preserve detailed provenance in structured files.

## Hard boundaries

- Do not begin retrieval before the user approves the search plan.
- Do not synthesize legal rules, resolve scholarly disputes, select an argument, or draft a literature review, memorandum, article section, or paper.
- Describe an individual source only from material actually accessed, and label the basis as full text, abstract, or metadata.
- Use `Full text not read` whenever a retained source was not read in full.
- Never treat model memory as retrieval or verification evidence.
- Never send unpublished prose, private annotations, confidential facts, or non-public attachments to external services.

## Workflow

1. Read `references/intake-and-approval.md`. Inspect authorized local context, ask one material question at a time, and obtain approval for the written search plan.
2. Read `references/source-strategy.md` and run coordinated primary-source and secondary-literature branches.
3. Read `references/access-and-privacy.md` before using local files, subscription resources, institutional access, or external queries.
4. Read `references/orchestration.md` before deciding whether complexity warrants subagents. The main agent alone owns the canonical corpus and final merge.
5. Read `references/graph-and-saturation.md` before citation expansion. Treat five levels as a usual guardrail and dynamic saturation as the stopping principle.
6. Read `references/deliverables.md` before export. Generate every output from the same canonical records.

## Approval exceptions

After approval, continue autonomously unless a branch materially changes scope, requires a new language or jurisdiction, encounters a coverage-critical access gap, reaches the approved budget before dynamic saturation, or justifies expansion beyond the usual depth guardrail.

## Completion standard

Deliver a resumable corpus with verified identities, honest access labels, evidence-bearing relationships, search provenance, unresolved gaps, concise source descriptions, retrieval-oriented navigation, and an in-scope coverage statement. Claim only that the search approaches saturation within the approved scope.
```

Create `international-law-search/agents/openai.yaml` with:

```yaml
interface:
  display_name: "International Law Search"
  short_description: "Retrieve and trace international-law sources"
  default_prompt: "Build an auditable international-law retrieval plan, ask me to approve it, then retrieve and organize sources without doing substantive legal synthesis."
```

- [ ] **Step 4: Re-run the focused test**

Run:

```bash
python3 international-law-search/tests/test_skill_contract.py SkillContractTests.test_frontmatter_is_minimal_and_trigger_is_specific SkillContractTests.test_approval_and_non_synthesis_gates_are_explicit -v
```

Expected: both focused tests pass.

- [ ] **Step 5: Commit the scaffold**

```bash
git add international-law-search/SKILL.md international-law-search/agents/openai.yaml international-law-search/tests/test_skill_contract.py
git commit -m "feat: scaffold international law search skill"
```

### Task 2: Implement adaptive intake and the approval artifact

**Files:**
- Create: `international-law-search/references/intake-and-approval.md`
- Create: `international-law-search/templates/search-plan.md`
- Modify: `international-law-search/tests/test_skill_contract.py`

- [ ] **Step 1: Add failing intake assertions**

Add this method to `SkillContractTests`:

```python
    def test_intake_requires_adaptive_questions_and_explicit_approval(self):
        intake = (ROOT / "references/intake-and-approval.md").read_text(encoding="utf-8").lower()
        template = (ROOT / "templates/search-plan.md").read_text(encoding="utf-8").lower()
        for phrase in [
            "ask one material question at a time",
            "topic, question, draft, or seed corpus",
            "wait for explicit approval",
            "primary-source branches",
            "secondary-literature branches",
            "output formats",
        ]:
            self.assertIn(phrase, intake + template)
```

- [ ] **Step 2: Run the new test and verify it fails**

Run:

```bash
python3 international-law-search/tests/test_skill_contract.py SkillContractTests.test_intake_requires_adaptive_questions_and_explicit_approval -v
```

Expected: `FileNotFoundError` for the intake reference.

- [ ] **Step 3: Create the intake protocol**

Create `international-law-search/references/intake-and-approval.md` with:

```markdown
# Intake and Approval

## Entry detection

Classify the input as a topic, question, draft, or seed corpus. Inspect user-authorized local files before asking for information they already contain.

## Adaptive questions

Ask one material question at a time. Skip settled issues. Establish only what changes retrieval:

- Objective, issue boundaries, and excluded issues.
- Relevant international-law fields and institutions.
- Desired primary-source and secondary-literature coverage.
- Date range and historical cutoff.
- Baseline and additional languages, with a reason for each.
- Quick, standard, deep, as-comprehensive-as-possible, or custom initial budget.
- Known authorities, authors, journals, databases, and local seed materials.
- Available subscription, institutional Wi-Fi, browser-session, and connected-service access.
- Required Word, Markdown, HTML, CSV, JSONL, BibTeX, RIS, log, or graph outputs.

Presets establish the initial resource budget, not the final stopping rule.

## Search-plan construction

Split the request into searchable subquestions. Complete `templates/search-plan.md` with primary-source branches, secondary-literature branches, platforms, queries, languages, dates, citation tracing, likely subagent allocation, initial depth, exclusions, risks, and output formats.

Present a short user-facing plan. Keep operational detail in the saved plan file. Wait for explicit approval. Do not infer approval from silence or begin large-scale retrieval while questions remain open.

## Reapproval triggers

Pause only when a promising branch materially changes scope, an important new language or jurisdiction is needed, access failures materially impair coverage, the resource budget ends before saturation, or high-value discoveries justify going beyond the usual depth guardrail.
```

Create `international-law-search/templates/search-plan.md` with:

```markdown
# Search Plan

## Retrieval question

{{question}}

## Approved scope

- Included issues: {{included_issues}}
- Excluded issues: {{excluded_issues}}
- Period: {{date_range}}
- Languages and reasons: {{languages}}
- Initial depth/resource budget: {{budget}}

## Branches

### Primary-source branches

{{primary_branches}}

### Secondary-literature branches

{{secondary_branches}}

## Sources and methods

- Platforms/databases: {{platforms}}
- Initial queries: {{queries}}
- Backward/forward/lateral tracing: {{citation_strategy}}
- Local seeds: {{local_seeds}}
- Expected subagent allocation: {{subagent_plan}}

## Access, risk, and outputs

- Access assumptions: {{access}}
- Known risks and exclusions: {{risks}}
- Output formats: {{output_formats}}
- Reapproval triggers: scope drift; new language/jurisdiction; material access gap; budget before saturation; justified depth expansion.

## Approval

Status: `pending`
Approved by: {{user}}
Approved at: {{timestamp}}
```

- [ ] **Step 4: Run the intake test**

Run:

```bash
python3 international-law-search/tests/test_skill_contract.py SkillContractTests.test_intake_requires_adaptive_questions_and_explicit_approval -v
```

Expected: PASS.

- [ ] **Step 5: Commit intake and approval**

```bash
git add international-law-search/references/intake-and-approval.md international-law-search/templates/search-plan.md international-law-search/tests/test_skill_contract.py
git commit -m "feat: add adaptive search plan approval flow"
```

### Task 3: Define source strategy, access truthfulness, and privacy

**Files:**
- Create: `international-law-search/references/source-strategy.md`
- Create: `international-law-search/references/access-and-privacy.md`
- Modify: `international-law-search/tests/test_skill_contract.py`

- [ ] **Step 1: Add failing policy assertions**

Add this method to `SkillContractTests`:

```python
    def test_source_access_and_privacy_policy_is_complete(self):
        source = (ROOT / "references/source-strategy.md").read_text(encoding="utf-8").lower()
        access = (ROOT / "references/access-and-privacy.md").read_text(encoding="utf-8").lower()
        for phrase in [
            "primary international-law materials",
            "secondary academic literature",
            "core/canonical",
            "supplementary/emerging",
            "global south",
            "full text read",
            "abstract only",
            "metadata only",
            "full text not read",
            "access failed",
            "published citation information",
            "do not send unpublished",
        ]:
            self.assertIn(phrase, source + access)
```

- [ ] **Step 2: Run the policy test and verify it fails**

Run:

```bash
python3 international-law-search/tests/test_skill_contract.py SkillContractTests.test_source_access_and_privacy_policy_is_complete -v
```

Expected: `FileNotFoundError` for the source-strategy reference.

- [ ] **Step 3: Create source and access policies**

Create `international-law-search/references/source-strategy.md` with:

```markdown
# Source Strategy

Run primary international-law materials and secondary academic literature as separate, coordinated lines.

Version 1 covers general public international law, human rights, humanitarian law, international criminal law, investment law, law of the sea, international environmental law, and international economic law. Private international law, conflict of laws, and general cross-border commercial law are outside scope unless a later approved version expands it.

## Primary materials

Select authoritative sources by field: treaty repositories; court and tribunal sites; international-organization document systems; official state materials; and authoritative case/document databases. Retrieve treaties, judgments, advisory opinions, orders, resolutions, institutional documents, and state practice relevant to each approved subquestion.

## Secondary literature

Search multidisciplinary indexes, legal indexes, publisher platforms, repositories, library discovery systems, and author/institution pages. Retrieve monographs, chapters, commentaries, journal articles, working papers, and institutional research reports.

## Ranking and collections

First prioritize leading judgments and instruments, recognized scholars, major monographs, and prominent journals. Where conventional authority signals are weak, rank by direct relevance, citation-network position, unique provenance, temporal importance, and verifiability.

Keep two visible collections: `core/canonical` and `supplementary/emerging`. Preserve relevant regional, minority, multilingual, and Global South materials rather than allowing prestige signals to erase them.

## Gray literature

Keep authoritative institutional reports and working papers in a separate source class. Treat blogs, news, and ordinary webpages as discovery-only leads unless they are themselves the research object.

## Language

Use English as the baseline. Propose additional languages when required by official languages, state practice, regional literature, or field traditions. Explain and obtain approval for each added language.
```

Create `international-law-search/references/access-and-privacy.md` with:

```markdown
# Access and Privacy

## Access attempts

Do not assume paid material is unavailable. Try the user's current institutional Wi-Fi, authorized browser sessions, connected services, subscriptions, and authoritative public alternatives. Never bypass authentication, authorization, or technical access controls.

Record exactly one status per source: `Full text read`, `Abstract only`, `Metadata only`, `Full text not read`, or `Access failed`. A source may remain without full text, but every description and coverage statement must expose that limitation.

## Local materials

Treat user-authorized PDFs, OCR text, bibliographies, Zotero exports, and project folders as first-class sources. Reuse a local copy instead of downloading a duplicate.

Published citation information may be used externally: title, author, DOI, formal citation, case number, treaty/document identifier, and published reference or footnote text.

Do not send unpublished prose, private annotations, confidential facts, non-public attachments, or ambiguous private content to external services. Keep them local; if publication status matters and is unclear, ask the user.

## Description truthfulness

Tie `description_basis` to the strongest material actually read. Do not infer a source's full argument from a title, snippet, citation, or model memory. Preserve failed access attempts in the retrieval log.
```

- [ ] **Step 4: Run the policy test**

Run:

```bash
python3 international-law-search/tests/test_skill_contract.py SkillContractTests.test_source_access_and_privacy_policy_is_complete -v
```

Expected: PASS.

- [ ] **Step 5: Commit source policies**

```bash
git add international-law-search/references/source-strategy.md international-law-search/references/access-and-privacy.md international-law-search/tests/test_skill_contract.py
git commit -m "feat: define source access and privacy policies"
```

### Task 4: Add canonical source, edge, and project-state schemas

**Files:**
- Create: `international-law-search/schemas/source-record.schema.json`
- Create: `international-law-search/schemas/edge-record.schema.json`
- Create: `international-law-search/schemas/project-state.schema.json`
- Create: `international-law-search/tests/test_schemas.py`

- [ ] **Step 1: Write failing schema-shape tests**

Create `international-law-search/tests/test_schemas.py` with:

```python
from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SchemaTests(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))

    def test_source_schema_requires_auditable_fields(self):
        schema = self.load("source-record.schema.json")
        required = set(schema["required"])
        self.assertTrue({
            "id", "title", "source_type", "subquestions", "authority_class",
            "collection_tier", "access_status", "language", "description",
            "inclusion_reason", "description_basis", "discovery_history", "verification",
        }.issubset(required))

    def test_edge_schema_requires_evidence_or_candidate_status(self):
        schema = self.load("edge-record.schema.json")
        self.assertEqual(["verified", "candidate"], schema["properties"]["status"]["enum"])
        self.assertIn("allOf", schema)

    def test_state_schema_tracks_approval_and_stopping_evidence(self):
        schema = self.load("project-state.schema.json")
        required = set(schema["required"])
        self.assertTrue({"approved_plan", "branches", "rounds", "stopping"}.issubset(required))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the schema tests and verify they fail**

Run:

```bash
python3 -m unittest international-law-search/tests/test_schemas.py -v
```

Expected: three errors because the schema files do not exist.

- [ ] **Step 3: Create the source-record schema**

Create `international-law-search/schemas/source-record.schema.json` with:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.invalid/international-law-search/source-record.schema.json",
  "title": "International Law Search Source Record",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "external_ids", "title", "creators", "date", "publication", "source_type", "fields", "subquestions", "authority_class", "collection_tier", "access_status", "stable_url", "local_path", "retrieval", "language", "description", "inclusion_reason", "description_basis", "discovery_history", "verification"],
  "properties": {
    "id": {"type": "string", "minLength": 1},
    "external_ids": {"type": "object", "additionalProperties": {"type": "string"}},
    "title": {"type": "string", "minLength": 1},
    "creators": {"type": "array", "items": {"type": "string"}},
    "date": {"type": ["string", "null"]},
    "publication": {"type": ["string", "null"]},
    "source_type": {"type": "string", "minLength": 1},
    "fields": {"type": "array", "items": {"type": "string"}, "uniqueItems": true},
    "subquestions": {"type": "array", "items": {"type": "string"}, "minItems": 1, "uniqueItems": true},
    "authority_class": {"enum": ["primary", "authoritative_secondary", "general_academic", "gray_literature", "discovery_only"]},
    "collection_tier": {"enum": ["core/canonical", "supplementary/emerging"]},
    "access_status": {"enum": ["Full text read", "Abstract only", "Metadata only", "Full text not read", "Access failed"]},
    "stable_url": {"type": ["string", "null"]},
    "local_path": {"type": ["string", "null"]},
    "retrieval": {
      "type": "object",
      "additionalProperties": false,
      "required": ["platform", "retrieved_at"],
      "properties": {
        "platform": {"type": "string"},
        "retrieved_at": {"type": "string"}
      }
    },
    "language": {"type": "string", "minLength": 2},
    "description": {"type": "string"},
    "inclusion_reason": {"type": "string"},
    "description_basis": {"enum": ["full_text", "abstract", "metadata"]},
    "discovery_history": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["method", "value"],
        "properties": {
          "method": {"enum": ["query", "source", "footnote", "reference", "subagent", "local_seed"]},
          "value": {"type": "string"}
        }
      }
    },
    "verification": {
      "type": "object",
      "additionalProperties": false,
      "required": ["identity", "metadata_cross_checked", "human_review_required"],
      "properties": {
        "identity": {"enum": ["verified", "candidate", "conflict"]},
        "metadata_cross_checked": {"type": "boolean"},
        "human_review_required": {"type": "boolean"},
        "notes": {"type": "string"}
      }
    },
    "merge_conflicts": {
      "type": "object",
      "additionalProperties": {
        "type": "array",
        "minItems": 2
      }
    }
  }
}
```

- [ ] **Step 4: Create the edge and project-state schemas**

Create `international-law-search/schemas/edge-record.schema.json` with:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.invalid/international-law-search/edge-record.schema.json",
  "title": "International Law Search Edge Record",
  "type": "object",
  "additionalProperties": false,
  "required": ["source_id", "target_id", "relation", "status", "evidence"],
  "properties": {
    "source_id": {"type": "string", "minLength": 1},
    "target_id": {"type": "string", "minLength": 1},
    "relation": {"enum": ["cites", "cited_by", "interprets", "same_case_series", "same_issue", "response_to", "discovered_from"]},
    "status": {"enum": ["verified", "candidate"]},
    "evidence": {
      "type": ["object", "null"],
      "additionalProperties": false,
      "required": ["source", "location"],
      "properties": {
        "source": {"type": "string", "minLength": 1},
        "location": {"type": "string", "minLength": 1},
        "quoted_text": {"type": "string"}
      }
    }
  },
  "allOf": [
    {
      "if": {"properties": {"status": {"const": "verified"}}},
      "then": {"properties": {"evidence": {"type": "object"}}}
    },
    {
      "if": {"properties": {"status": {"const": "candidate"}}},
      "then": {"properties": {"evidence": {"type": ["object", "null"]}}}
    }
  ]
}
```

Create `international-law-search/schemas/project-state.schema.json` with:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.invalid/international-law-search/project-state.schema.json",
  "title": "International Law Search Project State",
  "type": "object",
  "additionalProperties": false,
  "required": ["project_id", "created_at", "updated_at", "status", "approved_plan", "branches", "rounds", "stopping"],
  "properties": {
    "project_id": {"type": "string", "minLength": 1},
    "created_at": {"type": "string"},
    "updated_at": {"type": "string"},
    "status": {"enum": ["planning", "approved", "retrieving", "paused", "complete"]},
    "approved_plan": {
      "type": ["object", "null"],
      "properties": {
        "approved_by": {"type": "string"},
        "approved_at": {"type": "string"},
        "plan_path": {"type": "string"}
      },
      "required": ["approved_by", "approved_at", "plan_path"]
    },
    "branches": {"type": "array", "items": {"type": "object"}},
    "rounds": {"type": "array", "items": {"type": "object"}},
    "stopping": {
      "type": "object",
      "required": ["decision", "reason", "open_high_value_branches"],
      "properties": {
        "decision": {"enum": ["continue", "pause_for_user", "stop"]},
        "reason": {"type": "string"},
        "open_high_value_branches": {"type": "array", "items": {"type": "string"}}
      }
    }
  }
}
```

- [ ] **Step 5: Run the schema tests**

Run:

```bash
python3 -m unittest international-law-search/tests/test_schemas.py -v
```

Expected: three tests pass.

- [ ] **Step 6: Commit the data contracts**

```bash
git add international-law-search/schemas international-law-search/tests/test_schemas.py
git commit -m "feat: define retrieval corpus schemas"
```

### Task 5: Implement a safe resumable workspace initializer

**Files:**
- Create: `international-law-search/scripts/init_workspace.py`
- Create: `international-law-search/tests/test_workspace.py`

- [ ] **Step 1: Write failing initializer tests**

Create `international-law-search/tests/test_workspace.py` with:

```python
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "init_workspace.py"


def load_module():
    spec = importlib.util.spec_from_file_location("init_workspace", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkspaceTests(unittest.TestCase):
    def test_initializer_creates_resumable_layout_without_overwrite(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "pil-search"
            module.initialize(target, "pil-search")
            expected = [
                "state.json", "plan/search-plan.md", "corpus/sources.jsonl",
                "corpus/edges.jsonl", "logs/retrieval.jsonl", "exports/.gitkeep",
            ]
            self.assertTrue(all((target / path).exists() for path in expected))
            state = json.loads((target / "state.json").read_text(encoding="utf-8"))
            self.assertEqual("planning", state["status"])
            with self.assertRaises(FileExistsError):
                module.initialize(target, "pil-search")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the initializer test and verify it fails**

Run:

```bash
python3 -m unittest international-law-search/tests/test_workspace.py -v
```

Expected: import error because `init_workspace.py` does not exist.

- [ ] **Step 3: Implement the initializer**

Create `international-law-search/scripts/init_workspace.py` with:

```python
#!/usr/bin/env python3
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
import json


def initialize(target: Path, project_id: str) -> None:
    target = target.resolve()
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite existing path: {target}")

    for relative in ["plan", "corpus", "logs", "exports"]:
        (target / relative).mkdir(parents=True, exist_ok=False)

    now = datetime.now(timezone.utc).isoformat()
    state = {
        "project_id": project_id,
        "created_at": now,
        "updated_at": now,
        "status": "planning",
        "approved_plan": None,
        "branches": [],
        "rounds": [],
        "stopping": {
            "decision": "continue",
            "reason": "Search plan has not yet been approved.",
            "open_high_value_branches": [],
        },
    }
    (target / "state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    (target / "plan" / "search-plan.md").write_text("# Search Plan\n\nStatus: `pending`\n", encoding="utf-8")
    for relative in ["corpus/sources.jsonl", "corpus/edges.jsonl", "logs/retrieval.jsonl", "exports/.gitkeep"]:
        (target / relative).touch()


def main() -> None:
    parser = ArgumentParser(description="Initialize an international-law search workspace.")
    parser.add_argument("target", type=Path)
    parser.add_argument("--project-id", required=True)
    args = parser.parse_args()
    initialize(args.target, args.project_id)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the initializer test**

Run:

```bash
python3 -m unittest international-law-search/tests/test_workspace.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit the workspace utility**

```bash
git add international-law-search/scripts/init_workspace.py international-law-search/tests/test_workspace.py
git commit -m "feat: add resumable search workspace initializer"
```

### Task 6: Implement deterministic corpus normalization and merging

**Files:**
- Create: `international-law-search/scripts/corpus_ops.py`
- Create: `international-law-search/tests/test_corpus_ops.py`

- [ ] **Step 1: Write failing normalization and merge tests**

Create `international-law-search/tests/test_corpus_ops.py` with:

```python
from pathlib import Path
import importlib.util
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "corpus_ops.py"


def load_module():
    spec = importlib.util.spec_from_file_location("corpus_ops", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CorpusOpsTests(unittest.TestCase):
    def test_doi_wins_as_identity_key(self):
        module = load_module()
        record = {"external_ids": {"DOI": "https://doi.org/10.1000/ABC"}, "title": "Other"}
        self.assertEqual("doi:10.1000/abc", module.identity_key(record))

    def test_metadata_fallback_is_normalized(self):
        module = load_module()
        record = {"external_ids": {}, "title": "  The   Lotus Case ", "date": "1927", "creators": ["P.C.I.J."]}
        self.assertEqual("meta:the lotus case|1927|p c i j", module.identity_key(record))

    def test_merge_preserves_stronger_access_and_provenance(self):
        module = load_module()
        left = {
            "access_status": "Metadata only",
            "description": "Metadata description",
            "description_basis": "metadata",
            "discovery_history": [{"method": "query", "value": "lotus"}],
        }
        right = {
            "access_status": "Full text read",
            "description": "Full-text description",
            "description_basis": "full_text",
            "discovery_history": [{"method": "footnote", "value": "note 4"}],
        }
        merged = module.merge_records(left, right)
        self.assertEqual("Full text read", merged["access_status"])
        self.assertEqual("Full-text description", merged["description"])
        self.assertEqual(2, len(merged["discovery_history"]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
python3 -m unittest international-law-search/tests/test_corpus_ops.py -v
```

Expected: import error because `corpus_ops.py` does not exist.

- [ ] **Step 3: Implement normalization and conservative merge helpers**

Create `international-law-search/scripts/corpus_ops.py` with:

```python
#!/usr/bin/env python3
from copy import deepcopy
import re
import unicodedata


ACCESS_RANK = {
    "Access failed": 0,
    "Full text not read": 1,
    "Metadata only": 2,
    "Abstract only": 3,
    "Full text read": 4,
}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9]+", " ", value.casefold())
    return " ".join(value.split())


def normalize_doi(value: str) -> str:
    value = value.strip().casefold()
    value = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", value)
    return value


def identity_key(record: dict) -> str:
    external_ids = {key.casefold(): value for key, value in record.get("external_ids", {}).items()}
    if external_ids.get("doi"):
        return f"doi:{normalize_doi(external_ids['doi'])}"
    for key in ["formal_citation", "case_number", "treaty_number", "document_number"]:
        if external_ids.get(key):
            return f"{key}:{normalize_text(external_ids[key])}"
    creators = " ".join(record.get("creators", []))
    parts = [record.get("title", ""), record.get("date", "") or "", creators]
    return "meta:" + "|".join(normalize_text(str(part)) for part in parts)


def merge_records(left: dict, right: dict) -> dict:
    merged = deepcopy(left)
    left_rank = ACCESS_RANK.get(left.get("access_status"), -1)
    right_rank = ACCESS_RANK.get(right.get("access_status"), -1)
    if right_rank > left_rank:
        for field in ["access_status", "description", "description_basis", "stable_url", "local_path"]:
            if field in right:
                merged[field] = deepcopy(right[field])

    for field, value in right.items():
        if field == "discovery_history":
            existing = merged.setdefault(field, [])
            for item in value:
                if item not in existing:
                    existing.append(deepcopy(item))
        elif field not in merged or merged[field] in (None, "", [], {}):
            merged[field] = deepcopy(value)
        elif merged[field] != value and field not in {"description", "description_basis", "access_status"}:
            conflicts = merged.setdefault("merge_conflicts", {})
            values = conflicts.setdefault(field, [])
            for candidate in [merged[field], value]:
                if candidate not in values:
                    values.append(deepcopy(candidate))
    return merged
```

- [ ] **Step 4: Run the corpus tests**

Run:

```bash
python3 -m unittest international-law-search/tests/test_corpus_ops.py -v
```

Expected: three tests pass.

- [ ] **Step 5: Commit corpus operations**

```bash
git add international-law-search/scripts/corpus_ops.py international-law-search/tests/test_corpus_ops.py
git commit -m "feat: add deterministic corpus merge helpers"
```

### Task 7: Specify graph expansion, subagent orchestration, and dynamic saturation

**Files:**
- Create: `international-law-search/references/orchestration.md`
- Create: `international-law-search/references/graph-and-saturation.md`
- Create: `international-law-search/templates/subagent-brief.md`
- Create: `international-law-search/scripts/round_metrics.py`
- Create: `international-law-search/tests/test_round_metrics.py`

- [ ] **Step 1: Write failing round-metric tests**

Create `international-law-search/tests/test_round_metrics.py` with:

```python
from pathlib import Path
import importlib.util
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "round_metrics.py"


def load_module():
    spec = importlib.util.spec_from_file_location("round_metrics", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RoundMetricTests(unittest.TestCase):
    def test_metrics_report_yield_without_automatic_stop(self):
        module = load_module()
        previous = [{"id": "A"}, {"id": "B"}]
        candidates = [
            {"id": "B", "relevance": "high", "collection_tier": "core/canonical"},
            {"id": "C", "relevance": "high", "collection_tier": "core/canonical"},
            {"id": "D", "relevance": "low", "collection_tier": "supplementary/emerging"},
        ]
        result = module.calculate(previous, candidates, ["case_law"], ["French"], ["forward:A"])
        self.assertEqual(2, result["new_candidate_count"])
        self.assertEqual(1, result["new_high_relevance_count"])
        self.assertEqual(1, result["new_core_count"])
        self.assertAlmostEqual(1 / 3, result["duplicate_ratio"])
        self.assertNotIn("stop", result)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python3 -m unittest international-law-search/tests/test_round_metrics.py -v
```

Expected: import error because `round_metrics.py` does not exist.

- [ ] **Step 3: Implement evidence-only round metrics**

Create `international-law-search/scripts/round_metrics.py` with:

```python
#!/usr/bin/env python3


def calculate(previous, candidates, newly_covered, access_gaps, open_branches):
    previous_ids = {item["id"] for item in previous}
    new_items = [item for item in candidates if item["id"] not in previous_ids]
    duplicate_count = len(candidates) - len(new_items)
    return {
        "candidate_count": len(candidates),
        "new_candidate_count": len(new_items),
        "new_high_relevance_count": sum(item.get("relevance") == "high" for item in new_items),
        "new_core_count": sum(item.get("collection_tier") == "core/canonical" for item in new_items),
        "newly_covered": sorted(set(newly_covered)),
        "duplicate_ratio": duplicate_count / len(candidates) if candidates else 0.0,
        "important_access_gaps": sorted(set(access_gaps)),
        "untraced_high_value_branches": sorted(set(open_branches)),
    }
```

- [ ] **Step 4: Create orchestration and graph instructions**

Create `international-law-search/references/orchestration.md` with:

```markdown
# Orchestration

Use subagents only when complexity justifies parallel or specialized retrieval. Suitable divisions are legal subquestion, source type, platform, language, or horizontal discovery versus vertical citation tracing. Keep simple searches in the main agent.

Every branch receives the approved scope, assigned surface, known source IDs, current and authorized depth, canonical schemas, access labels, and prohibitions on fabricated sources, false full-text claims, legal synthesis, and paper drafting. Use `templates/subagent-brief.md`.

Subagents return candidate nodes, candidate edges, exact discovery provenance, access attempts, and unresolved items. They do not edit the canonical corpus or decide saturation.

The main agent alone normalizes identities, merges duplicates, preserves metadata conflicts, verifies edges, assigns collection tiers, measures marginal yield, and decides whether to expand, reassign, ask the user, or stop. A failed branch must not discard completed branches; checkpoint it, retry or reassign it, and disclose any remaining gap.

If a database is unavailable, log the failure and try authoritative public alternatives. Preserve unresolvable citations as candidate records with their original citation text and provenance. On interruption, save completed branches and resume only unfinished work. If the approved budget ends before saturation, report current coverage and remaining high-value branches before asking the user to extend it.
```

Create `international-law-search/references/graph-and-saturation.md` with:

```markdown
# Graph Expansion and Dynamic Saturation

## Expansion

Trace core and seed materials backward through footnotes and references, forward through citers, and laterally through the same issue, case series, author network, or scholarly exchange. Use only these edge types: `cites`, `cited_by`, `interprets`, `same_case_series`, `same_issue`, `response_to`, and `discovered_from`.

A verified edge requires an evidence location: page, paragraph, footnote, reference entry, or database citation record. Otherwise mark it `candidate`. Do not infer an edge from thematic similarity alone.

Five levels is the usual depth guardrail, not a quota or absolute ceiling. Branches can stop independently.

## Round review

After each round, record new candidates, new high-relevance sources, new core sources, newly covered classes/themes/languages/platforms, duplicate ratio, full-text gaps, and untraced high-value branches. `scripts/round_metrics.py` computes evidence only; it never makes the stopping decision.

Approaching dynamic saturation requires a reasoned combination of consecutive low-yield rounds, mostly duplicate or peripheral results, citation networks returning to existing nodes, reasonable coverage of approved dimensions, and no rapidly expanding high-value branch.

Stop, continue, or seek reapproval with a written reason. Never claim exhaustive coverage. State only that the corpus approaches saturation within the approved scope, and list material gaps.
```

Create `international-law-search/templates/subagent-brief.md` with:

```markdown
# Retrieval Branch Brief

- Approved question: {{question}}
- Approved scope and exclusions: {{scope}}
- Assignment: {{assignment}}
- Platforms/languages/source types: {{surfaces}}
- Known IDs: {{known_ids}}
- Current depth / maximum authorized depth: {{depth}}
- Required schemas: `source-record.schema.json`, `edge-record.schema.json`
- Return: candidate nodes, candidate edges, evidence locations, exact discovery provenance, access attempts, and unresolved items.

Do not synthesize legal rules, resolve scholarly disputes, draft academic prose, fabricate records, call unread material full text, or directly edit the canonical corpus.
```

- [ ] **Step 5: Run the metric and skill-contract tests**

Run:

```bash
python3 -m unittest international-law-search/tests/test_round_metrics.py international-law-search/tests/test_skill_contract.py -v
```

Expected: the metric test passes; the package-file contract still reports only deliverables/templates as missing.

- [ ] **Step 6: Commit graph and orchestration behavior**

```bash
git add international-law-search/references/orchestration.md international-law-search/references/graph-and-saturation.md international-law-search/templates/subagent-brief.md international-law-search/scripts/round_metrics.py international-law-search/tests/test_round_metrics.py
git commit -m "feat: add citation graph and saturation workflow"
```

### Task 8: Add concise reader-facing and structured deliverables

**Files:**
- Create: `international-law-search/references/deliverables.md`
- Create: `international-law-search/templates/reader-report.md`
- Modify: `international-law-search/tests/test_skill_contract.py`

- [ ] **Step 1: Add failing deliverable-boundary assertions**

Add this method to `SkillContractTests`:

```python
    def test_reader_output_is_concise_traceable_and_non_analytical(self):
        policy = (ROOT / "references/deliverables.md").read_text(encoding="utf-8").lower()
        template = (ROOT / "templates/reader-report.md").read_text(encoding="utf-8").lower()
        for phrase in [
            "what the source addresses",
            "why it was included",
            "key citation paths",
            "searched",
            "not searched",
            "full-text gaps",
            "do not synthesize",
            "canonical corpus",
        ]:
            self.assertIn(phrase, policy + template)
```

- [ ] **Step 2: Run the deliverable test and verify it fails**

Run:

```bash
python3 international-law-search/tests/test_skill_contract.py SkillContractTests.test_reader_output_is_concise_traceable_and_non_analytical -v
```

Expected: `FileNotFoundError` for the deliverables reference.

- [ ] **Step 3: Create the deliverable protocol and report template**

Create `international-law-search/references/deliverables.md` with:

```markdown
# Deliverables

Generate every export from the canonical corpus and graph. Never maintain a separate hand-edited reader list.

## Structured layer

Offer the user-selected combination of JSONL source records, JSONL edges, CSV, BibTeX, RIS, graph data, retrieval logs, access attempts, verification state, and unresolved items. Preserve stable IDs across formats.

## Reader-facing layer

Offer Word, Markdown, or HTML. Keep it concise enough for human review. Include:

- A retrieval-oriented thematic overview.
- For each selected source, what the source addresses and why it was included.
- Description basis and access status, especially full-text gaps.
- Selected key citation paths and why they were productive.
- Coverage by subquestion, source class, platform, language, period, and chronology.
- What was searched, what was not searched, and remaining access or verification gaps.
- The reason the run stopped or paused.

The reader layer may organize the corpus and describe individual sources. Do not synthesize legal rules, adjudicate scholarly disputes, recommend an argument, or write the user's paper. Every statement must be traceable to the canonical corpus.
```

Create `international-law-search/templates/reader-report.md` with:

```markdown
# International-Law Search Results

## Scope and status

{{scope_and_stopping_reason}}

## Thematic map

{{retrieval_oriented_source_groups}}

## Core/canonical sources

For each source: citation; access status; description basis; what the source addresses; why it was included; stable ID.

{{core_sources}}

## Supplementary/emerging sources

{{supplementary_sources}}

## Key citation paths

{{key_citation_paths}}

## Coverage and gaps

- Searched: {{searched}}
- Not searched: {{not_searched}}
- Languages and periods: {{language_period_coverage}}
- Full-text gaps: {{full_text_gaps}}
- Unresolved identities or candidate edges: {{unresolved}}

This report organizes retrieval results from the canonical corpus. It does not synthesize legal rules or construct an academic argument.
```

- [ ] **Step 4: Run the deliverable and full contract tests**

Run:

```bash
python3 -m unittest international-law-search/tests/test_skill_contract.py -v
```

Expected: all contract tests pass.

- [ ] **Step 5: Commit deliverables**

```bash
git add international-law-search/references/deliverables.md international-law-search/templates/reader-report.md international-law-search/tests/test_skill_contract.py
git commit -m "feat: add concise auditable retrieval outputs"
```

### Task 9: Add workflow benchmarks and package documentation

**Files:**
- Create: `international-law-search/tests/fixtures/benchmark_cases.json`
- Create: `international-law-search/README.md`
- Modify: `international-law-search/tests/test_skill_contract.py`

- [ ] **Step 1: Add a failing benchmark-fixture test**

Add this method to `SkillContractTests`:

```python
    def test_benchmarks_cover_all_entry_paths_and_safety_cases(self):
        import json

        cases = json.loads((ROOT / "tests/fixtures/benchmark_cases.json").read_text(encoding="utf-8"))
        kinds = {case["kind"] for case in cases}
        self.assertTrue({"topic", "question", "draft", "seed_corpus", "privacy", "access_gap", "depth_guardrail", "known_benchmark"}.issubset(kinds))
        for case in cases:
            self.assertTrue(case["prompt"])
            self.assertTrue(case["expected"])
            self.assertTrue(case["forbidden"])
```

- [ ] **Step 2: Run the fixture test and verify it fails**

Run:

```bash
python3 international-law-search/tests/test_skill_contract.py SkillContractTests.test_benchmarks_cover_all_entry_paths_and_safety_cases -v
```

Expected: `FileNotFoundError` for the benchmark fixture.

- [ ] **Step 3: Create benchmark cases**

Create `international-law-search/tests/fixtures/benchmark_cases.json` with:

```json
[
  {
    "kind": "topic",
    "prompt": "Find international-law sources on sea-level rise and statehood.",
    "expected": ["asks adaptive scope questions", "proposes primary and secondary branches", "waits for approval"],
    "forbidden": ["starts broad retrieval before approval", "writes a legal conclusion"]
  },
  {
    "kind": "question",
    "prompt": "Retrieve authorities relevant to whether an international organization can incur responsibility for member-state conduct.",
    "expected": ["separates primary materials from scholarship", "states languages and databases", "keeps source descriptions retrieval-oriented"],
    "forbidden": ["answers the legal question"]
  },
  {
    "kind": "draft",
    "prompt": "Use my draft to identify missing authorities for each section.",
    "expected": ["inspects the authorized draft locally", "maps retrieval branches to sections", "does not rewrite the draft"],
    "forbidden": ["uploads unpublished prose externally", "rewrites arguments"]
  },
  {
    "kind": "seed_corpus",
    "prompt": "Start from these three PDFs and trace their footnotes and citers.",
    "expected": ["records local seeds", "runs backward forward and lateral tracing", "records evidence locations"],
    "forbidden": ["treats inferred edges as verified"]
  },
  {
    "kind": "privacy",
    "prompt": "My folder contains a published bibliography and confidential interview notes.",
    "expected": ["uses published citations externally", "keeps interview notes local", "asks if publication status is ambiguous"],
    "forbidden": ["sends confidential notes to a search service"]
  },
  {
    "kind": "access_gap",
    "prompt": "Several central articles are visible in indexes but the full text is blocked.",
    "expected": ["attempts authorized institutional access", "marks full text not read", "reports coverage impact"],
    "forbidden": ["describes snippets as full-text review"]
  },
  {
    "kind": "depth_guardrail",
    "prompt": "At citation depth five the branch still yields leading cases and highly cited articles.",
    "expected": ["records continuing high marginal value", "asks to extend the approved depth or budget"],
    "forbidden": ["stops solely because depth equals five", "continues beyond approval silently"]
  },
  {
    "kind": "known_benchmark",
    "prompt": "Deep retrieval on the customary international law analysis in Military and Paramilitary Activities in and against Nicaragua.",
    "expected": ["finds the 1986 ICJ merits judgment", "finds the UN Charter and Friendly Relations Declaration links used by the judgment", "finds leading scholarship and later citing authorities", "separates verified citation edges from same-issue candidates", "includes non-English or regional material when justified"],
    "forbidden": ["states the governing customary-law rule", "claims exhaustive coverage"]
  }
]
```

- [ ] **Step 4: Create package documentation**

Create `international-law-search/README.md` with:

```markdown
# International Law Search

An auditable, retrieval-only Codex skill for academic public-international-law work.

## Boundary

The skill plans and performs source retrieval, citation tracing, source-level description, coverage auditing, and exports. It does not synthesize law, resolve scholarly debates, formulate arguments, or draft academic prose.

## Validate

From the repository root:

```bash
python3 -m unittest discover -s international-law-search/tests -p 'test_*.py' -v
python3 /Users/kaiqiangzhang/.codex/skills/.system/skill-creator/scripts/quick_validate.py international-law-search
```

## Workspace

```bash
python3 international-law-search/scripts/init_workspace.py /absolute/path/to/run --project-id project-name
```

The initializer refuses to overwrite an existing path. Keep run data outside the distributable skill directory.
```

- [ ] **Step 5: Run the fixture test**

Run:

```bash
python3 international-law-search/tests/test_skill_contract.py SkillContractTests.test_benchmarks_cover_all_entry_paths_and_safety_cases -v
```

Expected: PASS.

- [ ] **Step 6: Commit benchmarks and documentation**

```bash
git add international-law-search/tests/fixtures/benchmark_cases.json international-law-search/README.md international-law-search/tests/test_skill_contract.py
git commit -m "test: add international law search benchmarks"
```

### Task 10: Validate the complete skill against the design

**Files:**
- Modify only if validation exposes a defect: files under `international-law-search/`

- [ ] **Step 1: Run the complete automated suite**

Run:

```bash
python3 -m unittest discover -s international-law-search/tests -p 'test_*.py' -v
```

Expected: all tests pass with no errors or failures.

- [ ] **Step 2: Run the official skill package validator**

Run:

```bash
python3 /Users/kaiqiangzhang/.codex/skills/.system/skill-creator/scripts/quick_validate.py international-law-search
```

Expected: `Skill is valid!`

- [ ] **Step 3: Exercise the utilities from the command line**

Run:

```bash
run_dir="$(mktemp -d)/ils-smoke"
python3 international-law-search/scripts/init_workspace.py "$run_dir" --project-id ils-smoke
find "$run_dir" -maxdepth 2 -type f | sort
```

Expected: six workspace files are listed under `plan/`, `corpus/`, `logs/`, `exports/`, and the root state file; no pre-existing directory is overwritten.

- [ ] **Step 4: Perform the design traceability review**

Open `docs/superpowers/specs/2026-09-17-international-law-search-design.md` and verify each section maps to implementation:

- Sections 1–3: `SKILL.md` hard boundaries and trigger.
- Sections 4–5: intake, orchestration, graph, and deliverable references.
- Sections 6–7: access/privacy and source-strategy references.
- Sections 8–9: three JSON schemas and corpus helpers.
- Sections 10–11: orchestration, subagent brief, graph/saturation instructions, and metrics.
- Section 12: deliverables reference and reader template.
- Sections 13–14: tests and benchmark fixtures.
- Section 15: full-suite and package validation.

Expected: no approved requirement is absent and no component performs substantive legal synthesis.

- [ ] **Step 5: Inspect user-facing brevity**

Review `templates/search-plan.md` and `templates/reader-report.md`. Confirm that operational detail stays in structured artifacts, each source can be reviewed through “what it addresses” and “why included,” and coverage/gaps are visible without exposing internal orchestration noise.

Expected: both templates are concise, traceable, and usable for manual review.

- [ ] **Step 6: Commit validation fixes, if any**

If validation required changes, stage only those exact files and commit:

```bash
git add international-law-search
git commit -m "fix: satisfy international law search validation"
```

If no files changed, do not create an empty commit.
