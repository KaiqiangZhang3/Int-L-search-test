# International Law Search v3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the skill into a backward-compatible research system with deterministic source upsert, claim and round ledgers, repeatable main rounds, writing-time side rounds, versioned synthesis, and consistent Markdown, HTML, and CSV outputs.

**Architecture:** Keep the source ledger as the source-identity layer, add independent claim and round ledgers, and validate one shared round bundle before rendering. Public Python scripts own deterministic mutations; skill instructions own user interaction and approval boundaries.

**Tech Stack:** Python 3 standard library, JSON Schema Draft 2020-12, JSONL, Markdown, static HTML/CSS, CSV, and `unittest`.

---

## File map

New schemas: `readiness-matrix.schema.json`, `claim-record.schema.json`, `round-record.schema.json`, and `round-bundle.schema.json`.

New scripts: `ledger_ops.py`, `validate_source_ledger.py`, `validate_claim_ledger.py`, `round_ops.py`, `validate_round_bundle.py`, `render_research_outputs.py`, and `migrate_v2_workspace.py`.

New references: `readiness-and-scale.md`, `research-rounds.md`, and `knowledge-and-synthesis.md`.

New templates: `round-spec.md`, `round-report.md`, `side-round-report.md`, and `next-round-menu.md`.

The implementation also updates `SKILL.md`, the source and project schemas, workspace initialization, reader validation, delivery guidance, orchestration, privacy/access guidance, multilingual guidance, handoff and subagent templates, fixtures, and regression tests.

All test snippets below are methods inside the named `unittest.TestCase` class. Tests that need a filesystem use this setup in that class:

```python
def setUp(self):
    self._temporary_directory = tempfile.TemporaryDirectory()
    self.tmp_path = Path(self._temporary_directory.name)

def tearDown(self):
    self._temporary_directory.cleanup()
```

### Task 1: Lock the v3 behavior contract

**Files:**
- Create: `international-law-search/tests/test_v3_contract.py`
- Modify: `international-law-search/tests/test_skill_contract.py`
- Modify: `international-law-search/tests/test_modes_and_rounds.py`

- [ ] **Step 1: Write the failing contract test**

```python
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class V3ContractTests(unittest.TestCase):
    def test_repeatable_rounds_replace_fixed_stage_progression(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        rounds = (ROOT / "references/research-rounds.md").read_text(encoding="utf-8")
        self.assertIn("repeatable main rounds", skill.lower())
        self.assertIn("side round", skill.lower())
        self.assertNotIn("Stage 2 cannot begin", skill)
        for value in ("breadth_expansion", "primary_materials", "state_practice", "verification"):
            self.assertIn(value, rounds)

    def test_three_budget_axes_and_cumulative_outputs_are_required(self):
        rounds = (ROOT / "references/research-rounds.md").read_text(encoding="utf-8")
        delivery = (ROOT / "references/deliverables.md").read_text(encoding="utf-8")
        for value in ("bibliographic_discovery", "full_text_acquisition", "substantive_review"):
            self.assertIn(value, rounds)
        for value in ("immutable round report", "living synthesis", "bibliography.csv", "index.html"):
            self.assertIn(value, delivery.lower())
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest international-law-search/tests/test_v3_contract.py -v`.

Expected: FAIL because `research-rounds.md` does not exist and the entrypoint still uses fixed stage gates.

- [ ] **Step 3: Replace legacy fixed-stage assertions with behavior assertions**

Keep approval, privacy, review-evidence, seed authorization, and stopping assertions. Replace only assumptions that breadth must be followed by depth.

- [ ] **Step 4: Commit the failing contract**

```bash
git add international-law-search/tests/test_v3_contract.py international-law-search/tests/test_skill_contract.py international-law-search/tests/test_modes_and_rounds.py
git commit -m "test: define v3 research workflow contract"
```

### Task 2: Add deterministic source-ledger upsert

