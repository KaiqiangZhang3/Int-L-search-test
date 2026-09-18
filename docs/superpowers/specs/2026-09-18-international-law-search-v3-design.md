# International Law Search v3 Design

## Purpose

Version 3 turns the skill from a fixed staged retrieval workflow into a durable, user-directed research system. It preserves the existing audit, access, privacy, source-normalization, multilingual, and optional graph controls while supporting doctoral-scale bibliographic discovery, repeatable research rounds, writing-time side rounds, cumulative synthesis, and static HTML presentation.

The skill remains a retrieval and source-grounded research assistant. It may produce descriptive synthesis from reviewed material, but it must not choose the user's thesis, present contested law as settled, or draft unsupported argumentative prose.

## Design Principles

1. The user controls the research question, round type, scope, budget, seeds, pauses, and closure.
2. Intake remains conversational and asks one material question at a time.
3. Bibliographic discovery, full-text acquisition, and substantive review are separate activities with separate budgets and claims.
4. A source may be academically indispensable even when its full text is unavailable or unread.
5. Main rounds may repeat in any useful order. A completed breadth round does not force the next round to be depth tracing.
6. Side rounds support a narrow writing-time claim without changing the main research direction.
7. Immutable round reports preserve history; versioned living syntheses provide a coherent current view.
8. Reader-facing Markdown, HTML, and CSV derive from the same validated knowledge state.
9. Machine records remain the source of truth but stay behind the reader-facing presentation.
10. Existing v2 workspaces must migrate without losing source identifiers, provenance, user decisions, review claims, or audit history.

## Product Modes

The existing modes remain, but their scale and artifacts change.

### Quick mode

Quick mode supports orientation and bounded bibliographies. It uses the shared source ledger and a minimum resumable handoff. It may produce one lightweight research round and can upgrade without restarting retrieval. Static HTML is offered when a durable artifact is useful but is not mandatory for a chat-only result.

### Standard interactive mode

Standard mode is the default for substantial academic research. It uses the readiness matrix, repeatable main rounds, optional side rounds, source and claim ledgers, immutable round reports, living synthesis, bibliography CSV, and a static HTML project hub. The user may opt out of presentation artifacts.

### Deep-audit mode

Deep-audit mode adds complete retrieval events, atomic checkpoints, recoverable branch cursors, validated canonical data, and optional relationship graphs and saturation review. It follows the same round and user-decision model as Standard mode; audit requirements do not widen scope.

## Intake and Readiness

The assistant asks one question at a time and does not repeat facts already supplied. A persistent readiness matrix records:

- research purpose and current writing stage;
- tentative question, known disputes, and uncertain disputes;
- inclusion and exclusion boundaries;
- temporal, regional, institutional, and jurisdictional scope;
- desired balance among primary materials, doctrine, theory, cases, state practice, and empirical work;
- languages and the research purpose of each language branch;
- existing sources, authors, schools of thought, bibliographies, Zotero libraries, PDFs, and local collections;
- desired footnote, reference, cited-by, and author-lineage tracing;
- database, library, subscription, interlibrary-loan, and physical-book access;
- research scale;
- interaction cadence;
- citation style and output formats;
- HTML presentation preference; and
- whether the task starts a research project or supports one claim during writing.

Readiness is sufficient when the next bounded round can be designed and approved. It does not require the user to settle an uncertain research question before an exploratory round.

## Research Scale Profiles

Scale profiles set expectations rather than quotas.

| Profile | Bibliographic discovery | Substantive review | Typical use |
| --- | ---: | ---: | --- |
| Orientation | 15–30 | 5–10 | Initial understanding |
| Seminar paper | 30–60 | 10–20 | Course or seminar paper |
| Thesis chapter | 60–120 | 15–30 | Dissertation or thesis chapter |
| Doctoral corpus | 100–300+ | Iterative | Doctoral dissertation or long-running project |

The stopping decision depends on convergence across source genealogies, positions, source types, periods, jurisdictions, and languages. The skill must not add weak sources merely to reach a profile range.

## Round Model

### Main rounds

Main rounds use sequential IDs such as `R1`, `R2`, and `R3`. A round declares one `round_type`:

- `breadth`
- `breadth_expansion`
- `depth`
- `primary_materials`
- `state_practice`
- `doctrinal`
- `gap_filling`
- `verification`
- `synthesis`

The type describes the round's purpose, not its position. Any compatible type may follow another after user approval.

### Side rounds

Side rounds use parent-scoped IDs such as `R2.S1`. They do not advance the main-round counter or silently alter the approved main project. A side round normally confirms:

- the precise proposition or citation problem;
- the needed evidence function;
- applicable language, date, jurisdiction, or institution limits; and
- a small discovery, acquisition, review, query, and time budget.

Its claim-support package reports:

- `supported`, `partially_supported`, `unsupported`, or `counterevidence_found`;
- a safer proposed formulation when needed;
- the strongest two to five sources;
- precise pages, paragraphs, provisions, or other locators;
- each source's evidentiary function;
- contrary evidence and limitations;
- normalized footnote-ready citations; and
- whether the issue merits promotion to a main round.

