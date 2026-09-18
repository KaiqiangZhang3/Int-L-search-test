# User-Centered International Law Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `international-law-search` into an upgradeable quick, standard-interactive, and deep-audit research assistant that centers user decisions and readable research outputs while preserving source truthfulness, privacy, provenance, and recoverability.

**Architecture:** Keep one skill entrypoint with stage- and mode-based routing. All modes share an upgrade-safe lightweight source ledger; standard mode adds decision checkpoints, and deep-audit mode enriches the same records with persistent state, event logs, optional graph data, and validation. Reader-facing reports and machine exports derive from the same records but use separate presentation contracts.

**Tech Stack:** Markdown skill instructions and templates, JSON Schema Draft 2020-12, Python 3 standard library, `jsonschema`, `unittest`, JSONL fixtures, Codex skill validation scripts.

---

## File Structure

### Entrypoint and focused references

- Modify `international-law-search/SKILL.md`: concise mode selection, shared invariants, stage gates, and reference routing.
- Create `international-law-search/references/modes-and-rounds.md`: readiness interview, quick/standard/deep behavior, budgets, checkpoints, closure, and upgrades.
- Create `international-law-search/references/source-ledger.md`: minimum ledger, two-axis access model, ranking factors, and upgrade rules.
- Create `international-law-search/references/international-law-sources.md`: type-specific identity, legal-status, version, and authority guidance.
- Create `international-law-search/references/multilingual-retrieval.md`: per-language vocabulary, platforms, budgets, translation authority, and regional coverage.
- Modify `international-law-search/references/access-and-privacy.md`: retain privacy invariants and adopt availability/review terminology.
- Modify `international-law-search/references/orchestration.md`: lightweight candidate returns outside deep-audit mode and post-selection vertical tracing.
- Modify `international-law-search/references/graph-and-saturation.md`: optional graph, separated relation families, and budget-versus-saturation rules.
- Modify `international-law-search/references/deliverables.md`: archive/report boundary, reader-first reports, citation styles, and optional machine attachments.
- Replace `international-law-search/references/intake-and-approval.md` and `international-law-search/references/source-strategy.md` with short compatibility routers to the new focused references, then remove the routers after all callers and tests have migrated.

### Templates

- Create `international-law-search/templates/scope-card.md`: concise stage-0 confirmation.
- Create `international-law-search/templates/breadth-checkpoint.md`: field map, seed menu, budget actuals, gaps, and decision panel.
- Create `international-law-search/templates/depth-checkpoint.md`: per-seed paths, additions, duplicates, positions, and next decisions.
- Create `international-law-search/templates/decision-panel.md`: concrete user controls and mode upgrade choices.
- Modify `international-law-search/templates/search-plan.md`: deep-audit plan only.
- Modify `international-law-search/templates/reader-report.md`: Chinese-capable reader-first research report and retrieval-archive variants.
- Modify `international-law-search/templates/subagent-brief.md`: mode-aware concise or full candidate contract.

### Schemas and scripts

- Create `international-law-search/schemas/source-ledger-record.schema.json`: shared minimum record for quick and standard modes.
- Modify `international-law-search/schemas/source-record.schema.json`: deep-audit record with availability, review extent, type extensions, links, ranking factors, and version relations.
- Modify `international-law-search/schemas/candidate-source-record.schema.json`: two-axis access and mode-aware minimum submission.
- Modify `international-law-search/schemas/project-state.schema.json`: explicit stage transitions, user decisions, mode upgrades, and optional graph state.
- Modify `international-law-search/schemas/edge-record.schema.json`: literature and institutional relationships only; retrieval provenance moves to source records.
- Modify `international-law-search/scripts/corpus_ops.py`: evidence-consistent access validation and independent-field merging.
- Modify `international-law-search/scripts/init_workspace.py`: deep-audit initialization and version marker.
- Modify `international-law-search/scripts/validate_corpus.py`: validate new records and optional edge files.
- Create `international-law-search/scripts/migrate_v1_workspace.py`: non-destructive migration of existing workspaces.
- Create `international-law-search/scripts/validate_reader_report.py`: deterministic report-structure and unresolved-marker checks.

### Tests and fixtures

- Modify existing unit tests under `international-law-search/tests/` to migrate rejected version-1 contracts.
- Create `international-law-search/tests/test_modes_and_rounds.py`.
- Create `international-law-search/tests/test_source_ledger.py`.
- Create `international-law-search/tests/test_migrate_v1_workspace.py`.
- Create `international-law-search/tests/test_reader_report.py`.
- Create `international-law-search/tests/test_user_centered_e2e.py`.
- Create fixtures under `international-law-search/tests/fixtures/user-centered/` for quick upgrade, standard checkpoints, multilingual retrieval, report modes, and version-1 migration.
- Preserve and migrate `docs/superpowers/evals/fixtures/nicaragua-e2e/` as the deep-audit regression fixture.