**Files:**
- Create: `international-law-search/scripts/ledger_ops.py`
- Create: `international-law-search/scripts/validate_source_ledger.py`
- Create: `international-law-search/tests/test_ledger_ops_v3.py`
- Modify: `international-law-search/schemas/source-ledger-record.schema.json`
- Modify: `international-law-search/references/source-ledger.md`

- [ ] **Step 1: Write one failing upsert test**

```python
def test_upsert_merges_equivalent_doi_records_and_preserves_provenance(self):
    ledger = self.tmp_path / "sources.jsonl"
    first = source_record("SRC-001", title="Example Title", doi="10.1000/ABC")
    second = source_record("TEMP-9", title="EXAMPLE TITLE", doi="https://doi.org/10.1000/abc")
    second["discovery_provenance"] = [provenance("reference", "Seed A, note 14")]
    upsert_source(ledger, first)
    result = upsert_source(ledger, second)
    rows = read_jsonl(ledger)
    assert result == {"action": "merged", "source_key": "SRC-001"}
    assert len(rows) == 1
    assert len(rows[0]["discovery_provenance"]) == 2
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest international-law-search/tests/test_ledger_ops_v3.py -v`.

Expected: FAIL with an import error for `ledger_ops`.

- [ ] **Step 3: Implement the public upsert interface**

```python
def normalized_identity_keys(record: dict) -> list[str]:
    """Return strongest-first, type-aware normalized identity keys."""

def upsert_source(path: Path, incoming: dict) -> dict:
    """Atomically insert or merge one record and return action plus stable key."""
```

Normalize DOI prefixes and case; namespace official document, case, and treaty numbers; combine ISBN with edition; use normalized title, creators, date, and source type only as a conservative fallback. Write through a sibling temporary file followed by `Path.replace()`.

- [ ] **Step 4: Add idempotency and ambiguity tests**

```python
def test_repeated_upsert_is_idempotent(self):
    ledger = self.tmp_path / "sources.jsonl"
    record = source_record("SRC-001", title="Example", doi="10.1000/example")
    upsert_source(ledger, record)
    upsert_source(ledger, record)
    assert read_jsonl(ledger) == [record]

def test_ambiguous_metadata_does_not_silently_merge(self):
    ledger = self.tmp_path / "sources.jsonl"
    upsert_source(ledger, source_record("SRC-001", title="Common Title", creator="Author A"))
    result = upsert_source(ledger, source_record("SRC-002", title="Common Title", creator="Author B"))
    assert result["action"] == "inserted"
```

- [ ] **Step 5: Extend the source schema**

Add `scholarly_importance` with `level` and `reason`, `acquisition_priority`, typed `acquisition_routes`, and `round_membership`. Use closed enums. Add ISBN and library identifiers without weakening existing type-specific metadata.

- [ ] **Step 6: Implement Standard-ledger validation**

`validate_source_ledger.py PATH` validates every row, rejects duplicate `source_key` values, duplicate strong identities, unsupported description evidence, and externalizable local paths. Exit codes are `0` valid, `1` invalid content, and `2` unreadable input.

- [ ] **Step 7: Verify GREEN and commit**

```bash
python3 -m unittest international-law-search/tests/test_ledger_ops_v3.py international-law-search/tests/test_source_ledger.py international-law-search/tests/test_corpus_ops.py -v
git add international-law-search/scripts/ledger_ops.py international-law-search/scripts/validate_source_ledger.py international-law-search/schemas/source-ledger-record.schema.json international-law-search/references/source-ledger.md international-law-search/tests/test_ledger_ops_v3.py
git commit -m "feat: add deterministic source ledger upsert"
```

Expected: PASS.

### Task 3: Add the claim ledger

**Files:**
- Create: `international-law-search/schemas/claim-record.schema.json`
- Create: `international-law-search/scripts/validate_claim_ledger.py`
- Create: `international-law-search/tests/test_claim_ledger.py`
- Create: `international-law-search/references/knowledge-and-synthesis.md`

- [ ] **Step 1: Write the failing evidence test**

