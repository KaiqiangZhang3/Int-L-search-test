# Retrieval Branch Brief

## Approved assignment

- Project mode (`quick`, `standard`, or `deep-audit`): {{mode}}
- Current stage: {{stage}}
- Approved question: {{question}}
- Approved scope and exclusions: {{scope}}
- Branch ID: {{branch_id}}
- Source track (`primary`, `secondary`, or `mixed`): {{source_track}}
- Retrieval mode (`horizontal` or `vertical`): {{retrieval_mode}}
- Assignment: {{assignment}}
- Platforms, languages, source types, and period: {{surfaces}}
- Branch budget: {{budget}}
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

Initial Stage 1 assignments must be horizontal. Do not trace references,
footnotes, cited-by results, or lateral relations during Stage 1. A later
vertical assignment requires an approved seed, direction, and budget. If a
limit is reached, return the open path with `budget_paused`; do not continue.

## Required contracts

`$SKILL_ROOT` means the directory containing `SKILL.md`.

- Quick or standard lightweight record:
  `$SKILL_ROOT/schemas/source-ledger-record.schema.json`
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
discovery provenance, access attempts, reader descriptions, inclusion
reasons, coverage additions, and unresolved issues. Do not construct edges.

For deep-audit mode, return candidate nodes. If `graph_enabled=true`, optional
edges may also be returned with `record_scope=candidate` and
`status=candidate`. Each endpoint may use a known canonical ID from this brief
or a `candidate_id submitted in the same return`; the main agent resolves it.
Put query, platform, seed, footnote, bibliography, and subagent discovery in
source provenance, never in `discovered_from` edges.

Always return failures, metadata conflicts, access gaps, remaining high-value
paths, and actual budget use. Do not edit the shared ledger or canonical
corpus, merge identities, select final seeds, verify edges, assign final
collection tiers, decide saturation, or produce user-facing conclusions. Do
not fabricate records, call unread material full text, resolve scholarly
disputes, choose an argument, or draft academic prose.
