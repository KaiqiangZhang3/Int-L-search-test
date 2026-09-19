# Research Rounds

## Round model

Use repeatable main rounds rather than a fixed stage progression. Main rounds are `R1`, `R2`, and onward. After user approval, any useful round type may follow any other; for example, `breadth` may be followed by `breadth_expansion`, another source-focused round, or `synthesis` rather than mandatory citation tracing.

Available round types are:

- `breadth`: map the field and identify candidate materials and positions;
- `breadth_expansion`: extend coverage by source type, period, jurisdiction, region, language, platform, or perspective;
- `depth`: trace selected seeds backward, forward, or laterally;
- `primary_materials`: retrieve and verify treaties, cases, institutional documents, resolutions, and other primary materials;
- `state_practice`: retrieve attributable practice and opinio juris evidence with jurisdictional and temporal controls;
- `doctrinal`: examine a defined doctrinal question or literature lineage;
- `gap_filling`: address a demonstrated retrieval or coverage gap;
- `verification`: verify identities, propositions, citations, access, or conflicting metadata;
- `synthesis`: consolidate current validated knowledge without silently widening retrieval.

The type states purpose, not position. Every main round receives the next consecutive `R` number.

## Side rounds

Side rounds answer narrow writing-time questions without changing the approved main research direction. They use a parent-scoped ID such as `R2.S1`, do not advance the main counter, and may not have another side round as their parent. Typical uses include checking whether a source supports a sentence, locating controlling text, finding contrary authority, or repairing a citation.

Before starting, confirm the proposition or citation problem, evidence function, relevant language/date/jurisdiction limits, and a small budget. A side-round result should state `supported`, `partially_supported`, `unsupported`, or `counterevidence_found`; propose a safer formulation when necessary; give the strongest two to five sources with exact locators and evidentiary functions; identify limits or contrary evidence; and state whether promotion to a main round is warranted.

Accepted sources and claims join the shared ledgers. The side-round report is immutable, and its findings may update the next version of the living synthesis.

## Three-axis budget

Plan and report these independently:

1. `bibliographic_discovery`: source identities found and bibliographically verified;
2. `full_text_acquisition`: texts successfully obtained through authorized routes;
3. `substantive_review`: full texts or selected sections actually examined.

Also record named platforms and each purpose, query and time caps, tracing depth, seeds, and language allocations. An important inaccessible work remains visible as an acquisition priority; lack of access does not lower its scholarly importance. Planned counts are caps or expectations, not promises. Actual counts must never exceed an authorized cap unless a recorded user decision extends it.

## Approval contract

Before retrieval, present one concise round specification containing:

- round kind and type;
- question addressed and expected output;
- inclusions, exclusions, and retrieval objects;
- starting seeds and method;
- the three-axis budget plus platform, query, time, depth, and language caps; and
- the stopping checkpoint.

Approval authorizes only that specification. Query wording may be refined within it. Obtain a new decision before changing the question, material scope, source track, language, jurisdiction, seed, tracing direction, depth, output, or budget.
A newly suggested seed requires approval before tracing, even when it appears highly influential.

## Allocation and persistence

Use `scripts/round_ops.py` to allocate IDs and append records to `knowledge/rounds.jsonl`. The append operation rejects duplicate IDs, main-round gaps, missing or side-round parents, and use above authorized caps without an extension decision. It replaces the ledger atomically so a failed validation does not partially write a round.

Every paused or completed round records planned and actual budgets, source and claim changes, gaps, report and presentation pointers, and complete next-round options. Round reports remain immutable. A next-round menu may offer another breadth round, source-type or language expansion, selected-seed tracing, review without new discovery, verification, synthesis, a writing pause, a side round, or closure. The user chooses; completion of one type never silently authorizes another.
