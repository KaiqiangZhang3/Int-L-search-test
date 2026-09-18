# Deliverables

Generate every deliverable from the canonical corpus, graph, and project state. Do not maintain a separate hand-edited reader list. Reader-facing and structured files must represent the same corpus at the same export checkpoint. Every displayed source must retain its stable source ID; identify a relationship by its endpoint IDs, relation, and status because the edge schema has no relationship ID.

## Select outputs

Use the formats approved in the search plan. Offer the reader-facing report as Word, Markdown, or HTML, as selected by the user. Keep the report concise enough for human review; place operational detail in the structured layer.

The structured layer may include:

- Source records as JSONL or CSV.
- Edge records or other graph data.
- BibTeX or RIS citation exports.
- Retrieval and access logs.
- Verification state, unresolved items, and coverage data.

Derive structured exports directly from canonical records. Preserve stable source IDs in formats that support custom fields and provide an explicit ID mapping when a format cannot carry them natively. Preserve edge evidence and status in graph exports rather than flattening candidate and verified relationships together.

## Reader-facing report

Use [`../templates/reader-report.md`](../templates/reader-report.md) as the content model for Word, Markdown, and HTML. Include only material that helps the user inspect and navigate the retrieval result:

- A retrieval-oriented thematic overview of the source groups found.
- Concise navigation by approved subquestion, theme, source type, chronology, and selected citation path.
- For each selected source, its stable ID, citation, access status, description basis, what the source addresses, and why it was included.
- Selected key citation paths and each path's retrieval value. List each edge separately with from ID, canonical relation, to ID, status, and evidence location. Candidate status must remain shown even when an evidence location exists; evidence does not upgrade the edge.
- Coverage showing what was searched and not searched by approved subquestion, platform, language, period or chronology, and source class. Derive this table directly from the cumulative `coverage` object in project state; do not reconstruct it from the latest round or hand-edit it.
- Full-text gaps, verification gaps, unresolved identities, and candidate edges that materially affect review.
- The stopping reason and a constrained coverage conclusion. Use `Approaches saturation within the approved scope` only when the reasoned saturation review supports it. Otherwise use a clear `Paused—not saturated` or `In progress—not saturated` status and state the reason. The report must not claim exhaustive or comprehensive coverage.

Select sources and paths for review value; do not reproduce the full corpus in narrative form. Keep exact queries, complete provenance, access-attempt history, and the full graph in structured outputs unless a detail is necessary to understand a material gap.

## Description and analysis boundary

Describe an individual item only from the material identified by its `description_basis` and `description_retrieval_id`. A faithful source description may state what the source addresses and why it was included. It may not attribute a conclusion that was not present in the material accessed.

The report may group sources and explain retrieval paths. Coverage language describes the retrieval process, not the substantive state of the law.

Do not synthesize legal rules.
Do not resolve scholarly disputes.
Do not recommend an argument.
Do not draft academic prose.
Do not turn thematic navigation into a literature review.

## Traceability check

Before export, run `$SKILL_ROOT/scripts/validate_corpus.py` with `--sources`
and `--edges` pointing to the exact canonical checkpoint used to generate the
deliverables. Schema validation alone is not sufficient because it cannot
enforce corpus-wide identity, endpoint, edge direction, and retrieval-link
invariants. Do not export while the script reports any error.

After that validation succeeds, confirm that:

1. Each reported source resolves by stable ID to one canonical source record.
2. Each reported path resolves to canonical nodes and graph edges. Relationship traceability uses endpoint IDs, relation, and status; verified edges retain their evidence locations and candidate edges remain labeled.
3. Access status and description basis match the canonical record.
4. Coverage and stopping reason match the approved plan and project state at the export checkpoint.
5. Word, Markdown, HTML, and structured exports selected for the run were generated from the same corpus checkpoint.
6. Every gap entry carries either a stable source ID or the edge's endpoint IDs, relation, and status. Do not create an untraceable free-form gap list.
