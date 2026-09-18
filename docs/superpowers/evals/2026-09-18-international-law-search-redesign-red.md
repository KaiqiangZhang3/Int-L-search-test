# International Law Search User Centered Red Baseline

## Purpose

This RED baseline converts the real-use findings in `user_feedback.docx` into observable behavior contracts before changing the skill implementation. The source request concerned the role of corporations in public international law and possible corporate-governance connections. The document concludes that the current skill behaves primarily as an audit-oriented corpus builder rather than a user-participatory academic research assistant.

The benchmark language below paraphrases the feedback document. It does not invent user quotations or claim that the benchmark prompts are verbatim transcripts.

## Real Use Failures Captured

The feedback identifies the following behavior failures that the new fixtures preserve:

- The ambiguous corporate-role topic was expanded across distinct questions such as legal personality, direct obligations, business and human rights, investment law, global governance, and corporate governance without enough prior clarification.
- A preselected search plan was offered for binary approval instead of allowing the user to shape the question through a research interview.
- The user first saw substantive results only after 72 sources had been collected, so there was no useful breadth-stage choice point.
- The model selected the vertical-tracing seeds, including Ahlborn, the UN Guiding Principles, and Barcelona Traction, rather than presenting a seed menu for user confirmation.
- The 45-70 source budget did not expose round allocation, platforms, queries, full-text reviews, seed count, per-seed depth, or mandatory pause points.
- The report foregrounded stable IDs, machine state, relationship edges, and coverage tables before field structure, debates, and reading priorities.
- Chinese retrieval functioned mainly as a small addition to English searching rather than as an independent branch with local terminology, platforms, purpose, and budget.
- The universal prohibition on literature-review synthesis conflicted with the user's need for a cited, descriptive research report.
- Even a small request for roughly a dozen sources required plans, state, schemas, branch reports, JSONL validation, a graph, and machine exports.

## New Fixture Coverage

Eight fixtures in `international-law-search/tests/fixtures/benchmark_cases.json` now define the approved mode, prompt, required observable behavior, and prohibited behavior:

1. `vague-corporate-role-readiness`
2. `standard-round-1-checkpoint`
3. `user-selected-seeds`
4. `quick-mode-upgrade`
5. `independent-chinese-branch`
6. `reader-first-report`
7. `retrieval-archive-boundary`
8. `research-report-boundary`

The archive and report cases intentionally use the same standard-interactive mode. Their different synthesis rules are output contracts, not separate retrieval systems.

## RED Test Evidence

Command:

```text
python3 -m unittest international-law-search.tests.test_modes_and_rounds international-law-search.tests.test_skill_contract -v
```

Result on 2026-09-18:

```text
Ran 23 tests in 0.004s
FAILED (failures=8)
```

The two fixture-shape tests passed. The eight implementation-contract failures are expected and identify missing redesign behavior:

| Failing test | Current behavior contradicted by the real-use feedback | Required new behavior |
| --- | --- | --- |
| `test_standard_mode_requires_user_seed_selection_before_depth` | The search accumulated 72 sources before the first substantive user choice, and vertical tracing had already been shaped by the model. | Stage 1 must stop after bounded breadth discovery; Stage 2 cannot begin until the user selects or confirms seeds. |
| `test_depth_round_honors_branch_and_source_decisions` | The model selected Ahlborn, the UN Guiding Principles, and Barcelona Traction as seeds. | Trace only user-confirmed seeds, honor deleted branches, and allow review without tracing. |
| `test_quick_mode_is_upgradeable_without_restart` | Small searches were required to create the same state, schemas, graph, logs, and machine exports as deep projects. | Quick mode omits mandatory graph and audit infrastructure, then reuses its existing ledger if the user upgrades. |
| `test_rounds_expose_multidimensional_budget_and_actual_use` | The budget was only a broad 45-70 source target, without round, platform, query, review, seed, depth, language, or pause allocations. | Each round exposes applicable budget dimensions and reports planned-versus-actual use; a budget pause is not saturation evidence. |
| `test_closure_rules_preserve_user_control` | The workflow largely completed retrieval before asking the user what to do, and lacked a concrete control for saying the result was sufficient. | Quick scope approval can authorize its bounded delivery, while standard and deep-audit closure remains an explicit user decision, including "stop and deliver." |
| `test_intake_compatibility_file_routes_to_mode_contract` | The old intake file constructs one full written plan and asks for binary approval. | Intake becomes a compatibility route to adaptive readiness and round-specific scope approval. |
| `test_references_are_routed_from_skill` | The entrypoint routes directly into the audit-oriented plan, source strategy, graph, and delivery stack. | The entrypoint routes through the mode-and-round contract before loading only the references needed for the current stage. |
| `test_scope_approval_survives_urgency_and_modes_preserve_boundaries` | The skill has one retrieval-only boundary and categorically prohibits literature-review synthesis. | The user chooses an upgradeable mode; a retrieval archive remains non-synthetic, while a research report may use cited descriptive synthesis without choosing a thesis or writing argumentative prose. |

Five tests fail with the explicit message `The public mode-and-round contract is missing` because `references/modes-and-rounds.md` does not yet exist. This is the intended missing public contract for the next vertical slice, not an environmental or dependency failure.

## RED Scope

This baseline changes tests and fixtures only. It does not add mode routing, round execution, templates, schemas, or skill behavior. Passing the new tests requires implementing the missing user-centered contract rather than weakening the assertions.