## Task 1: Capture the New RED Behavioral Contract

**Files:**
- Modify: `international-law-search/tests/fixtures/benchmark_cases.json`
- Create: `international-law-search/tests/test_modes_and_rounds.py`
- Modify: `international-law-search/tests/test_skill_contract.py`
- Create: `docs/superpowers/evals/2026-09-18-international-law-search-redesign-red.md`

- [ ] **Step 1: Add realistic behavior fixtures**

Add cases for `vague-corporate-role-readiness`, `standard-round-1-checkpoint`, `user-selected-seeds`, `quick-mode-upgrade`, `independent-chinese-branch`, `reader-first-report`, and paired `retrieval-archive`/`research-report` boundaries. Each fixture must define the prompt, approved mode, observable required behavior, and prohibited behavior.

```json
{
  "id": "quick-mode-upgrade",
  "prompt": "Give me 10–15 reliable sources on corporate international legal personality, then let me deepen selected sources.",
  "required": [
    "quick scope approval also authorizes delivery",
    "no mandatory graph or deep-audit workspace",
    "offer upgrade using the existing ledger"
  ],
  "prohibited": [
    "restart retrieval after upgrade",
    "silently begin citation tracing"
  ]
}
```

- [ ] **Step 2: Add failing contract tests for modes and stage gates**

```python
def test_standard_mode_requires_user_seed_selection_before_depth(self):
    text = (ROOT / "references/modes-and-rounds.md").read_text(encoding="utf-8")
    assert "Stage 1" in text
    assert "must stop" in text
    assert "user-confirmed seeds" in text


def test_quick_mode_is_upgradeable_without_restart(self):
    text = (ROOT / "references/modes-and-rounds.md").read_text(encoding="utf-8")
    assert "Quick mode" in text
    assert "reuse" in text.lower()
    assert "must not restart" in text.lower()
```

- [ ] **Step 3: Run the focused tests and preserve the failure evidence**

Run: `python3 -m unittest international-law-search.tests.test_modes_and_rounds international-law-search.tests.test_skill_contract -v`

Expected: FAIL because `references/modes-and-rounds.md` and the new mode contract do not exist.

Record the exact old-skill behaviors contradicted by each failure in `docs/superpowers/evals/2026-09-18-international-law-search-redesign-red.md`, using `user_feedback.docx` as the real-use baseline rather than inventing synthetic failure quotes.

- [ ] **Step 4: Commit the RED contract**

```bash
git add international-law-search/tests/fixtures/benchmark_cases.json international-law-search/tests/test_modes_and_rounds.py international-law-search/tests/test_skill_contract.py docs/superpowers/evals/2026-09-18-international-law-search-redesign-red.md
git commit -m "test: define user-centered search behavior"
```

## Task 2: Implement Mode Routing, Readiness, and Stage Gates

**Files:**
- Modify: `international-law-search/SKILL.md`
- Create: `international-law-search/references/modes-and-rounds.md`
- Create: `international-law-search/templates/scope-card.md`
- Create: `international-law-search/templates/breadth-checkpoint.md`
- Create: `international-law-search/templates/depth-checkpoint.md`
- Create: `international-law-search/templates/decision-panel.md`
- Modify: `international-law-search/references/intake-and-approval.md`

- [ ] **Step 1: Write the failing scope-card and checkpoint assertions**

```python
def test_scope_card_contains_only_next_round_decisions(self):
    text = (ROOT / "templates/scope-card.md").read_text(encoding="utf-8")
    for field in ["Research question", "Included", "Excluded", "Mode", "Next-round budget"]:
        assert field in text
    assert "Exact query strings" not in text


def test_breadth_checkpoint_ends_with_concrete_user_controls(self):
    text = (ROOT / "templates/breadth-checkpoint.md").read_text(encoding="utf-8")
    for field in ["Field map", "Candidate seeds", "Planned versus actual", "Decision panel"]:
        assert field in text
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python3 -m unittest international-law-search.tests.test_modes_and_rounds -v`

Expected: FAIL on missing templates and routing language.

- [ ] **Step 3: Rewrite the entrypoint as a mode and stage router**

The new `SKILL.md` must declare standard interactive mode as the recommendation for ambiguous substantial requests, preserve user mode choice, permit quick-to-standard-to-deep upgrades, and route only to references needed for the current stage. Its hard boundaries must allow cited descriptive synthesis in research-report mode while continuing to prohibit unsupported conclusions, thesis selection, and argumentative ghostwriting.

