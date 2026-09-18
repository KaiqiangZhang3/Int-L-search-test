# Citation Graph Expansion and Dynamic Saturation

## Expansion directions

Start from approved seeds and newly identified core materials. Expand in three
directions:

- **Backward:** inspect footnotes, reference lists, cited cases, treaties, and
  institutional documents.
- **Forward:** locate later cases, documents, and scholarship that cite the
  node through authoritative citation records or verified full text.
- **Lateral:** inspect the same issue, case or procedural series, author
  network, or identifiable scholarly exchange.

Candidate submissions may use these relationships: `cites`, `cited_by`,
`interprets`, `same_case_series`, `same_issue`, `response_to`, and
`discovered_from`. Thematic resemblance alone is not evidence of a
relationship.

## Edge status and evidence

Subagents submit every relationship with `record_scope=candidate` and
`status=candidate`. The main agent may
mark it `verified` only after checking an evidence location. Acceptable
locations include a page, paragraph, footnote, reference entry, or database
citation record. Store the evidence source and precise location in the edge
record. When the location is absent or ambiguous, keep the edge as
`candidate`; do not infer or upgrade it.

Direction matters. Regardless of whether a discovery source reports `cites`
or `cited_by`, canonical graph storage stores only `citing_node cites cited_node`.
It derives `cited_node cited_by citing_node` for inverse navigation; the
derived relationship is never a second stored edge and never another
discovery. A citation does not by itself support `interprets` or `response_to`.
After endpoint resolution and inverse normalization, the main agent sets
`record_scope=canonical`; canonical records never use `cited_by`.

## Depth guardrail

Five levels is the usual depth guardrail. It is neither a quota nor an
automatic stopping rule: a branch may saturate earlier, and a high-value
branch may justify going deeper. Track depth per branch because horizontal
discovery and separate vertical paths may progress at different rates.

Never cross the maximum depth authorized in the approved plan. When the next
round would exceed that depth, pause the branch, preserve its open paths, and
request reapproval with the marginal-yield evidence and expected value of the
extra depth.

## Round evidence

After each retrieval round, record:

- Candidate count and unique new-candidate count.
- New high-relevance and new core-material counts.
- Newly covered source classes, themes, languages, and platforms.
- Duplicate count or duplicate ratio.
- Important sources without full-text access.
- Untraced high-value citation branches.
- Branch depth, queries or paths attempted, and access failures.

After recording the round, update the cumulative `coverage` object in project
state. For subquestions, platforms, languages, periods, and authority classes,
move completed approved surfaces to `searched`, retain approved but unfinished
surfaces in `unsearched`, and preserve both arrays across rounds. Round-level
`coverage_additions` is evidence for this update, not a replacement for the
cumulative object.

Inputs to `$SKILL_ROOT/scripts/round_metrics.py` are already canonicalized
source records, and comparison uses their canonical `id`. The script returns
a state-compatible evidence fragment containing `counts`, dimensioned
`coverage_additions`, `access_gaps`, and `open_high_value_branches`. It
produces evidence only: it never declares saturation, makes a stopping
decision, or authorizes another round.

The caller adds the branch ID, round number, timestamp, branch depth, attempts,
access failures, and the reasoned decision, reason, and gaps. To form a full
round state, encode the round number in `round_id`, use the branch ID as a key
in `branch_depth`, and store the remaining values as `timestamp`,
`attempted_queries_or_paths`, `access_failures`, `decision`,
`decision_reason`, and `unresolved_gaps`, as defined by
`$SKILL_ROOT/schemas/project-state.schema.json`.

## Reasoned saturation review

Dynamic saturation is a reasoned decision by the main agent, not a fixed
numeric threshold. Review multiple rounds and the approved coverage dimensions
together. Evidence that the corpus approaches saturation may include:

- Consecutive rounds yield few new high-relevance or core sources.
- Results are increasingly duplicates or low-relevance peripheral items.
- Core citation paths repeatedly return to existing canonical nodes.
- Approved subquestions, source classes, languages, periods, and platforms
  have reasonable coverage.
- No untraced high-value branch remains in rapid expansion.

No single indicator is sufficient. A low-yield round does not justify stopping
when a major platform failed, a required source class is uncovered, or a
high-value branch remains open. Conversely, a branch may stop before depth
five when its evidence shows saturation. Branches may saturate independently.

For each continuation, pause, or stop decision, write the evidence considered,
the unresolved gaps, and the reason. If the approved budget ends before
saturation, report present coverage and remaining high-value work and seek
reapproval. Never claim exhaustive coverage; state only that the corpus
approaches saturation within the approved scope.