```python
def test_supported_claim_requires_reviewed_evidence_and_locator(self):
    write_jsonl(self.tmp_path / "sources.jsonl", [source_record("SRC-1", review_extent="metadata_verified")])
    write_jsonl(self.tmp_path / "claims.jsonl", [claim_record("CLM-1", status="supported", source_key="SRC-1", locator=None)])
    errors = validate_claim_ledger(self.tmp_path / "claims.jsonl", self.tmp_path / "sources.jsonl")
    assert any("reviewed evidence" in error for error in errors)
    assert any("locator" in error for error in errors)
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest international-law-search/tests/test_claim_ledger.py -v`.

- [ ] **Step 3: Define the claim record**

Require `claim_id`, `claim_text`, `claim_type`, `scope`, status, first and last round, supporting and contrary evidence, predecessor and successor IDs, and reader qualification. Status is one of `provisional`, `supported`, `contested`, `revised`, or `superseded`. Evidence stores `source_key`, exact locator, evidence function, and review basis.

- [ ] **Step 4: Implement cross-ledger validation**

```python
def validate_claim_ledger(claim_path: Path, source_path: Path) -> list[str]:
    """Return deterministic evidence and revision errors without mutation."""
```

Verify unique IDs, resolvable sources, locators, sufficient review extent, reciprocal revision links, and absence of revision cycles. `supported` requires supporting evidence; `contested` requires both supporting and contrary evidence.

- [ ] **Step 5: Add a revision-lifecycle test**

```python
def test_revised_claim_links_to_current_successor(self):
    claims = [
        claim_record("CLM-1", status="revised", successor="CLM-2"),
        claim_record("CLM-2", status="supported", predecessor="CLM-1"),
    ]
    assert validate_records(claims, [reviewed_source("SRC-1")]) == []
    assert current_claim_ids(claims) == {"CLM-2"}
```

- [ ] **Step 6: Verify GREEN and commit**

```bash
python3 -m unittest international-law-search/tests/test_claim_ledger.py -v
git add international-law-search/schemas/claim-record.schema.json international-law-search/scripts/validate_claim_ledger.py international-law-search/tests/test_claim_ledger.py international-law-search/references/knowledge-and-synthesis.md
git commit -m "feat: add evidence-backed claim ledger"
```

### Task 4: Implement repeatable main rounds and side rounds

**Files:**
- Create: `international-law-search/schemas/round-record.schema.json`
- Create: `international-law-search/schemas/readiness-matrix.schema.json`
- Create: `international-law-search/scripts/round_ops.py`
- Create: `international-law-search/tests/test_round_ops.py`
- Create: `international-law-search/references/readiness-and-scale.md`
- Create: `international-law-search/references/research-rounds.md`
- Modify: `international-law-search/templates/scope-card.md`

- [ ] **Step 1: Write failing allocation tests**

```python
def test_breadth_may_be_followed_by_breadth_expansion(self):
    result = allocate_round([round_record("R1", "breadth")], kind="main", round_type="breadth_expansion")
    assert (result["round_id"], result["round_type"]) == ("R2", "breadth_expansion")

def test_side_round_does_not_advance_main_counter(self):
    records = [round_record("R1", "breadth")]
    side = allocate_round(records, kind="side", round_type="verification", parent_round_id="R1")
    main = allocate_round(records + [side], kind="main", round_type="depth")
    assert side["round_id"] == "R1.S1"
    assert main["round_id"] == "R2"
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest international-law-search/tests/test_round_ops.py -v`.

- [ ] **Step 3: Define the round and budget schemas**

Round types are `breadth`, `breadth_expansion`, `depth`, `primary_materials`, `state_practice`, `doctrinal`, `gap_filling`, `verification`, and `synthesis`. Planned and actual budgets separately record `bibliographic_discovery`, `full_text_acquisition`, and `substantive_review`, plus named platforms and purposes, query and time caps, depth, seeds, and language allocations.

- [ ] **Step 4: Implement allocation and atomic append**

```python
def allocate_round(records: list[dict], *, kind: str, round_type: str, parent_round_id: str | None = None) -> dict:
    """Allocate the next main or parent-scoped side-round ID."""

def append_round(path: Path, record: dict) -> None:
    """Validate and atomically append one non-duplicate round."""
```