```markdown
## Choose the working mode

- Use quick mode for a bounded starting bibliography.
- Recommend standard interactive mode for ambiguous or substantial research requests.
- Use deep-audit mode when the user requires reproducibility, persistent state, full logs, or validated structured data.

Mode choice belongs to the user. Reuse the shared ledger when upgrading; do not restart completed retrieval.
```

- [ ] **Step 4: Implement the readiness and round contract**

`modes-and-rounds.md` must define adaptive one-question-at-a-time intake, recommended defaults, exploratory scope assistance, multidimensional budgets, mandatory Stage-1 pause, user-owned seed selection, optional gap filling, closure semantics, and mode upgrades. `intake-and-approval.md` becomes a short compatibility router until all references have migrated.

- [ ] **Step 5: Add checkpoint templates**

The breadth template must cap the ordinary result at 15–30 candidates, present five to ten seed choices, distinguish research gaps from retrieval gaps, and end with concrete actions. The decision panel must include continue, delete branch, select seed, review without tracing, change language/date/source budget, upgrade mode, stop and deliver, and request another bounded exploratory round.

- [ ] **Step 6: Run contract tests**

Run: `python3 -m unittest international-law-search.tests.test_modes_and_rounds international-law-search.tests.test_skill_contract -v`

Expected: PASS for the new mode and stage tests; any failures must identify remaining version-1 assertions to migrate rather than be bypassed.

- [ ] **Step 7: Commit the vertical slice**

```bash
git add international-law-search/SKILL.md international-law-search/references/modes-and-rounds.md international-law-search/references/intake-and-approval.md international-law-search/templates/scope-card.md international-law-search/templates/breadth-checkpoint.md international-law-search/templates/depth-checkpoint.md international-law-search/templates/decision-panel.md international-law-search/tests
git commit -m "feat: add user-controlled search modes and rounds"
```

## Task 3: Add the Upgrade-Safe Lightweight Source Ledger

**Files:**
- Create: `international-law-search/schemas/source-ledger-record.schema.json`
- Create: `international-law-search/references/source-ledger.md`
- Create: `international-law-search/tests/test_source_ledger.py`
- Modify: `international-law-search/tests/test_schemas.py`

- [ ] **Step 1: Write failing schema tests for minimum upgrade data**

```python
def test_lightweight_ledger_requires_upgrade_safe_fields(self):
    schema = load_schema("source-ledger-record.schema.json")
    assert {
        "source_key", "identity_evidence", "discovery_provenance",
        "availability", "review_extent", "description_basis",
        "description", "inclusion_reason", "user_decisions"
    }.issubset(schema["required"])


def test_quick_record_does_not_require_graph_or_audit_events(self):
    schema = load_schema("source-ledger-record.schema.json")
    assert "retrieval_history" not in schema["required"]
    assert "edges" not in schema["properties"]
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest international-law-search.tests.test_source_ledger -v`

Expected: FAIL because the ledger schema is missing.

- [ ] **Step 3: Create the minimum ledger schema**

Define closed enums for `availability` and `review_extent`, stable session keys, identifiers, links, local paths, discovery provenance, description evidence, ranking factors, reading priority, source type, language, version relationships, and user decisions. Keep deep-audit event history optional.

```json
{
  "availability": "subscription_full_text",
  "review_extent": "selected_sections_reviewed",
  "description_basis": {
    "kind": "selected_sections",
    "locations": ["Introduction", "Part III", "Conclusion"]
  }
}
```

- [ ] **Step 4: Document reader labels and upgrade invariants**

`source-ledger.md` must map internal enums to natural reader-facing labels without requiring English system terms in a Chinese report. It must state that enrichment may add evidence but cannot discard provenance, silently change identity, or overstate prior review.

- [ ] **Step 5: Run schema tests**

Run: `python3 -m unittest international-law-search.tests.test_source_ledger international-law-search.tests.test_schemas -v`

Expected: PASS for the new ledger and migrated schema expectations.

- [ ] **Step 6: Commit**

```bash
git add international-law-search/schemas/source-ledger-record.schema.json international-law-search/references/source-ledger.md international-law-search/tests/test_source_ledger.py international-law-search/tests/test_schemas.py
git commit -m "feat: add upgrade-safe source ledger"
```

## Task 4: Replace the Single Access Status with Two Evidence Axes