Accepted source and claim records join the shared knowledge layer. The side-round report remains immutable.

### Round approval and pauses

Every retrieval round requires a concise approved specification. Query refinements within that specification do not require reapproval. A material change to question, scope, source track, language, jurisdiction, seed, tracing direction, depth, or budget does.

Every completed or paused round creates a report containing a concrete next-round menu. The menu may offer another breadth round, a source-type expansion, a language or regional expansion, selected-seed tracing, review without new discovery, synthesis, a writing pause, a side round, or closure. Each option states its purpose, objects, seeds, method, three-axis budget, expected output, and exclusions.

## Three-Axis Research Budget

Every round records planned and actual use for:

1. `bibliographic_discovery`: identities discovered and bibliographically verified;
2. `full_text_acquisition`: texts successfully obtained through authorized routes; and
3. `substantive_review`: full texts or selected sections actually examined.

The round may also cap named platforms, queries, time, tracing depth, seeds, and language allocations. Time is an upper bound, not a completion promise. Platform budgets name each platform and its purpose.

An unavailable but important source remains in the ledger with its acquisition route, scholarly importance, reason it must be read, and honest review state. Lack of access must not automatically lower scholarly priority.

## Knowledge Layer

### Source ledger

The existing source ledger remains authoritative for source identity and access history. Version 3 adds:

- `scholarly_importance` with a reason;
- `acquisition_priority` such as `must_obtain`, `should_obtain`, or `optional`;
- `acquisition_routes` for open, subscription, publisher, library holding, physical copy, purchase, document delivery, or unavailable routes;
- bibliographic discovery and review round references;
- richer identifiers such as ISBN and library identifiers; and
- an explicit record of whether a source is suitable for a particular claim or only for background discovery.

The availability and review-extent axes remain independent.

### Deterministic source upsert

A dedicated ledger operation must insert or merge records using normalized strong identifiers first and conservative metadata fallback second. DOI, official document number, case number, treaty identifier, ISBN plus edition, and stable publisher identity are type-aware keys. Title capitalization and punctuation differences do not create a conflict. Ambiguous identities remain separate and require review.

Upsert must preserve:

- the stable `source_key`;
- every discovery path;
- aliases and prior citations;
- access and review events;
- source-specific user decisions;
- attributed metadata conflicts; and
- round membership.

The operation must be atomic and idempotent.

### Claim ledger

Each research proposition has a stable record containing:

- `claim_id` and normalized claim text;
- claim type and applicable scope;
- status: `provisional`, `supported`, `contested`, `revised`, or `superseded`;
- `first_seen_round` and `last_verified_round`;
- supporting and contrary evidence entries;
- source keys plus precise evidence locators;
- the review basis that permits the claim;
- predecessor or successor claim links when revised; and
- a reader-facing qualification.

A claim cannot be `supported` without qualifying reviewed evidence. A source discovered only through metadata cannot support a substantive proposition. Revised and superseded claims remain in history but do not appear as current conclusions without an explicit historical label.

### Round index

The round index records:

- round ID, parent ID, kind, and type;
- status and authorization decision;
- research question and exclusions;
- planned and actual budgets;
- named platforms and their functions;
- seeds and methods;
- added, updated, duplicate, and unresolved source keys;
- added or revised claim IDs;
- immutable report paths;
- synthesis and presentation versions; and
- next-round menu entries.

### Other shared records

The decision log records user choices across rounds. The terminology table stores multilingual concepts, variants, legal distinctions, and search uses. Bibliography CSV provides a human-usable complete source inventory. Optional deep-audit graph data stays separate from discovery provenance and claim evidence.

## Workspace Layout

New durable projects use this conceptual layout:

```text
project/
  knowledge/
    sources.jsonl
    claims.jsonl
    rounds.jsonl
    decisions.jsonl
    terminology.jsonl
  reports/
    round-R1-breadth.md
    round-R2-depth.md
    side-R2-S1-claim-verification.md
  synthesis/
    synthesis-v1.md
    synthesis-v2.md
    current-synthesis.md
  presentations/
    round-R1.html
    round-R2.html
    side-R2-S1.html
    index.html
  exports/
    bibliography.csv
  logs/
  state.json
```

Quick-mode projects may use a reduced form, but any upgrade maps their source ledger and handoff into the same knowledge layer.

## Reports and Presentation

### Immutable round report

Each round report explains:

- why the round ran;
- what it added;
- which earlier understandings it confirmed, revised, or superseded;
- important new sources and claims;
- remaining gaps;
- planned and actual budget use; and
- the next-round menu.

Past round reports are never overwritten.

### Living synthesis

After each main or side round, the project may generate a new versioned synthesis and update `current-synthesis.md`. It reorganizes the current validated knowledge into the research question, terminology, literature development, positions, argument matrix, primary materials, state practice, cases, disputes, unresolved questions, reading path, classified bibliography, coverage, limits, and round history.

The synthesis is regenerated from current source, claim, round, terminology, and decision records. It is not a concatenation of round reports. It displays claim revision history when that history affects the reader's understanding.

### Static HTML