Reject missing parents, duplicate IDs, main-round gaps, side-round parents that are side rounds, and actual use above authorized caps without an extension decision.

- [ ] **Step 5: Implement the readiness contract**

Each readiness topic is `known`, `default_accepted`, `deferred`, or `not_applicable`, with evidence from the user or existing context. The reference requires one material question at a time, skips answered questions, and stops once the next round is designable. Include Orientation, Seminar paper, Thesis chapter, and Doctoral corpus profiles as expectations rather than quotas.

- [ ] **Step 6: Verify GREEN and commit**

```bash
python3 -m unittest international-law-search/tests/test_round_ops.py -v
git add international-law-search/schemas/round-record.schema.json international-law-search/schemas/readiness-matrix.schema.json international-law-search/scripts/round_ops.py international-law-search/tests/test_round_ops.py international-law-search/references/readiness-and-scale.md international-law-search/references/research-rounds.md international-law-search/templates/scope-card.md
git commit -m "feat: support repeatable and side research rounds"
```

### Task 5: Upgrade workspace initialization and migration

**Files:**
- Modify: `international-law-search/scripts/init_workspace.py`
- Modify: `international-law-search/schemas/project-state.schema.json`
- Create: `international-law-search/scripts/migrate_v2_workspace.py`
- Create: `international-law-search/tests/test_migrate_v2_workspace.py`
- Create: `international-law-search/tests/fixtures/v3/v2-workspace/`
- Modify: `international-law-search/templates/session-handoff.md`

- [ ] **Step 1: Write the failing layout test**

```python
def test_v3_workspace_contains_all_research_layers(self):
    target = self.tmp_path / "project"
    initialize(target, "project-1")
    expected = {
        "knowledge/sources.jsonl", "knowledge/claims.jsonl", "knowledge/rounds.jsonl",
        "knowledge/decisions.jsonl", "knowledge/terminology.jsonl", "reports",
        "synthesis", "presentations", "exports/bibliography.csv", "logs", "state.json",
    }
    assert expected.issubset(relative_paths(target))
    assert read_json(target / "state.json")["schema_version"] == 3
```

- [ ] **Step 2: Verify RED, then update initialization and state**

Run `python3 -m unittest international-law-search/tests/test_workspace.py -v` and confirm the v2 layout fails. Create the v3 layout atomically. Keep round facts in `knowledge/rounds.jsonl`; `state.json` stores project status, current checkpoint, artifact pointers, optional graph flags, coverage, and deduplication state.

- [ ] **Step 3: Write the failing migration test**

```python
def test_v2_migration_preserves_identity_decisions_provenance_and_review(self):
    source = copy_fixture("v2-workspace", self.tmp_path / "v2")
    target = self.tmp_path / "v3"
    migrate(source, target)
    assert source_keys(target) == source_keys(source)
    assert review_extents(target) == review_extents(source)
    assert decisions(target) == decisions(source)
    assert provenance(target) == provenance(source)
```

- [ ] **Step 4: Implement additive migration**

```python
def migrate(source: Path, target: Path) -> None:
    """Create a validated v3 copy without changing the v2 source."""
```

Convert legacy stages to main rounds, preserve sources, decisions, graph and logs, initialize empty claim and terminology ledgers without invention, register legacy reports, mark unknown historic acquisition counts explicitly, and refuse overwrite or remigration.

- [ ] **Step 5: Verify GREEN and commit**

```bash
python3 -m unittest international-law-search/tests/test_workspace.py international-law-search/tests/test_migrate_v1_workspace.py international-law-search/tests/test_migrate_v2_workspace.py -v
git add international-law-search/scripts/init_workspace.py international-law-search/schemas/project-state.schema.json international-law-search/scripts/migrate_v2_workspace.py international-law-search/tests/test_workspace.py international-law-search/tests/test_migrate_v2_workspace.py international-law-search/tests/fixtures/v3/v2-workspace international-law-search/templates/session-handoff.md
git commit -m "feat: initialize and migrate v3 research workspaces"
```

