# Retrieval Orchestration

## Delegate only independent work

Keep a small, single-surface search in the main agent. Delegate when approved
languages, platforms, source types, legal subquestions, or citation branches
form independent assignments. Every branch records its mode, stage, scope,
budget, exclusions, and expected return contract.

Initial Stage 1 breadth discovery is horizontal only and must not launch vertical tracing,
including hidden reference-list or cited-by expansion. Stop
after the breadth result so the user can choose themes, approved seeds, and a
tracing budget. After that approval, horizontal gap filling and vertical
tracing may run concurrently within the selected scope.

Do not delegate merely to increase agent count. A branch needs a distinct
surface, independently useful output, and limited overlap.

## Mode-aware return contracts

Quick and standard branches return concise candidate rows compatible with
`$SKILL_ROOT/schemas/source-ledger-record.schema.json`. They include identity,
availability, review extent, reader description, inclusion reason, discovery
provenance, access attempts, and unresolved issues. They do not need canonical
IDs, candidate-edge lifecycles, corpus-wide validation, or a graph.

Deep-audit branches return candidate nodes conforming to
`$SKILL_ROOT/schemas/candidate-source-record.schema.json`. When
`graph_enabled=true`, a branch may also return optional edges conforming to
`$SKILL_ROOT/schemas/edge-record.schema.json`, with `record_scope=candidate`
and `status=candidate`. When graph support is disabled, it returns no edge
file. Retrieval provenance belongs in each source's `discovery_history`, not
in an edge.

For every mode, provide exact discovery provenance, access attempts, coverage
additions, unresolved citations, metadata conflicts, failures, and remaining
high-value paths. Never describe unread material as full text.

## Branch brief

Create delegated work from `$SKILL_ROOT/templates/subagent-brief.md`. Supply:

- The approved question, scope, exclusions, mode, and current stage.
- `source_track`: `primary`, `secondary`, or `mixed`.
- `retrieval_mode`: `horizontal` or `vertical`.
- Approved platforms, languages, source types, period, and branch budget.
- For a vertical branch, the approved seed, direction, current depth, and
  maximum authorized depth.
- Known canonical IDs and aliases when deep-audit deduplication applies.
- The applicable lightweight or deep-audit schema contract.
- Access, evidence, and local-material privacy restrictions.

A vertical assignment without an approved seed and budget is invalid. A
subagent cannot expand scope, choose final seeds, assign collection tiers,
declare an edge verified, decide saturation, or publish a user-facing
conclusion.

Persist every user choice in `decision_log`. Each vertical branch must carry
an `authorization_decision_id` pointing to its `approve_trace` decision, with
the same branch, seed, direction, and item, review, depth, and time budget.
Store that mapping in the branch's `approved_budget`. Use
`$SKILL_ROOT/scripts/checkpoint_state.py` for breadth pauses, seed approvals,
budget pauses, failures, and resumptions so state replacement is atomic and
illegal transitions leave the prior checkpoint intact.

A budget pause or failure checkpoint is incomplete without the branch cursor,
pending and unresolved items, platform errors, open paths, status reason and
time, and a complete round-evidence record. Write all of them in the same
atomic replacement so a resumed branch cannot observe a newer status with an
older cursor.

## Main-agent ownership

The main agent owns user decisions and the normalized source ledger in every
mode. In deep-audit mode it also owns the canonical corpus and, when enabled,
the single canonical graph. It:

1. Validates each return against the contract named in the brief.
2. Normalizes identities, preserves separate discovery histories, and merges
   duplicates without discarding attributed conflicts.
3. In deep-audit mode, converts accepted candidates to canonical source
   records and assigns `relevance and collection_tier` before running round metrics.
4. Resolves each edge endpoint independently. It preserves a known canonical
   ID and remaps a `candidate_id submitted in the same return` to the accepted
   canonical ID.
5. Stores only `citing_node cites cited_node` for citations. It may normalize
   a candidate `cited_by` lead to that direction, but never stores `cited_by`
   as a canonical edge.
6. Verifies edge evidence, records round evidence and budget status, and
   updates cumulative searched and unsearched coverage.
7. After each canonical merge, runs
   `$SKILL_ROOT/scripts/validate_corpus.py` on canonical sources, passing
   `--state` and passing `--edges` only when graph support is enabled.
8. Repeats canonical validation at every checkpoint before presenting counts
   or coverage claims to the user.
9. Gives the user concrete choices to continue, redirect, upgrade, pause, or
   close.

No subagent maintains a competing final ledger, corpus, or graph.

## Authorization, failure, and resumption

Never cross an approved depth, item cap, platform budget, or time budget. A
branch that reaches its cap becomes `budget_paused`; preserve its open paths
and ask the user whether to extend it. Budget exhaustion is not saturation.

Record the last successful checkpoint, attempted queries or paths, platform
errors, and unresolved items. A failed branch must not discard completed work
elsewhere. Retry, reassign, or disclose the gap within the approved scope, and
resume only unfinished work after interruption.
