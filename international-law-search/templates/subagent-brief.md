# Retrieval Branch Brief

## Approved assignment

- Approved question: {{question}}
- Approved scope and exclusions: {{scope}}
- Branch ID: {{branch_id}}
- Source track (`primary`, `secondary`, or `mixed`): {{source_track}}
- Retrieval mode (`horizontal` or `vertical`): {{retrieval_mode}}
- Assignment: {{assignment}}
- Platforms, languages, source types, and period: {{surfaces}}
- Vertical seed and direction, if applicable: {{seed_and_direction}}
- Known canonical IDs and aliases: {{known_ids}}
- Current depth: {{current_depth}}
- Maximum authorized depth: {{maximum_authorized_depth}}
- Local-material privacy constraints: {{privacy_constraints}}

If the proposed next depth exceeds the maximum authorized depth, do not
continue. Return the open branch and evidence supporting a reapproval request.

## Required contracts

`$SKILL_ROOT` means the directory containing `SKILL.md`.

- Candidate node schema: `$SKILL_ROOT/schemas/candidate-source-record.schema.json`
- Edge schema: `$SKILL_ROOT/schemas/edge-record.schema.json`
- Access and privacy policy: `$SKILL_ROOT/references/access-and-privacy.md`
- Graph evidence rules: `$SKILL_ROOT/references/graph-and-saturation.md`

## Return package

Return only:

1. Candidate nodes conforming to the candidate node schema. Do not assign a
   canonical ID or collection tier.
2. Candidate edges conforming to the edge schema; keep `status` as
   `candidate` even when evidence is supplied. Each `source_id` and
   `target_id` may independently reference either a known canonical ID from
   this brief or a `candidate_id submitted in the same return`. The main agent
   resolves each endpoint and remaps candidate IDs.
3. Exact discovery provenance and edge evidence locations.
4. Access attempts and accurate access labels.
5. Newly covered source classes, themes, languages, and platforms.
6. Unresolved citations, metadata conflicts, failures, and untraced
   high-value branches.

Do not edit the canonical corpus, merge identities, declare edges verified,
assign final collection tiers, decide saturation, or produce final
user-facing conclusions. Do not synthesize legal rules, resolve scholarly
disputes, choose an argument, draft academic prose, fabricate records, or call
unread material full text.
