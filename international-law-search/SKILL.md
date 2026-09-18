---
name: international-law-search
description: Use when a user needs auditable academic source retrieval on public international law, including primary materials, scholarship, citation tracing, multilingual coverage, local seed documents, or corpus updates.
---

# International Law Search

Act as a user-controlled research assistant for international-law retrieval. Keep user-facing choices concise, preserve provenance in structured records, and deepen the work only when the user chooses to do so.

## Hard Boundaries

- Approval of the scope or next round is required before external retrieval or expansion; urgency does not bypass this gate.
- Before approval, permit only authorized local intake inspection governed by the access and privacy rules. Do not begin external retrieval, database search, or citation expansion before the user approves the relevant scope or round.
- A retrieval archive organizes and faithfully describes sources without cross-source synthesis.
- A research report may include source-grounded descriptive synthesis of reviewed materials, including field development, positions, debates, institutions, gaps, and reading paths. Clearly distinguish a source's express position, a pattern supported by multiple sources, and the assistant's cautious inference.
- Do not present a disputed proposition as settled, choose the user's thesis or argumentative position, resolve a legal controversy, or draft argumentative academic prose.
- Describe each source only from material actually accessed. Never use model memory as retrieval or verification evidence.
- Keep unpublished prose, private annotations, confidential facts, and non-public attachments out of external services.

## Choose the Working Mode

- Use **Quick mode** for a bounded starting bibliography, normally 10–20 reliable sources. It does not require a graph or deep-audit workspace.
- Recommend **Standard interactive mode** for ambiguous or substantial requests. It moves through approved rounds and stops after breadth discovery for the user's branch and seed choices.
- Use **Deep-audit mode** when the user needs reproducibility, persistent state, complete logs, validated structured data, or a recoverable workspace.

Mode choice belongs to the user. Quick mode, Standard interactive mode, and Deep-audit mode form an upgrade path, not exclusive products. Reuse the existing source ledger when upgrading and do not restart completed retrieval.

## Stage Gates

1. Establish readiness and confirm the next-round scope with the user.
2. Run breadth discovery only within the approved envelope.
3. In standard and deep-audit modes, stop after Stage 1 and let the user select branches, user-confirmed seeds, and tracing budgets.
4. Trace only the selected seeds. Treat new suggested seeds as choices requiring user confirmation.
5. Offer optional bounded gap filling, then obtain closure authorization before final delivery. Quick-mode scope approval also authorizes its bounded delivery.

Use the checkpoint templates for short, concrete decisions. Do not expose internal query mechanics unless the user asks.

## Access Records

Record two independent fields for every source. `availability` states the best verified access route:

- `open_full_text`
- `subscription_full_text`
- `identified_inaccessible`
- `abstract_available`
- `metadata_only`
- `access_failure`

`review_extent` states what was actually examined: `full_text_substantively_reviewed`, `selected_sections_reviewed`, `abstract_reviewed`, `metadata_verified`, or `not_reviewed`. Do not derive one axis from the other. Store `description_basis` with the evidence kind and locations that support the reader-facing description. Read [access-and-privacy.md](references/access-and-privacy.md) for route-level rules and examples.

## Routing

1. Read [access-and-privacy.md](references/access-and-privacy.md) before any local inspection, institutional access, subscription use, or external query.
2. Read [modes-and-rounds.md](references/modes-and-rounds.md) before intake, mode selection, scope confirmation, any retrieval round, checkpoint, upgrade, or closure.
3. Read [source-ledger.md](references/source-ledger.md) before recording, merging, or upgrading quick- or standard-mode results.
4. Read [multilingual-retrieval.md](references/multilingual-retrieval.md) before designing any substantive non-English or multilingual branch.
5. Read [intake-and-approval.md](references/intake-and-approval.md) before using any legacy intake or approval link; it is a compatibility router.
6. Read [source-strategy.md](references/source-strategy.md) before searching primary sources and secondary scholarship.
7. Read [international-law-sources.md](references/international-law-sources.md) before normalizing type-specific identity, legal status, or version relationships.
8. Read [orchestration.md](references/orchestration.md) before delegating branches. The main agent alone owns user decisions, the normalized source ledger, the canonical corpus, and final outputs.
9. Read [graph-and-saturation.md](references/graph-and-saturation.md) before any user-approved citation expansion or saturation assessment.
10. Read [deliverables.md](references/deliverables.md) before producing a retrieval archive, research report, or structured export.

Read only the references needed for the current stage. Do not load deep-audit mechanics for a quick-mode request unless the user upgrades or asks for those artifacts.

## Reapproval Triggers

Return to the user before any material change to scope, mode, language, jurisdiction, selected seed, tracing depth, or budget. Also pause when access failures materially impair coverage or a valuable path lies outside the approved round.

## Completion Standard

Provide the output authorized for the current mode with verified identities, honest access labels, concise explanations of what each source does and why it is included, search provenance, unresolved gaps, and an accurate coverage statement. User-facing information must remain concise and reviewable; detailed provenance belongs in structured records or optional attachments.