Standard and Deep-audit projects recommend static HTML by default, subject to user choice. Each HTML page and the project hub derive from the same structured round bundle and validated ledgers as the Markdown output. HTML is self-contained, uses local CSS, loads no network resources, and is suitable for screen reading and printing. Generation never opens a browser automatically.

The project hub shows reader-facing research content, filters, timelines, round navigation, current synthesis, gaps, and links to Markdown and CSV. JSONL, manifests, logs, state, and validators stay hidden unless the user expands a research-record section or requests them.

### Clear delivery

After generation, the assistant explicitly identifies the main entry file, current synthesis, latest round report, and bibliography CSV. The user must not need to ask where the outputs were saved.

## Shared Round Bundle

To prevent Markdown, HTML, CSV, and ledger drift, each round first creates a validated structured bundle referencing source keys and claim IDs. Renderers consume that bundle and the knowledge ledgers. Narrative sections may be drafted by the assistant, but every cited source and claim reference must resolve before rendering.

The bundle contains no private local paths or non-externalizable notes. Existing export-manifest privacy checks remain mandatory for outbound content.

## Validation

Version 3 adds deterministic validators for:

1. source-ledger schema and cross-record uniqueness;
2. source upsert identity and idempotency;
3. claim evidence and revision lineage;
4. round IDs, parent links, authorization, budgets, and artifact paths;
5. report and synthesis citations against source and claim ledgers;
6. Markdown, HTML, and CSV consistency at one checkpoint;
7. HTML internal links, required sections, local assets, and absence of network dependencies;
8. unresolved manual-review items before final delivery; and
9. privacy classifications and local-path exclusion.

Validators must distinguish blocking integrity failures from non-blocking coverage warnings. A failed artifact build must not corrupt the last valid synthesis or project hub.

## Access Recovery

When an official or publisher route fails, the skill records the failed attempt and tries authorized alternatives appropriate to the source type, such as another official repository, a library catalogue, an institutional subscription, an open repository, a publisher page, or a document-delivery lead. A search snippet cannot become full-text evidence. Local file paths remain internal and must not appear in outbound reports or HTML.

## Orchestration

The main agent owns readiness, user decisions, source upsert, claim status, round indexing, synthesis, and final artifacts. Subagents may conduct independently bounded language, platform, source-type, jurisdiction, or tracing assignments when complexity justifies delegation. Their return contracts include candidate source records, candidate claim evidence, actual three-axis budget use, failures, and unresolved paths. They cannot mutate the shared ledgers or decide claim status, synthesis, saturation, or the next round.

## Migration

A v2-to-v3 migration performs an additive conversion:

1. preserve all source and decision identifiers;
2. convert existing stage or round records into main-round records;
3. map previous source and full-text caps into the new budget axes while marking unknown historical acquisition counts explicitly;
4. retain graph and retrieval logs when present;
5. initialize empty claim and terminology ledgers without inventing claims;
6. register existing reports as legacy artifacts;
7. build the first bibliography CSV and project hub only from validated migrated data; and
8. leave the original workspace recoverable until the migrated copy passes validation.

The migration must be idempotent or refuse to remigrate an already converted workspace.

## Implementation Boundaries

The upgrade will modify the skill instructions, references, templates, schemas, scripts, fixtures, and tests. It will not perform a live international-law search, rewrite user feedback files, or add external services. Existing user-owned untracked files remain untouched.

## Test Strategy

Implementation follows vertical red-green-refactor slices:

1. source upsert and duplicate prevention;
2. Standard ledger validation;
3. claim evidence and revision lifecycle;
4. repeatable main-round IDs and side-round IDs;
5. three-axis budgets and doctoral-scale profiles;
6. next-round menus embedded in round artifacts;
7. one structured bundle producing consistent Markdown, HTML, and CSV;
8. living synthesis versioning and claim supersession;
9. v2-to-v3 migration; and
10. end-to-end scenarios for doctoral discovery, repeated breadth expansion, selected-seed tracing, writing-time claim verification, inaccessible canonical books, multilingual terminology, and clear artifact delivery.

Tests assert observable behavior through public scripts and artifact contracts. Existing privacy, access, graph, corpus, and user-choice regression tests remain in the suite and are updated only where the v3 model intentionally replaces fixed stage semantics.

## Acceptance Criteria

The upgrade is complete when:

- no instruction forces a fixed breadth-to-depth-to-gap-filling sequence;
- intake remains one question at a time and records a complete readiness matrix;
- doctoral-scale discovery can record hundreds of verified citations without claiming equivalent review;
- source upsert prevents duplicate strong-identifier records and preserves provenance;
- source, claim, round, and decision records validate independently and together;
- a side round can add evidence without advancing the main-round counter;
- every paused round includes a concrete next-round menu in its saved report;
- immutable reports and versioned synthesis coexist without contradiction;
- Markdown, HTML, and CSV resolve to the same source and claim checkpoint;
- inaccessible but important books and chapters remain visible and prioritized honestly;
- final delivery clearly links the presentation hub, synthesis, latest report, and bibliography;
- v2 fixtures migrate without losing identifiers, decisions, provenance, or review extent; and
- all existing and new automated tests pass.