### Task 6: Add immutable round reports and next-round menus

**Files:**
- Create: `international-law-search/templates/round-spec.md`
- Create: `international-law-search/templates/round-report.md`
- Create: `international-law-search/templates/side-round-report.md`
- Create: `international-law-search/templates/next-round-menu.md`
- Create: `international-law-search/tests/test_round_templates_v3.py`
- Modify: `international-law-search/templates/decision-panel.md`
- Modify: `international-law-search/templates/breadth-checkpoint.md`
- Modify: `international-law-search/templates/depth-checkpoint.md`

- [ ] **Step 1: Write failing structure tests**

```python
def test_round_report_saves_complete_next_round_designs(self):
    report = template("round-report.md")
    menu = template("next-round-menu.md")
    for field in ("Round purpose", "Knowledge changes", "Planned and actual budget", "Next-round menu"):
        assert field in report
    for field in ("Question addressed", "Retrieval objects", "Starting seeds", "Method", "Three-axis budget", "Expected output", "Exclusions"):
        assert field in menu
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest international-law-search/tests/test_round_templates_v3.py -v`.

- [ ] **Step 3: Implement positive output contracts**

The main report shows research findings before audit details. The side report begins with `supported`, `partially_supported`, `unsupported`, or `counterevidence_found`, followed by a safer formulation, two to five sources, exact locators, evidentiary functions, limits, and citations. Both reports save complete next-round designs. Legacy breadth and depth templates become compatibility routers without fixed progression.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest international-law-search/tests/test_round_templates_v3.py international-law-search/tests/test_reader_report.py -v
git add international-law-search/templates international-law-search/tests/test_round_templates_v3.py
git commit -m "feat: add immutable round reporting contracts"
```

### Task 7: Validate one shared round bundle

**Files:**
- Create: `international-law-search/schemas/round-bundle.schema.json`
- Create: `international-law-search/scripts/validate_round_bundle.py`
- Create: `international-law-search/tests/test_round_bundle.py`
- Modify: `international-law-search/scripts/validate_reader_report.py`

- [ ] **Step 1: Write the failing cross-reference test**

```python
def test_bundle_rejects_unknown_source_and_claim_references(self):
    bundle = valid_bundle()
    bundle["featured_source_keys"].append("SRC-MISSING")
    bundle["claim_ids"].append("CLM-MISSING")
    errors = validate_bundle(bundle, sources=[reviewed_source("SRC-1")], claims=[supported_claim("CLM-1")], rounds=[round_record("R1", "breadth")])
    assert any("SRC-MISSING" in error for error in errors)
    assert any("CLM-MISSING" in error for error in errors)
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest international-law-search/tests/test_round_bundle.py -v`.

- [ ] **Step 3: Define and implement bundle validation**

The schema requires checkpoint ID, round ID, generation time, reader language, research question, narrative sections, featured sources, claims, budget summary, gaps, next-round options, bibliography selection, privacy classification, and `externalizable: true`.

```python
def validate_bundle(bundle: dict, *, sources: list[dict], claims: list[dict], rounds: list[dict]) -> list[str]:
    """Return schema, reference, evidence, privacy, and checkpoint errors."""