**Files:**
- Modify: `international-law-search/schemas/source-record.schema.json`
- Modify: `international-law-search/schemas/candidate-source-record.schema.json`
- Modify: `international-law-search/scripts/corpus_ops.py`
- Modify: `international-law-search/tests/test_corpus_ops.py`
- Modify: `international-law-search/tests/test_schemas.py`
- Modify: `international-law-search/references/access-and-privacy.md`

- [ ] **Step 1: Write one failing valid-combination test**

```python
def test_subscription_full_text_can_coexist_with_abstract_review(self):
    record = base_record(
        availability="subscription_full_text",
        review_extent="abstract_reviewed",
        description_basis={"kind": "abstract", "locations": ["Publisher abstract"]},
    )
    validate_record(record)
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python3 -m unittest international-law-search.tests.test_schemas.SchemaTests.test_subscription_full_text_can_coexist_with_abstract_review -v`

Expected: FAIL because version 1 exposes only `access_status`.

- [ ] **Step 3: Implement the two-axis schema and validation**

Replace `access_status` precedence with independent `availability` and `review_extent`. Require evidence-consistent `description_basis`. A route that only provides metadata or an abstract cannot support selected-section or substantive-full-text review. A separate local or subscription route may support stronger review even if another route failed.

- [ ] **Step 4: Write one failing merge test**

```python
def test_merge_improves_availability_without_overwriting_review_evidence():
    left = source(availability="abstract_available", review_extent="abstract_reviewed")
    right = source(availability="subscription_full_text", review_extent="not_reviewed")
    merged = merge_records(left, right)
    assert merged["availability"] == "subscription_full_text"
    assert merged["review_extent"] == "abstract_reviewed"
```

- [ ] **Step 5: Implement independent-field merging and rerun tests**

Run: `python3 -m unittest international-law-search.tests.test_corpus_ops international-law-search.tests.test_schemas -v`

Expected: PASS. Delete or rewrite the old test that ranks `Full text not read` above `Abstract only`; do not preserve that rejected behavior.

- [ ] **Step 6: Update the access reference and commit**

```bash
git add international-law-search/schemas/source-record.schema.json international-law-search/schemas/candidate-source-record.schema.json international-law-search/scripts/corpus_ops.py international-law-search/tests/test_corpus_ops.py international-law-search/tests/test_schemas.py international-law-search/references/access-and-privacy.md
git commit -m "feat: separate source availability from review extent"
```

## Task 5: Add International-Law Metadata and Version Normalization

**Files:**
- Create: `international-law-search/references/international-law-sources.md`
- Modify: `international-law-search/schemas/source-ledger-record.schema.json`
- Modify: `international-law-search/schemas/source-record.schema.json`
- Modify: `international-law-search/scripts/corpus_ops.py`
- Modify: `international-law-search/tests/test_corpus_ops.py`
- Modify: `international-law-search/tests/test_schemas.py`
- Modify: `international-law-search/references/source-strategy.md`

- [ ] **Step 1: Write failing type-extension tests**

```python
def test_case_extension_records_procedural_context(self):
    schema = load_schema("source-record.schema.json")
    case = schema["$defs"]["case_details"]
    assert {"court", "decision_date", "procedural_stage"}.issubset(case["required"])


def test_article_publication_is_not_a_formatted_citation_blob(self):
    record = article_record(journal="European Journal of International Law", volume="35")
    assert_schema_valid(record)
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest international-law-search.tests.test_schemas -v`

Expected: FAIL on missing type-specific definitions.

- [ ] **Step 3: Add common fields and type extensions**

Implement case, treaty, international-organization document, article, book, chapter, working-paper, institutional-report, and commentary details. Represent legal status contextually through issuing authority, addressees or parties, procedural posture, jurisdictional context, and status date rather than a global `binding` flag.

- [ ] **Step 4: Add version and link relations**

Support `is_version_of`, `revises`, `consolidates`, `corrects`, `has_protocol`, `has_annex`, `interprets_decision`, `implements`, and `supersedes`, with distinct official, publisher, open-access, and stable links. Normalize title capitalization before conflict detection.

- [ ] **Step 5: Permit qualified commentary**

Update source strategy so high-quality international-law blogs and practitioner analysis may appear as a labeled commentary class. Ordinary webpages remain discovery leads unless they are the research object.

- [ ] **Step 6: Run tests and commit**

Run: `python3 -m unittest international-law-search.tests.test_schemas international-law-search.tests.test_corpus_ops -v`

Expected: PASS.

```bash
git add international-law-search/references/international-law-sources.md international-law-search/references/source-strategy.md international-law-search/schemas/source-ledger-record.schema.json international-law-search/schemas/source-record.schema.json international-law-search/scripts/corpus_ops.py international-law-search/tests/test_corpus_ops.py international-law-search/tests/test_schemas.py
git commit -m "feat: normalize international-law source types and versions"
```

