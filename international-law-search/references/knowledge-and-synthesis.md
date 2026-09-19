# Knowledge and Synthesis

## Purpose

Keep retrieval records separate from research propositions. The source ledger says what a work is, how it was found, what was accessible, and what was actually reviewed. The claim ledger says which proposition the reviewed material can support, qualify, or contradict. Reports and the living synthesis are views of these ledgers, not independent stores of research facts.

Use `schemas/claim-record.schema.json` for each claim record and `scripts/validate_claim_ledger.py` for cross-ledger validation.

## Claim Records

Create one stable `claim_id` for each materially distinct proposition. Write `claim_text` as a complete, bounded sentence. Keep `claim_type` useful to the project rather than forcing every project into a universal taxonomy. Use `scope` to state the applicable legal issue, jurisdictional or institutional setting, time boundary, and any other limit needed to prevent overgeneralization.

Record:

- `first_seen_round`: the main or side round in which the proposition first entered the knowledge layer;
- `last_verified_round`: the latest round that checked the proposition against qualifying evidence, or `null` while it remains unverified;
- supporting and contrary evidence separately;
- predecessor and successor claim IDs when the proposition changes; and
- `reader_qualification`: a short reader-facing limit or caveat, not internal process commentary.

Do not create duplicate claims merely because another round or source states the same proposition. Update evidence and `last_verified_round` on the stable record. Create a successor only when the proposition itself changes materially.

## Status Semantics

Use exactly one status:

| Status | Meaning |
|---|---|
| `provisional` | A research proposition worth tracking, but not yet supported by qualifying reviewed evidence. |
| `supported` | At least one supporting item has a precise locator and a substantive review basis. |
| `contested` | Qualifying reviewed evidence exists on both the supporting and contrary sides. |
| `revised` | A later proposition materially changes this claim while retaining its lineage. |
| `superseded` | A later proposition replaces this claim for current research use. |

`revised` and `superseded` records remain immutable history. They do not appear among current conclusions unless the output gives them an explicit historical label. `current_claim_ids()` implements this default selection rule.

## Evidence Rules

Every evidence entry identifies:

- `source_key`: an existing source-ledger record;
- `locator`: an exact page, paragraph, provision, section, chapter, footnote, or equivalent location;
- `evidence_function`: what the passage does for the proposition; and
- `review_basis`: the extent of content review that permits the evidence use.

For a substantive proposition, qualifying review basis is `selected_sections_reviewed` or `full_text_substantively_reviewed`. The entry must not claim a stronger basis than the linked source record. Metadata, snippets, citation counts, and an unreviewed abstract can establish discovery or identity, but cannot support a substantive proposition.

Use the evidence function precisely:

| Value | Use |
|---|---|
| `direct_support` | The located material expressly supports the proposition. |
| `interpretive_support` | The proposition follows from a stated interpretation of the located material. |
| `qualification` | The material narrows or conditions the proposition. |
| `contrary_authority` | Authority expressly rejects or conflicts with the proposition. |
| `counterexample` | The material supplies a factual, doctrinal, or institutional counterexample. |
| `context` | The material is needed to understand the proposition but does not independently prove it. |

A `supported` claim requires supporting evidence. A `contested` claim requires both supporting and contrary evidence. Include qualifications and context in the appropriate evidence array, but do not count context alone as direct proof when describing the claim to the reader.

## Revision Lineage

When a claim changes materially:

1. preserve the old record and stable ID;
2. create a new claim with a new ID;
3. set the old status to `revised` or `superseded`;
4. add the new ID to the old record's `successor_claim_ids`;
5. add the old ID to the new record's `predecessor_claim_ids`; and
6. explain the operative limit in each record's reader qualification when needed.

Links must be reciprocal, must resolve within the claim ledger, and must not form a revision cycle. A historical claim requires at least one successor. Do not overwrite earlier claim text to conceal a change in understanding.

## Round Write-Back

Every main round and side round writes validated knowledge back to the same ledgers. A side round may add sources, add claims, add evidence, or revise a claim, but it does not maintain a separate private conclusion set. Preserve its round ID in `first_seen_round` or `last_verified_round` as appropriate.

Before a round completes:

1. upsert sources and preserve their provenance;
2. add or update claims without duplicating stable propositions;
3. validate source references, locators, review basis, and revision lineage;
4. record which claim IDs were added or revised in the round record; and
5. generate reader artifacts only from the validated checkpoint.

## Living Synthesis

The living synthesis is regenerated from the current source, claim, round, terminology, and decision records. It is not a concatenation of round reports and must not become a second knowledge store.

By default, synthesize only current claims. A revised or superseded claim may appear only with an explicit historical label when its history helps the reader understand a doctrinal shift, evidentiary correction, or change in project framing. Display contested claims as contested and preserve both evidence directions. Display provisional claims as open questions or gaps, not findings.

Each reader-facing proposition must remain traceable to its `claim_id` and then to source keys and exact locators. Render the concise reader qualification near the proposition when omission would overstate the result. Internal validator output, local paths, and private notes do not belong in the reader-facing narrative.

## Validation

Run:

```bash
python3 scripts/validate_claim_ledger.py \
  --claims project/knowledge/claims.jsonl \
  --sources project/knowledge/sources.jsonl
```

The validator returns errors without mutating either ledger. Resolve every reported duplicate ID, missing source, missing locator, insufficient review basis, non-reciprocal link, missing successor, or revision cycle before treating the checkpoint as valid.