```

Verify all references, current claim status, evidence sufficiency, budget match, option completeness, and absence of private paths.

- [ ] **Step 4: Make reader validation bundle-aware**

Support `--bundle`, `--sources`, `--claims`, and `--rounds` while preserving legacy standalone validation.

- [ ] **Step 5: Verify GREEN and commit**

```bash
python3 -m unittest international-law-search/tests/test_round_bundle.py international-law-search/tests/test_reader_report.py -v
git add international-law-search/schemas/round-bundle.schema.json international-law-search/scripts/validate_round_bundle.py international-law-search/scripts/validate_reader_report.py international-law-search/tests/test_round_bundle.py
git commit -m "feat: validate shared research output bundles"
```

### Task 8: Render Markdown, HTML, synthesis, and CSV consistently

**Files:**
- Create: `international-law-search/scripts/render_research_outputs.py`
- Create: `international-law-search/tests/test_render_outputs.py`
- Modify: `international-law-search/references/deliverables.md`
- Modify: `international-law-search/templates/reader-report.md`

- [ ] **Step 1: Write the failing consistency test**

```python
def test_one_bundle_renders_matching_source_sets(self):
    outputs = render_outputs(bundle_path=fixture("round-bundle.json"), source_path=fixture("sources.jsonl"), claim_path=fixture("claims.jsonl"), round_path=fixture("rounds.jsonl"), output_root=self.tmp_path)
    expected = {"SRC-1", "SRC-2"}
    assert source_keys_in_markdown(outputs.round_markdown) == expected
    assert source_keys_in_html(outputs.round_html) == expected
    assert source_keys_in_csv(outputs.bibliography_csv) == expected
```

- [ ] **Step 2: Verify RED**

Run `python3 -m unittest international-law-search/tests/test_render_outputs.py -v`.

- [ ] **Step 3: Implement failure-atomic rendering**

```python
@dataclass(frozen=True)
class RenderedOutputs:
    round_markdown: Path
    round_html: Path
    bibliography_csv: Path
    synthesis_markdown: Path | None
    project_index_html: Path

def render_outputs(*, bundle_path: Path, source_path: Path, claim_path: Path, round_path: Path, output_root: Path) -> RenderedOutputs:
    """Validate one checkpoint and atomically publish reader outputs."""
```

Render in a sibling temporary directory, validate links and checkpoint metadata, preserve old round reports, then atomically replace `current-synthesis.md` and `presentations/index.html` only after versioned files succeed.

For Standard and Deep-audit projects, every completed main or side round creates a new versioned synthesis and updates the current pointer. Quick mode creates a synthesis only when the user requests a durable report or upgrades the project.

- [ ] **Step 4: Enforce presentation rules**

HTML uses embedded CSS, semantic headings, print styles, accessible tables, no remote assets, and no automatic browser launch. CSV includes stable source key, citation, type, language, scholarly importance, acquisition priority, availability, review extent, reading priority, links, and round membership.

- [ ] **Step 5: Add failure-atomicity and no-network tests**

```python
def test_failed_render_keeps_last_valid_index(self):
    previous = seed_valid_index(self.tmp_path)
    with self.assertRaises(BundleValidationError):
        render_outputs(bundle_path=invalid_bundle_path(self.tmp_path), output_root=self.tmp_path, **ledger_paths(self.tmp_path))
    self.assertEqual(previous, (self.tmp_path / "presentations/index.html").read_bytes())
```

- [ ] **Step 6: Verify GREEN and commit**

```bash
python3 -m unittest international-law-search/tests/test_render_outputs.py international-law-search/tests/test_reader_report.py -v
git add international-law-search/scripts/render_research_outputs.py international-law-search/tests/test_render_outputs.py international-law-search/references/deliverables.md international-law-search/templates/reader-report.md
git commit -m "feat: render consistent research presentations"
```

### Task 9: Rewrite the skill workflow around rounds

**Files:**
- Modify: `international-law-search/SKILL.md`
- Modify: `international-law-search/references/modes-and-rounds.md`
- Modify: `international-law-search/references/orchestration.md`
- Modify: `international-law-search/references/access-and-privacy.md`
- Modify: `international-law-search/references/multilingual-retrieval.md`
- Modify: `international-law-search/templates/subagent-brief.md`
- Modify: `international-law-search/agents/openai.yaml`

- [ ] **Step 1: Replace fixed stage gates with the working loop**

```markdown
## Working Loop