## Task 6: Add Non-Destructive Version-1 Migration

**Files:**
- Create: `international-law-search/scripts/migrate_v1_workspace.py`
- Create: `international-law-search/tests/test_migrate_v1_workspace.py`
- Create: `international-law-search/tests/fixtures/user-centered/v1-workspace/`
- Modify: `international-law-search/scripts/init_workspace.py`
- Modify: `international-law-search/tests/test_workspace.py`

- [ ] **Step 1: Write a failing migration test**

```python
def test_migration_preserves_source_ids_and_flags_ambiguous_access(tmp_path):
    source = copy_fixture("v1-workspace", tmp_path / "project")
    result = migrate(source, tmp_path / "project-v2")
    migrated = read_jsonl(result / "corpus" / "sources.jsonl")
    assert migrated[0]["legacy_ids"] == ["source-001"]
    assert migrated[0]["migration_review_required"] is True
    assert (source / "corpus" / "sources.jsonl").exists()
```

- [ ] **Step 2: Run the migration test and verify RED**

Run: `python3 -m unittest international-law-search.tests.test_migrate_v1_workspace -v`

Expected: FAIL because the migration module does not exist.

- [ ] **Step 3: Implement explicit access mapping**

Use the following conservative mapping:

```python
ACCESS_MAP = {
    "Full text read": ("identified_inaccessible", "full_text_substantively_reviewed", True),
    "Full text not read": ("identified_inaccessible", "not_reviewed", True),
    "Abstract only": ("abstract_available", "abstract_reviewed", False),
    "Metadata only": ("metadata_only", "metadata_verified", False),
    "Access failed": ("access_failure", "not_reviewed", False),
}
```

The third value marks ambiguity requiring review. Override the proposed availability only when a preserved retrieval event proves an open, subscription, or local full-text route.

- [ ] **Step 4: Migrate edges and state without overwriting the source workspace**

Separate `discovered_from` into retrieval provenance. Preserve `cites` as a literature relation. Retain `interprets`, `response_to`, and other judgmental edges as candidates unless their evidence remains sufficient. Copy approval, round, coverage, and stopping evidence into the new state model.

- [ ] **Step 5: Add version markers to new workspaces**

`init_workspace.py` must write `schema_version: 2` and create graph files only when graph support is selected.

- [ ] **Step 6: Run migration and workspace tests**

Run: `python3 -m unittest international-law-search.tests.test_migrate_v1_workspace international-law-search.tests.test_workspace -v`

Expected: PASS with the original fixture unchanged and all ambiguous conversions reported.

- [ ] **Step 7: Commit**

```bash
git add international-law-search/scripts/migrate_v1_workspace.py international-law-search/scripts/init_workspace.py international-law-search/tests/test_migrate_v1_workspace.py international-law-search/tests/test_workspace.py international-law-search/tests/fixtures/user-centered/v1-workspace
git commit -m "feat: migrate version-one search workspaces"
```

## Task 7: Implement Reader-First Reports and Controlled Synthesis

**Files:**
- Modify: `international-law-search/references/deliverables.md`
- Modify: `international-law-search/templates/reader-report.md`
- Create: `international-law-search/scripts/validate_reader_report.py`
- Create: `international-law-search/tests/test_reader_report.py`
- Create: `international-law-search/tests/fixtures/user-centered/research-report.md`
- Create: `international-law-search/tests/fixtures/user-centered/retrieval-archive.md`

- [ ] **Step 1: Write failing report-contract tests**

```python
def test_chinese_report_leads_with_field_understanding(self):
    report = fixture("research-report.md")
    headings = markdown_headings(report)
    assert headings[:3] == ["问题界定", "研究脉络", "主要立场与争论"]
    assert headings.index("推荐阅读路径") < headings.index("检索范围与限制")


def test_archive_omits_cross_source_synthesis_labels(self):
    report = fixture("retrieval-archive.md")
    assert "多项来源共同显示" not in report
    assert "谨慎归纳" not in report
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest international-law-search.tests.test_reader_report -v`

Expected: FAIL because the version-1 report starts with scope, IDs, and graph navigation.

- [ ] **Step 3: Rewrite the deliverable contract and template**

Support Word, Markdown, and HTML; citation styles including OSCOLA, Bluebook, Chicago, and GB/T 7714; ordering by theme, chronology, authority, relevance, priority, position, or source type; and a default theme-plus-priority view with a timeline where useful. Keep source IDs and machine enums out of the opening report.

