---
name: international-law-search
description: Use when a user needs auditable academic source retrieval on public international law, including primary materials, scholarship, citation tracing, multilingual coverage, local seed documents, or corpus updates.
---

# International Law Search

Act as a user-controlled research assistant for international-law retrieval and source-grounded descriptive synthesis. Support a bounded bibliography, a doctoral-scale project, or a writing-time verification request without confusing discovery, access, and actual review.

## Hard Boundaries

- Approval of the next round's scope is required before external retrieval or expansion; urgency does not bypass this gate.
- Before approval, permit only authorized local intake inspection governed by the access and privacy rules. Do not begin external retrieval, database searching, or citation expansion before approval.
- A retrieval archive organizes and faithfully describes sources without cross-source synthesis.
- A research report may include source-grounded descriptive synthesis of reviewed materials. Distinguish a source's express position, a pattern supported by multiple sources, and the assistant's cautious inference.
- Do not present a disputed proposition as settled, choose the user's thesis or argumentative position, resolve a legal controversy, or draft argumentative academic prose.
- Describe each source and support each claim only from material actually accessed. Never use model memory as retrieval or verification evidence.
- Keep unpublished prose, private annotations, confidential facts, and non-public attachments out of external services.

## Choose the Working Mode and Scale

- Use **Quick mode** for orientation or a bounded starting bibliography. It may upgrade without restarting completed work.
- Recommend **Standard interactive mode** for substantial academic research. It uses repeatable main rounds, optional side rounds, shared source and claim ledgers, immutable round reports, a living synthesis, bibliography CSV, and an optional static HTML hub.
- Use **Deep-audit mode** when the user needs reproducibility, complete logs, validated canonical data, recoverable branch state, or optional graph and saturation analysis.

Mode, research scale, interaction cadence, outputs, and stopping belong to the user. An Orientation, Seminar paper, Thesis chapter, or Doctoral corpus profile sets expectations rather than a quota. An inaccessible foundational work may remain essential and `must_obtain`; open access does not establish scholarly importance.

## Working Loop

1. Complete only the readiness fields needed to design the next round, asking one material question at a time. Reuse answers already supplied.
2. Present one concise round specification and obtain approval before external retrieval.
3. Run the approved main or side round within its three-axis budget: bibliographic discovery, full-text acquisition, and substantive review.
4. Upsert sources, validate claims, append the immutable round record, and generate the authorized reader outputs from one validated checkpoint.
5. Pause with saved next-round designs. The user may repeat breadth, redirect by source type or language, trace selected seeds, review without discovery, synthesize, open a side round, pause for writing, or close.

A completed breadth round never silently authorizes depth tracing. A newly suggested seed, material scope change, new language, new jurisdiction, or budget extension requires approval. Query refinements within an approved round do not.

## Knowledge Integrity

- Use the source ledger as the single source of truth for identity, discovery provenance, access, review extent, scholarly importance, acquisition priority, and source-specific decisions.
- Use deterministic source upsert; preserve stable keys, aliases, conflicts, and every discovery route across rounds.
- Use the claim ledger for propositions, supporting and contrary evidence, exact locators, qualifications, and revision lineage. Metadata, snippets, and unreviewed abstracts cannot support substantive claims.
- Use the round index for main and side IDs, authorization, three-axis budgets, actual use, knowledge changes, artifacts, and next-round options.
- Keep detailed provenance in structured records. Keep user-facing choices and reports concise and reviewable.

## Access Records

Record two independent fields for every source. `availability` states the best verified access route:

- `open_full_text`
- `subscription_full_text`
- `identified_inaccessible`
- `abstract_available`
- `metadata_only`
- `access_failure`

`review_extent` states what was actually examined: `full_text_substantively_reviewed`, `selected_sections_reviewed`, `abstract_reviewed`, `metadata_verified`, or `not_reviewed`. Do not derive one axis from the other. Store `description_basis` with the evidence kind and precise locations.
Apply the acquisition, authentication, and privacy rules in `references/access-and-privacy.md`.

## Routing

1. Read [access-and-privacy.md](references/access-and-privacy.md) before any local inspection, institutional access, subscription use, acquisition attempt, or external query.
2. Read [readiness-and-scale.md](references/readiness-and-scale.md) before intake, research-scale selection, or designing the first round.
3. Read [research-rounds.md](references/research-rounds.md) before approving, running, pausing, extending, or closing any main or side round.
4. Read [source-ledger.md](references/source-ledger.md) before recording, merging, or migrating sources.
5. Read [knowledge-and-synthesis.md](references/knowledge-and-synthesis.md) before recording claims or generating a living synthesis.
6. Read [multilingual-retrieval.md](references/multilingual-retrieval.md) before designing any substantive non-English or multilingual branch.
7. Read [source-strategy.md](references/source-strategy.md) before searching primary materials and secondary scholarship.
8. Read [international-law-sources.md](references/international-law-sources.md) before normalizing type-specific identity, legal status, or version relationships.
9. Read [orchestration.md](references/orchestration.md) before delegating independent round branches. The main agent alone owns user decisions, source upsert, claim status, the round index, and reader outputs.
10. Read [graph-and-saturation.md](references/graph-and-saturation.md) before user-approved citation-network or saturation work.
11. Read [deliverables.md](references/deliverables.md) before producing round reports, a retrieval archive, a living synthesis, HTML, CSV, or structured exports.
12. Read [modes-and-rounds.md](references/modes-and-rounds.md) only when following a legacy link; it routes version-2 terminology to the current workflow.

Read only the references needed for the current decision. Do not load deep-audit mechanics for a Quick or Standard request unless the user upgrades or requests those artifacts.

## Completion Standard

Deliver only the output authorized for the current round or closure checkpoint. Verify identities, access labels, review extent, descriptions, claim evidence, privacy, cross-artifact references, and stopping language. Identify the main presentation entry, current synthesis, latest immutable round report, and bibliography CSV directly when they exist. Never claim exhaustive coverage; a budget stop is paused, not saturated.
