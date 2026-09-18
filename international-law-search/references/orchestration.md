# Retrieval Orchestration

## When to delegate

Keep a small, single-surface search in the main agent. Use subagents when the
approved plan contains independent surfaces that benefit from parallel or
specialized retrieval, such as different legal subquestions, source types,
platforms, languages, or citation branches.

Each branch has two independent dimensions:

- `source_track`: `primary`, `secondary`, or `mixed`.
- `retrieval_mode`: `horizontal` or `vertical`.

Horizontal and vertical retrieval modes may run at the same time:

- **Horizontal discovery** searches across approved platforms, databases,
  languages, source classes, and query variants. Its purpose is breadth and
  coverage comparison.
- **Vertical tracing** follows backward citations, forward citers, and lateral
  relationships from a specified seed or core node. Its purpose is to expose
  the source's citation neighborhood and promising paths at the current depth.

Do not delegate merely to increase agent count. Define branches so that each
has an identifiable surface, useful independent output, and limited overlap.

## Branch contract

`$SKILL_ROOT` means the directory containing `SKILL.md`. Create every
delegated task from `$SKILL_ROOT/templates/subagent-brief.md`. Give the
subagent:

- The approved retrieval question, scope, and exclusions.
- Its `source_track`, `retrieval_mode`, and horizontal surface or vertical
  seed and tracing direction.
- Approved platforms, languages, source types, and time range.
- Known canonical IDs and aliases to reduce duplicate retrieval.
- Current depth and maximum authorized depth.
- `$SKILL_ROOT/schemas/candidate-source-record.schema.json` and
  `$SKILL_ROOT/schemas/edge-record.schema.json`.
- Required access labels, provenance fields, and evidence rules.
- Any local-material privacy restrictions that apply to the branch.

A subagent returns only candidate nodes conforming to
`$SKILL_ROOT/schemas/candidate-source-record.schema.json` and candidate edges
conforming to `$SKILL_ROOT/schemas/edge-record.schema.json` with `status` set
to `candidate` and `record_scope` set to `candidate`. It also returns exact
discovery provenance, evidence locations, access attempts, unresolved
citations, coverage additions, and remaining high-value branches. It must not
edit the canonical corpus, declare an edge verified, assign a collection tier,
decide saturation, or publish a user-facing conclusion. Each candidate edge
endpoint may independently use a known canonical ID supplied in the brief or a
`candidate_id submitted in the same return`. One endpoint may be canonical
while the other is a candidate.

Subagents must not fabricate records, describe unread material as full text,
synthesize legal rules, resolve scholarly disputes, choose an argument, or
draft academic prose.

## Main-agent ownership

The main agent alone owns the canonical corpus and graph. After each branch
returns, the main agent:

1. Validates nodes against the candidate schema and edges against the edge
   schema.
2. Normalizes identities and merges duplicates by identifiers and metadata.
3. Converts accepted candidates into canonical records conforming to
   `$SKILL_ROOT/schemas/source-record.schema.json`, assigns both canonical
   `relevance and collection_tier`, and resolves each edge endpoint
   independently. It preserves a known canonical ID and remaps a
   same-return `candidate_id` to its new canonical ID.
4. Preserves conflicting metadata and flags unresolved identity questions for
   human review.
5. Checks edge evidence before changing an edge from `candidate` to
   `verified`. It normalizes inverse `cited_by` submissions to `cites`, sets
   accepted graph records to `record_scope=canonical`, and never stores
   `cited_by` in the canonical graph.
6. Confirms every accepted canonical record has both `relevance` and
   `collection_tier` before running round metrics, then records round evidence,
   updates branch state, and updates cumulative searched and unsearched
   coverage in project state.
7. After each canonical merge and at every checkpoint, runs
   `$SKILL_ROOT/scripts/validate_corpus.py` with the canonical source and edge
   JSONL paths. A failed validation blocks metrics, state advancement, and
   export until the line-specific errors are corrected. Candidate edges stay
   outside these final-corpus files.
8. Decides, with a written reason, whether to continue, reassign, pause for
   reapproval, or stop.

No subagent maintains a competing final graph. If multiple branches return the
same item, retain their separate discovery histories while merging the item
into one canonical node.

## Authorization and depth gate

Before dispatching a vertical branch, compare its proposed depth with the
branch's maximum authorized depth. If the next round would exceed the
authorized depth, do not dispatch it. Save the promising branch and ask the
user to reapprove an expanded depth or resource budget. Continuing high-value
discoveries explain why expansion may be useful; they do not override the
approval boundary.

Also seek reapproval for material scope drift, a necessary new language or
jurisdiction, a serious access gap, or exhaustion of the approved budget
before the corpus approaches saturation.

## Failure isolation and resumption

A failed branch must not discard completed work from other branches. Record
its last successful checkpoint, attempted queries or paths, platform errors,
and unresolved items. Retry the branch, reassign it, or disclose the remaining
gap.

If a database is unavailable, log the failure and try authoritative public
alternatives within the approved scope. Preserve an unresolvable citation as
a candidate record with its original citation text and provenance. After an
interruption, resume only unfinished branches from saved state.