1. Complete only the readiness fields needed for the next round, asking one material question at a time.
2. Present one concise round specification and obtain approval before external retrieval.
3. Run the approved main or side round within its three-axis budget.
4. Upsert sources, validate claims, append the immutable round record, and generate authorized outputs.
5. Pause with saved next-round designs. The user may repeat, redirect, synthesize, start a side round, write, or close.
```

- [ ] **Step 2: Preserve hard boundaries and route progressive disclosure**

Keep approval before external retrieval, private-material restrictions, truthful review status, disputed-law qualifications, user thesis ownership, and non-exhaustiveness. Route intake to `readiness-and-scale.md`, execution to `research-rounds.md`, and accumulated knowledge to `knowledge-and-synthesis.md`.

- [ ] **Step 3: Update orchestration and access recovery**

Subagent briefs include round ID and type, exact assignment, three-axis budget, platforms and purposes, permitted seeds and directions, privacy constraints, and candidate source and claim-evidence returns. The main agent alone mutates shared ledgers. Access recovery covers official, publisher, library, subscription, repository, physical-copy, purchase, and document-delivery routes without upgrading snippets into evidence.

For United Nations materials, record the failed official route, then try another official UN document surface or stable identifier lookup before authorized library or repository alternatives. Never relabel indexed snippets as reviewed official text.

- [ ] **Step 4: Persist multilingual terminology**

Every language branch records native concepts, variants, legal distinctions, search uses, and the gap it addresses in `knowledge/terminology.jsonl`. Translation does not establish legal equivalence.

- [ ] **Step 5: Verify GREEN and commit**

```bash
python3 -m unittest international-law-search/tests/test_v3_contract.py international-law-search/tests/test_skill_contract.py international-law-search/tests/test_modes_and_rounds.py international-law-search/tests/test_round_metrics.py -v
git add international-law-search/SKILL.md international-law-search/references international-law-search/templates/subagent-brief.md international-law-search/agents/openai.yaml
git commit -m "refactor: replace fixed search stages with research rounds"
```

### Task 10: Add doctoral and writing-time end-to-end fixtures

**Files:**
- Create: `international-law-search/tests/fixtures/v3/doctoral-corpus/`
- Create: `international-law-search/tests/fixtures/v3/side-round/`
- Create: `international-law-search/tests/test_v3_e2e.py`
- Modify: `international-law-search/tests/fixtures/benchmark_cases.json`
- Modify: `international-law-search/tests/test_benchmarks.py`
- Modify: `international-law-search/tests/test_user_centered_e2e.py`

- [ ] **Step 1: Add the doctoral discovery scenario**

```python
def test_doctoral_round_separates_discovery_acquisition_and_review(self):
    project = load_fixture("doctoral-corpus")
    self.assertEqual(80, project.round["planned_budget"]["bibliographic_discovery"])
    self.assertEqual(25, project.round["planned_budget"]["full_text_acquisition"])
    self.assertEqual(12, project.round["planned_budget"]["substantive_review"])
    book = project.source("SRC-BOOK-1")
    self.assertEqual("must_obtain", book["acquisition_priority"])
    self.assertEqual("not_reviewed", book["review_extent"])
```

The fixture includes a foundational physical book with verified ISBN and library holding but no substantive description beyond metadata or contents evidence.

- [ ] **Step 2: Add repeat-breadth and side-round scenarios**

```python
def test_user_may_choose_breadth_expansion_after_breadth(self):
    rounds = fixture_rounds("doctoral-corpus")
    self.assertEqual(["breadth", "breadth_expansion"], [item["round_type"] for item in rounds[:2]])

def test_side_round_updates_claims_without_advancing_main_round(self):
    project = load_fixture("side-round")
    self.assertEqual("R2.S1", project.side_round["round_id"])
    self.assertEqual("R3", project.next_main_round_id)
    self.assertEqual("contested", project.claim("CLM-1")["status"])