- [ ] **Step 4: Implement the deterministic report validator**

`validate_reader_report.py` must reject unfilled template markers, unresolved manual-review items in a final report, missing source citations for synthetic claims, and a final Chinese report whose opening headings are machine-state sections. It must not attempt to judge legal correctness through keyword counts.

```python
FORBIDDEN_MARKERS = ("{{", "}}", "TODO", "TBD")


def validate_report(text: str, *, language: str, final: bool) -> list[str]:
    errors = [f"Unresolved marker: {marker}" for marker in FORBIDDEN_MARKERS if marker in text]
    if final and "manual review required" in text.lower():
        errors.append("Final report contains unresolved manual-review items")
    return errors
```

- [ ] **Step 5: Add paired fixtures and run tests**

Run: `python3 -m unittest international-law-search.tests.test_reader_report -v`

Expected: PASS. Manually inspect both fixtures to confirm the archive does not synthesize and the research report labels source claims, multi-source trends, and cautious inferences.

- [ ] **Step 6: Commit**

```bash
git add international-law-search/references/deliverables.md international-law-search/templates/reader-report.md international-law-search/scripts/validate_reader_report.py international-law-search/tests/test_reader_report.py international-law-search/tests/fixtures/user-centered/research-report.md international-law-search/tests/fixtures/user-centered/retrieval-archive.md
git commit -m "feat: add reader-first international-law reports"
```

## Task 8: Implement Independent Multilingual Branches

**Files:**
- Create: `international-law-search/references/multilingual-retrieval.md`
- Modify: `international-law-search/references/modes-and-rounds.md`
- Modify: `international-law-search/templates/scope-card.md`
- Modify: `international-law-search/templates/breadth-checkpoint.md`
- Modify: `international-law-search/tests/test_modes_and_rounds.py`
- Create: `international-law-search/tests/fixtures/user-centered/chinese-branch.json`

- [ ] **Step 1: Write a failing multilingual branch test**

```python
def test_chinese_branch_has_its_own_purpose_vocabulary_platforms_and_budget(self):
    branch = json.loads(fixture("chinese-branch.json"))
    assert branch["language"] == "zh"
    assert branch["purpose"]
    assert branch["local_vocabulary"]
    assert set(branch["platforms"]) >= {"CNKI", "PKULaw", "Wanfang"}
    assert set(branch["budget"]) >= {"queries", "candidates", "full_text_reviews"}
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest international-law-search.tests.test_modes_and_rounds -v`

Expected: FAIL because the language-branch contract and fixture do not exist.

- [ ] **Step 3: Implement the language-branch reference and templates**

Require a research purpose, local vocabulary, platforms, access assumptions, budget, official-translation status, actual contribution, and remaining gap for every substantive language. Do not use English as a fixed baseline. Permit only isolated verification work to use an unbudgeted auxiliary language.

- [ ] **Step 4: Make regional and Global South coverage measurable**

When applicable, the scope card records the intended regions, languages, platforms, or perspectives; the checkpoint reports actual additions and remaining gaps. Do not claim representative coverage from the mere presence of one non-English source.

- [ ] **Step 5: Run tests and commit**

Run: `python3 -m unittest international-law-search.tests.test_modes_and_rounds -v`

Expected: PASS.

```bash
git add international-law-search/references/multilingual-retrieval.md international-law-search/references/modes-and-rounds.md international-law-search/templates/scope-card.md international-law-search/templates/breadth-checkpoint.md international-law-search/tests/test_modes_and_rounds.py international-law-search/tests/fixtures/user-centered/chinese-branch.json
git commit -m "feat: add independent multilingual retrieval branches"
```

## Task 9: Make Subagents and Relationship Graphs Mode-Aware

**Files:**
- Modify: `international-law-search/references/orchestration.md`
- Modify: `international-law-search/references/graph-and-saturation.md`
- Modify: `international-law-search/templates/subagent-brief.md`
- Modify: `international-law-search/schemas/edge-record.schema.json`
- Modify: `international-law-search/schemas/project-state.schema.json`
- Modify: `international-law-search/scripts/validate_corpus.py`
- Modify: `international-law-search/tests/test_validate_corpus.py`
- Modify: `international-law-search/tests/test_schemas.py`
- Modify: `international-law-search/tests/test_round_metrics.py`

- [ ] **Step 1: Write failing graph-optionality and relation tests**

