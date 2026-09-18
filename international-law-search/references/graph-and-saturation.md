# Optional Relationship Graph and Saturation Review

## Enable deliberately

The relationship graph is optional, including in deep-audit mode. Enable it
only when the user approves citation tracing or network coverage. Stage 1 does
not construct it. Set `graph_enabled=true` only after graph work is selected;
otherwise validate the canonical sources without an edge file.

Formal saturation review is separately optional. Set
`saturation_enabled=true` only when the approved project calls for multi-round
coverage assessment. Neither a graph nor saturation analysis is required for
a quick bibliography, standard interactive search, or ordinary deep-audit
corpus.

## Relationship families

Store only directed, evidenced relationships between materials:

- **Literature:** `cites`, `responds_to`, `criticizes`, and `extends`.
- **Institutional:** `amends`, `implements`, `interprets`, and
  `same_proceeding`.

`cited_by` is allowed only as an incoming candidate lead. Canonical storage
stores only `citing_node cites cited_node`; the inverse is never a second stored edge.
Thematic similarity is a tag or candidate grouping, not an edge.

Retrieval provenance is not a relationship edge. Queries, platforms, seeds,
footnotes, bibliographies, local files, and subagents belong in source
`discovery_history` and retrieval logs. There is no `discovered_from` edge.

## Evidence and status

Subagents submit graph records with `record_scope=candidate` and
`status=candidate`. The main agent changes an edge to `verified` only after
checking a locatable page, paragraph, footnote, reference entry, or database
citation record. Store the evidence source and precise location.

A citation record supports `cites`; it does not by itself support
`responds_to`, `criticizes`, `extends`, or `interprets`. Those judgmental
relations require locatable textual evidence even while candidate status is
retained. Missing or ambiguous evidence stays unresolved and is not promoted.

## Depth and budget stops

Backward, forward, and lateral tracing begins only from an approved seed.
Five levels is a possible guardrail, not a target or stopping rule. Track each
branch independently and never exceed its authorized depth or item budget.

When a cap is reached, set the branch status and round budget status to
`budget_paused`, preserve untraced paths, and offer the user an extension.
`budget_paused` cannot establish saturation, even when the final authorized
round had low yield or many duplicates.

## Round evidence

After every authorized round record:

- Candidate and unique-new counts.
- New high-relevance and core-material counts.
- Duplicate count or ratio.
- Coverage additions by source type, theme, language, and platform.
- Access gaps and platform failures.
- Open high-value branches, branch depth, and attempted paths.
- `budget_status` as `within_budget` or `budget_paused`.

`$SKILL_ROOT/scripts/round_metrics.py` returns only counts, coverage additions,
access gaps, and open paths from canonicalized source IDs. The caller adds
budget status and the reasoned continue, pause, or stop decision. Metrics do
not decide saturation.

## Formal saturation assessment

Run this assessment only when `saturation_enabled=true`. Review multiple
authorized rounds together; one low-yield round is insufficient. Consider:

- Marginal yield of new high-relevance and core sources across rounds.
- Duplicate trends and repeated returns to existing nodes.
- Coverage of approved subquestions, source classes, languages, periods, and
  platforms.
- Access failures and their likely effect on coverage.
- Remaining high-value paths and whether they are still expanding.

Do not infer saturation while a material platform failed, a required class is
uncovered, or a high-value path remains untraced. If budget ends first, report
the achieved coverage and remaining work as paused, not saturated. Any final
wording is limited to "approaches saturation within the approved scope"; never
claim exhaustive coverage.