```

The side-round fixture also stores a multilingual terminology group for `obsolete`, `desuetude`, `obsolescence`, `dead letter`, and `inapplicable`, with non-equivalence notes and search functions. Add a `primary_materials` fixture branch that performs a real case-law surface check and records either responsive cases or an honest zero-result coverage entry.

- [ ] **Step 3: Update benchmarks**

Replace fixed Stage 1/2 expectations with repeated breadth, source-type expansion, side-round verification, inaccessible foundational books, and synthesis-only rounds. Retain all privacy, access, depth-budget, and non-exhaustiveness cases.

- [ ] **Step 4: Verify GREEN and commit**

```bash
python3 -m unittest international-law-search/tests/test_v3_e2e.py international-law-search/tests/test_benchmarks.py international-law-search/tests/test_user_centered_e2e.py -v
git add international-law-search/tests
git commit -m "test: cover doctoral and writing-time workflows"
```

### Task 11: Preserve privacy, graph, and deep-audit controls

**Files:**
- Modify: `international-law-search/scripts/validate_export_manifest.py`
- Modify: `international-law-search/scripts/validate_corpus.py`
- Modify: `international-law-search/scripts/checkpoint_state.py`
- Modify: `international-law-search/references/graph-and-saturation.md`
- Modify: relevant existing regression tests.

- [ ] **Step 1: Add failing regression cases**

```python
def test_reader_bundle_rejects_local_path(self):
    bundle = valid_bundle()
    bundle["narrative_sections"][0]["text"] = "/Users/example/private-note.pdf"
    self.assertTrue(any("local path" in error for error in validate_bundle_fixture(bundle)))

def test_budget_pause_never_claims_saturation(self):
    round_record = paused_round(budget_status="budget_paused", saturation_claimed=True)
    self.assertTrue(any("saturation" in error for error in validate_round_fixture(round_record)))
```

- [ ] **Step 2: Adapt deep-audit state**

Keep atomic branch cursor transitions and authorization links. Point round evidence to the authoritative round record rather than a competing stage record. Validate optional edges only when graph support is enabled.

- [ ] **Step 3: Run regressions and commit**

```bash
python3 -m unittest international-law-search/tests/test_export_privacy.py international-law-search/tests/test_validate_corpus.py international-law-search/tests/test_checkpoint_state.py international-law-search/tests/test_nicaragua_e2e_fixture.py -v
git add international-law-search/scripts/validate_export_manifest.py international-law-search/scripts/validate_corpus.py international-law-search/scripts/checkpoint_state.py international-law-search/references/graph-and-saturation.md international-law-search/tests
git commit -m "refactor: preserve audit controls in v3 rounds"
```

### Task 12: Full validation and release preparation

**Files:**
- Modify only files required by observed failures.

- [ ] **Step 1: Run the complete suite**

```bash
python3 -m unittest discover -s international-law-search/tests -p 'test_*.py' -v
```

Expected: all tests PASS with no skipped v3 behavioral tests.

- [ ] **Step 2: Run the official skill validator**

```bash
python3 /Users/kaiqiangzhang/.codex/skills/.system/skill-creator/scripts/quick_validate.py international-law-search
```

Expected: `Skill is valid!`

- [ ] **Step 3: Run static checks**

```bash
git diff --check
python3 -m py_compile international-law-search/scripts/*.py
rg -n 'Stage 2 cannot begin|Ordinary range: 15–30|TBD|TODO|PLACEHOLDER' international-law-search
```

Expected: no whitespace or syntax errors and no stale fixed-stage rule or unfinished placeholder. Historical fixture text must be assessed rather than deleted mechanically.

- [ ] **Step 4: Inspect rendered fixture artifacts**

Generate the doctoral fixture into a temporary directory. Verify that the round Markdown, synthesis Markdown, round HTML, project `index.html`, and bibliography CSV exist; internal links resolve; no network asset loads; the inaccessible foundational book remains visible; and machine logs are not prominent.

- [ ] **Step 5: Commit observed final fixes**

```bash
git add international-law-search
git commit -m "feat: complete international law search v3"
```

Do not create an empty commit.

- [ ] **Step 6: Report deployment choices**

Report the final commit, test count, validator result, migration behavior, and main artifacts. Ask before replacing the globally installed copy or pushing commits if those actions have not been authorized for this upgrade.

The final user-facing handoff must identify the project `index.html`, `current-synthesis.md`, latest immutable round report, and `bibliography.csv` directly; it must not require the user to ask where the outputs are.
