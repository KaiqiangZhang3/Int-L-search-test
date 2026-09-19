# Retrieval Orchestration

## Delegate only independent round work

Keep a small, single-surface round in the main agent. Delegate when approved languages, platforms, source types, jurisdictions, legal subquestions, or citation paths form independently useful assignments. Do not delegate merely to increase agent count.
Delegate only within an approved main or side round.

Every branch brief records the project mode, round ID and type, approved question and exclusions, exact assignment, named platforms and their purposes, languages, source types, period, three-axis branch budget, privacy constraints, and expected return contract. A tracing branch also requires approved seeds, directions, depth, and the authorization decision ID.

The round type does not determine whether work is horizontal or vertical. A `breadth_expansion` branch may search new catalogues while a separately approved `depth` branch traces one seed. Do not trace a seed merely because it was influential or appeared in a prior round.

## Return contracts

Quick and Standard branches return candidate rows compatible with `schemas/source-ledger-record.schema.json` plus candidate claim evidence when the assignment examines a proposition. They report:

- exact discovery provenance;
- source identity evidence and conflicts;
- access and acquisition attempts;
- actual review extent and description basis;
- scholarly importance and acquisition priority when assessed;
- actual bibliographic-discovery, full-text-acquisition, and substantive-review use;
- coverage additions, duplicates, failures, and unresolved paths; and
- candidate claim ID or text, evidence function, exact locator, review basis, and whether the evidence supports, qualifies, or contradicts it.

Deep-audit branches may additionally return candidate nodes and optional candidate edges under the existing deep-audit schemas. Retrieval provenance belongs in source records, not graph edges.

## Main-agent ownership

The main agent alone owns user decisions, deterministic source upsert, stable source keys, claim status and revision lineage, the round index, canonical deep-audit data, synthesis, and reader outputs. A subagent cannot mutate shared ledgers, merge identities, choose final seeds, approve a budget extension, verify a graph edge, decide saturation, or publish a user-facing conclusion.

For each return, the main agent:

1. validates the candidate contract;
2. upserts sources and preserves attributed conflicts and provenance;
3. verifies claim evidence against review extent and exact locators;
4. resolves graph endpoints only when graph work was approved;
5. records actual three-axis use and unresolved paths;
6. validates the source, claim, and round ledgers;
7. generates outputs from one validated checkpoint; and
8. presents complete next-round designs without choosing for the user.

Treat validation as an operational gate. Run `scripts/validate_source_ledger.py`,
`scripts/validate_claim_ledger.py`, and `scripts/validate_round_bundle.py` before
creating a validated checkpoint or reader output. Deep-audit graph work also
requires `scripts/validate_corpus.py`.

## Authorization, failure, and resumption

Never cross an approved discovery, acquisition, review, query, time, depth, seed, language, or platform cap. A branch that reaches a cap becomes budget-paused, preserves its cursor and open paths, and returns control to the user. Budget exhaustion is not saturation.

Record failed platforms and access routes without discarding work completed elsewhere. Retry or switch routes only within the approved round. A resumed branch continues unfinished work from the last valid cursor and uses the same authorization unless the user changed the budget or scope.

Deep-audit projects retain atomic checkpoint transitions through `scripts/checkpoint_state.py` and canonical validation through `scripts/validate_corpus.py`. Those controls support the v3 round record; they do not create a competing stage progression.
