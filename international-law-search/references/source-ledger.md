# Source Ledger

## Purpose

Use the lightweight source ledger in Quick mode and Standard interactive mode. It is the shared source of truth for reader-facing reports and later mode upgrades. It records enough evidence to preserve identity, provenance, access truthfulness, review limits, relevance, and user choices without forcing a graph, a persistent workspace, or a complete audit log.

Pair the ledger with the compact `templates/session-handoff.md` artifact. The handoff preserves project-level scope, branch, language, budget, mode, and stopping decisions; the ledger preserves source-level decisions. Together they support an upgrade or resumption across sessions without pretending to be a deep-audit workspace.

The JSON contract is `schemas/source-ledger-record.schema.json`. A source may later become a deep-audit canonical record, but the earlier ledger record remains part of its history.

## Minimum Record

Every ledger record requires:

- `source_key`: a stable project-local key. Preserve it across rounds and mode upgrades.
- `identity_evidence`: the normalized title, identity status, and the records or document text used to identify the source.
- `discovery_provenance`: every material route through which the source entered the project, such as a query, local seed, footnote, reference, cited-by index, or subagent return.
- `availability`: the best verified access route currently known.
- `review_extent`: what the assistant actually examined through any authorized route.
- `description_basis`: the evidence level and locations supporting the annotation.
- `description`: a concise account of what the source does, bounded by the review evidence.
- `inclusion_reason`: why the source belongs in this project.
- `user_decisions`: source-specific instructions that later rounds must honor.

Identifiers, links, local paths, source type, language, ranking factors, reading priority, version relationships, and retrieval events are optional at first and added when known. Do not invent empty facts merely to make a record look complete.

Version 3 also supports the following optional research-management fields:

- `scholarly_importance`: a closed level (`foundational`, `major`, `useful`, `peripheral`, or `not_assessed`) plus a concise evidence-based reason. Importance is independent from current access.
- `acquisition_priority`: `must_obtain`, `should_obtain`, `optional`, or `not_assessed`.
- `acquisition_routes`: typed open, subscription, publisher, library-holding, physical-copy, purchase, document-delivery, or unavailable routes. A route containing a local path must set `externalizable` to `false`.
- `round_membership`: the stable round ID and whether the source was discovered, acquired, reviewed, used as a seed, used as evidence, or retained as background in that round.

Use `identifiers.isbn`, `isbn_10`, or `isbn_13` for ISBNs and `oclc`, `lccn`, or `worldcat` for library identifiers. Keep edition information in the type-specific book or chapter details so ISBN matching can remain edition-aware.

## Deterministic Upsert

Use `scripts/ledger_ops.py` whenever a source enters or re-enters a Standard ledger. Its public operations are:

- `normalized_identity_keys(record)`: returns strongest-first, type-aware identity keys.
- `upsert_source(path, record)`: atomically inserts or merges one record and returns its action and stable source key.

Identity matching uses DOI first, followed by namespaced official document, case, treaty, stable publisher, and ISBN-plus-edition identifiers. Only when strong identifiers do not conflict may normalized title, creators, publication date, and source type provide a conservative fallback. Capitalization, punctuation, DOI URL prefixes, and creator ordering do not create separate identities. Conflicting strong identifiers remain separate even when their descriptive metadata matches.

An upsert preserves the existing `source_key` and records a different incoming key in `source_key_aliases`. It unions discovery provenance, user decisions, acquisition routes, round membership, retrieval history, links, paths, version relationships, and citation aliases without duplicating identical values. Repeating an identical upsert is a no-op. The ledger is written through a sibling temporary file and replaced atomically.

Run the Standard-ledger validator before rendering or migration:

```bash
python3 scripts/validate_source_ledger.py path/to/sources.jsonl
```

Exit code `0` means valid, `1` means readable input with invalid content, and `2` means that the ledger or bundled schema could not be read. The validator checks every JSONL row against the record schema, then rejects duplicate stable keys, duplicate strong identities, descriptions exceeding their review evidence, and local paths marked for externalization.