```python
def test_deep_audit_without_citation_tracing_does_not_require_edges(self):
    state = deep_audit_state(graph_enabled=False)
    validate_state(state)


def test_retrieval_provenance_is_not_an_edge_relation(self):
    schema = load_schema("edge-record.schema.json")
    assert "discovered_from" not in schema["properties"]["relation"]["enum"]
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest international-law-search.tests.test_schemas international-law-search.tests.test_validate_corpus -v`

Expected: FAIL because version 1 requires edge-oriented deep-audit state and permits `discovered_from`.

- [ ] **Step 3: Separate relation families and optional graph state**

Allow literature relations such as `cites`, `responds_to`, `criticizes`, and `extends`, plus institutional relations such as `amends`, `implements`, `interprets`, and `same_proceeding`. Move query, platform, seed, footnote, bibliography, and subagent discovery into source provenance. Require precise textual evidence for judgmental relations.

- [ ] **Step 4: Update orchestration contracts**

Initial breadth branches may not launch vertical tracing. After user seed approval, horizontal gap filling and vertical tracing may run concurrently. Quick and standard subagents return the lightweight ledger contract; deep-audit branches return canonical candidates and optional edges.

- [ ] **Step 5: Separate budget stops from saturation**

Update state and metrics so a per-branch cap records `budget_paused` and cannot imply saturation. Formal saturation assessment runs only when enabled and requires multi-round yield, duplicate, coverage, failure, and open-path evidence.

- [ ] **Step 6: Run graph, state, metric, and validation tests**

Run: `python3 -m unittest international-law-search.tests.test_schemas international-law-search.tests.test_validate_corpus international-law-search.tests.test_round_metrics -v`

Expected: PASS with and without an edge file when graph support is disabled.

- [ ] **Step 7: Commit**

```bash
git add international-law-search/references/orchestration.md international-law-search/references/graph-and-saturation.md international-law-search/templates/subagent-brief.md international-law-search/schemas/edge-record.schema.json international-law-search/schemas/project-state.schema.json international-law-search/scripts/validate_corpus.py international-law-search/tests/test_validate_corpus.py international-law-search/tests/test_schemas.py international-law-search/tests/test_round_metrics.py
git commit -m "feat: make retrieval graphs and subagents mode-aware"
```

## Task 10: Add Quick-Upgrade and Standard-Interaction End-to-End Fixtures

**Files:**
- Create: `international-law-search/tests/test_user_centered_e2e.py`
- Create: `international-law-search/tests/fixtures/user-centered/quick-upgrade/`
- Create: `international-law-search/tests/fixtures/user-centered/standard-corporate-role/`
- Modify: `international-law-search/tests/test_nicaragua_e2e_fixture.py`
- Modify: `docs/superpowers/evals/2026-09-17-international-law-search-e2e.md`

- [ ] **Step 1: Write a failing quick-upgrade E2E test**

```python
def test_quick_result_upgrades_without_losing_sources_or_user_decisions(self):
    quick = load_json("quick-upgrade/quick-session.json")
    standard = load_json("quick-upgrade/standard-session.json")
    assert set(quick["source_keys"]).issubset(standard["source_keys"])
    assert quick["user_decisions"] == standard["inherited_user_decisions"]
    assert standard["stage"] == "round_1_waiting_for_user"
```

- [ ] **Step 2: Write a failing standard checkpoint E2E test**

```python
def test_standard_fixture_cannot_enter_depth_without_selected_seeds(self):
    round_1 = load_json("standard-corporate-role/round-1.json")
    assert round_1["stage"] == "round_1_waiting_for_user"
    assert round_1["selected_seeds"] == []
    assert round_1["vertical_branches"] == []
```

- [ ] **Step 3: Run tests and verify RED**

Run: `python3 -m unittest international-law-search.tests.test_user_centered_e2e -v`

Expected: FAIL because the new fixtures do not exist.

- [ ] **Step 4: Build the machine-verifiable fixtures**

The quick fixture must contain 10–15 lightweight ledger records, explicit scope approval, and an upgrade checkpoint. The standard corporate-role fixture must show ambiguous intake, a bounded breadth result, an empty seed selection at the mandatory pause, a later user decision selecting only named seeds, and a depth round that respects those choices.

- [ ] **Step 5: Migrate the Nicaragua fixture as deep-audit regression**

Preserve its six sources, three verified canonical relations, access evidence, and stopped-because-budget statement. Convert access fields and relation families without changing the historical factual metadata.

- [ ] **Step 6: Run all E2E tests and commit**

Run: `python3 -m unittest international-law-search.tests.test_user_centered_e2e international-law-search.tests.test_nicaragua_e2e_fixture -v`

Expected: PASS.

