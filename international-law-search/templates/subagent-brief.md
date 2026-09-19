# Retrieval Branch Brief

## Approved assignment

- Project mode (`quick`, `standard`, or `deep-audit`): {{mode}}
- Round ID and type: {{round_id_and_type}}
- Approved question: {{question}}
- Approved scope and exclusions: {{scope}}
- Branch ID: {{branch_id}}
- Source track (`primary`, `secondary`, or `mixed`): {{source_track}}
- Retrieval mode (`horizontal` or `vertical`): {{retrieval_mode}}
- Assignment: {{assignment}}
- Platforms, languages, source types, and period: {{surfaces}}
- Three-axis branch budget: discovery {{discovery_cap}}; acquisition {{acquisition_cap}}; substantive review {{review_cap}}
- Query, time, platform, language, and depth limits: {{other_budget_limits}}
- Approved seed and direction, if vertical: {{seed_and_direction}}
- Authorization decision ID, if vertical: {{authorization_decision_id}}
- Known canonical IDs and aliases: {{known_ids}}
- Current and maximum authorized depth: {{depth}}
- Graph enabled: {{graph_enabled}}
- Local-material privacy constraints: {{privacy_constraints}}

For every local-seed discovery fragment, declare
`privacy_classification` as `public_citation_extract` or
`private_note_reference` and declare `externalizable` as a boolean. A
`private_note_reference` must remain `externalizable=false`. Keep its content
and path local; use only an opaque local ID in internal coordination. Never
place non-externalizable content, a `file://` URI, or an absolute local path in
this brief, a query, or a return package.

The round specification controls whether work is horizontal, vertical, or
review-only. A vertical assignment requires an approved seed, direction, and
budget. A breadth assignment does not authorize hidden footnote or cited-by
tracing. If a limit is reached, return the open path with `budget_paused`; do
not continue.

## Required contracts

`$SKILL_ROOT` means the directory containing `SKILL.md`.

- Quick or standard lightweight record:
  `$SKILL_ROOT/schemas/source-ledger-record.schema.json`
- Candidate claim evidence:
  `$SKILL_ROOT/schemas/claim-record.schema.json`
- Round and budget contract:
  `$SKILL_ROOT/schemas/round-record.schema.json`
- Deep-audit candidate node:
  `$SKILL_ROOT/schemas/candidate-source-record.schema.json`
- Deep-audit optional edges, only when graph support is enabled:
  `$SKILL_ROOT/schemas/edge-record.schema.json`
- Access and privacy policy:
  `$SKILL_ROOT/references/access-and-privacy.md`
- Outbound privacy validator:
  `$SKILL_ROOT/scripts/validate_export_manifest.py`
- Graph evidence rules:
  `$SKILL_ROOT/references/graph-and-saturation.md`

## Return package

For quick or standard mode, return concise candidate ledger rows with exact
discovery provenance, acquisition and access attempts, reader descriptions,
inclusion reasons, coverage additions, and unresolved issues. When the
assignment examines a proposition, also return candidate claim evidence with
the source key, evidence function, exact locator, review basis, and whether it
supports, qualifies, or contradicts the proposition. Do not assign final claim
status or construct edges.

For deep-audit mode, return candidate nodes. If `graph_enabled=true`, optional
edges may also be returned with `record_scope=candidate` and
`status=candidate`. Each endpoint may use a known canonical ID from this brief
or a `candidate_id submitted in the same return`; the main agent resolves it.
Put query, platform, seed, footnote, bibliography, and subagent discovery in
source provenance, never in `discovered_from` edges.

Always return failures, metadata conflicts, access gaps, remaining high-value
paths, and actual use on all three budget axes. Do not edit shared source,
claim, round, or terminology ledgers; merge identities; select final seeds;
verify edges; assign final claim status; decide saturation; or produce
user-facing conclusions. Do not fabricate records, call unread material full
text, resolve scholarly disputes, choose an argument, or draft academic prose.