## Availability and Review Are Separate

`availability` describes the best verified route, not the latest attempt. `review_extent` describes actual examination, not theoretical access. A subscription route can coexist with substantive review, while an open route can coexist with `not_reviewed`.

Use these reader-facing labels instead of exposing internal enums. Localize labels consistently with the report language; a Chinese report must not require the reader to interpret English system terms.

### Availability reader-facing labels

| Internal value | English label | Chinese label |
|---|---|---|
| `open_full_text` | Open full text available | 可公开获取全文 |
| `subscription_full_text` | Full text available through authorized subscription | 可通过已授权订阅获取全文 |
| `identified_inaccessible` | Identified, but full text is not currently accessible | 已确认材料，但暂无法获取全文 |
| `abstract_available` | Abstract available | 可获取摘要 |
| `metadata_only` | Metadata only | 仅核验元数据 |
| `access_failure` | Access attempt failed | 访问失败 |

### Review-extent reader-facing labels

| Internal value | English label | Chinese label |
|---|---|---|
| `full_text_substantively_reviewed` | Full text substantively reviewed | 已实质审阅全文 |
| `selected_sections_reviewed` | Selected sections reviewed | 已审阅相关章节 |
| `abstract_reviewed` | Abstract reviewed | 已审阅摘要 |
| `metadata_verified` | Metadata verified | 已核验元数据 |
| `not_reviewed` | Not reviewed | 尚未审阅内容 |

Opening a page is not substantive review. Search snippets and index fragments never support a full-text or selected-section claim. Record named sections, provisions, paragraphs, pages, or other useful locators in `description_basis.locations`. Descriptions and later synthesis must not exceed that basis.

## Description Basis

Use `full_text`, `selected_sections`, `abstract`, `metadata`, or `none`. For substantive or selected-section review, identify the inspected locations. An abstract supports a description of the abstract's stated purpose or claim, not an account of the complete argument. Metadata supports identity and classification, not a substantive account of the source's position.

## Ranking and Reading Priority

Record ranking factors separately. Do not collapse direct relevance, legal or institutional authority, scholarly influence, citation-network position, viewpoint distinctiveness, recency, regional or linguistic representation, verification strength, introductory value, and issue-specific utility into an unexplained score.

Use one reading-priority value and explain it in the reader annotation:

| Internal value | English label | Chinese label |
|---|---|---|
| `priority_reading` | Priority reading | 优先阅读 |
| `read_by_research_direction` | Read according to research direction | 按研究方向选择阅读 |
| `background_or_supplementary` | Background or supplementary reading | 背景或补充阅读 |

## User Decisions

Record decisions that affect later work, including inclusion, exclusion, seed selection, review without tracing, approved tracing, a hold, a stop-tracing instruction, or full-text priority. A later round must consult these entries before expanding a branch. An empty array means that no source-specific choice has yet been recorded; it does not authorize tracing.

## Upgrade Invariants

Enrichment may add identifiers, evidence, links, retrieval events, type-specific metadata, verification detail, version relations, or graph records. It must preserve the following invariants:

- An upgrade **must not discard provenance**. Retain every valid discovery route and attribute corrections.
- An upgrade **must not silently change identity**. Preserve aliases and conflicting candidates until the change is evidenced and disclosed.
- An upgrade **must not overstate prior review**. New access does not retroactively mean that full text was read; raise `review_extent` only after actual review.
- Preserve `source_key` as the cross-mode key or map it explicitly to a canonical identifier.
- Preserve user decisions and the round in which they were made.
- Keep local paths and private annotations out of reader-facing or externally transmitted outputs unless the user separately authorizes disclosure.

`retrieval_history` is optional enrichment. Citation or institutional relationships belong in optional graph records, not in the lightweight ledger. Retrieval provenance stays with the source and is never presented as proof of a scholarly relationship.