```bash
git add international-law-search/tests/test_user_centered_e2e.py international-law-search/tests/fixtures/user-centered international-law-search/tests/test_nicaragua_e2e_fixture.py docs/superpowers/evals/2026-09-17-international-law-search-e2e.md docs/superpowers/evals/fixtures/nicaragua-e2e
git commit -m "test: add interactive search end-to-end fixtures"
```

## Task 11: Complete Skill Routing, Metadata, and Package Validation

**Files:**
- Modify: `international-law-search/SKILL.md`
- Modify: `international-law-search/agents/openai.yaml`
- Modify: `international-law-search/references/intake-and-approval.md`
- Modify: `international-law-search/references/source-strategy.md`
- Modify: `international-law-search/tests/test_skill_contract.py`
- Modify: `international-law-search/tests/test_benchmarks.py`

- [ ] **Step 1: Write the final routing assertions**

```python
def test_entrypoint_routes_references_by_stage_and_mode(self):
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "references/modes-and-rounds.md" in text
    assert "references/source-ledger.md" in text
    assert "references/multilingual-retrieval.md" in text
    assert "deep-audit" in text.lower()


def test_default_prompt_describes_user_controlled_research_assistance(self):
    text = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
    assert "user" in text.lower()
    assert "research" in text.lower()
    assert "without substantive legal synthesis" not in text
```

- [ ] **Step 2: Run contract tests and verify any remaining RED failures**

Run: `python3 -m unittest international-law-search.tests.test_skill_contract international-law-search.tests.test_benchmarks -v`

Expected: remaining failures identify obsolete version-1 routing, report order, or no-synthesis assertions.

- [ ] **Step 3: Finish concise progressive-disclosure routing**

Keep shared principles and mode choice in `SKILL.md`. Load multilingual, graph, reporting, or deep-audit details only when the selected mode and stage need them. Remove compatibility routers only after no file points to superseded content.

- [ ] **Step 4: Update UI metadata**

Use a default prompt that asks the skill to help clarify and progressively retrieve an international-law research topic while preserving user choices. Keep automatic invocation enabled.

- [ ] **Step 5: Run the official validator and contract suite**

Run: `python3 /Users/kaiqiangzhang/.codex/skills/.system/skill-creator/scripts/quick_validate.py international-law-search`

Expected: `Skill is valid!`

Run: `python3 -m unittest discover -s international-law-search/tests -v`

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add international-law-search/SKILL.md international-law-search/agents/openai.yaml international-law-search/references international-law-search/tests/test_skill_contract.py international-law-search/tests/test_benchmarks.py
git commit -m "refactor: finalize user-centered search skill"
```

## Task 12: Independent Forward Evaluation and Deployment

**Files:**
- Create: `docs/superpowers/evals/2026-09-18-international-law-search-redesign-forward.md`
- Modify only if evaluation proves a concrete gap: files named in Tasks 2–11

- [ ] **Step 1: Run independent forward evaluations**

Dispatch fresh evaluators with only the finished skill and realistic prompts for:

- The ambiguous corporate-role request.
- A 30-minute quick bibliography followed by an upgrade.
- A Chinese and English standard search with institutional database access.
- A retrieval archive request under pressure to synthesize.
- A research report request under pressure to choose a thesis.
- A deep-audit local-seed project containing published PDFs and private notes.

Evaluators must inspect user-visible behavior and produced artifacts, not merely search for phrases in `SKILL.md`.

- [ ] **Step 2: Record failures and close only demonstrated gaps**

Write the prompt, observed behavior, pass/fail judgment, and any minimal corrective change in `docs/superpowers/evals/2026-09-18-international-law-search-redesign-forward.md`. If a correction is made, rerun the affected scenario and the full test suite.

- [ ] **Step 3: Run final verification**

Run: `python3 -m unittest discover -s international-law-search/tests -v`

Expected: all tests PASS.

Run: `python3 /Users/kaiqiangzhang/.codex/skills/.system/skill-creator/scripts/quick_validate.py international-law-search`

Expected: `Skill is valid!`

Run: `git diff --check`

Expected: no output.

- [ ] **Step 4: Commit evaluation-supported refinements**

```bash
git add international-law-search docs/superpowers/evals/2026-09-18-international-law-search-redesign-forward.md
git commit -m "test: verify user-centered international law search"
```

- [ ] **Step 5: Push the repository and refresh the global installation**

Push the verified commits to the configured `origin/master`. Reinstall or synchronize only the `international-law-search` folder into `/Users/kaiqiangzhang/.codex/skills/international-law-search`, then compare the installed directory with the repository source and rerun the official validator against the installed copy.

Expected: remote push succeeds, source and installed skill match, and both validations pass.
