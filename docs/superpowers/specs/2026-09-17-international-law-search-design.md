# International Law Search Skill Design

## 1. Purpose

Create a single-entry skill for academic international-law retrieval. The skill helps a user define and approve a search plan, executes the approved search, expands the result through citation networks, and delivers a resumable and auditable source package.

The skill performs retrieval and retrieval-oriented description. It does not conduct substantive legal research on the user's behalf: it does not synthesize legal rules, reconcile scholarly positions, choose an argument, or draft academic prose.

## 2. Scope

The first version covers public international law and its major fields, including:

- General public international law.
- International human rights law.
- International humanitarian law.
- International criminal law.
- International investment law.
- Law of the sea.
- International environmental law.
- International economic law.

Private international law, conflict of laws, and general cross-border commercial law are outside the initial scope.

The skill supports four entry points:

- A broad topic that needs narrowing.
- A defined research question.
- A paper outline or draft containing retrieval needs.
- One or more seed sources, including local files and bibliographies.

## 3. Product Boundary

### 3.1 In scope

- Interactive definition of retrieval direction, depth, content, languages, dates, platforms, exclusions, and output formats.
- Separate but coordinated retrieval of primary international-law materials and secondary academic literature.
- Public, subscription, institutionally accessible, and user-connected databases.
- Local PDFs, bibliographies, Zotero libraries, and other user-authorized local collections.
- Forward, backward, and lateral citation tracing.
- Metadata validation, deduplication, access-status tracking, and provenance recording.
- Brief source-level descriptions explaining what a source addresses and why it was included.
- Retrieval-oriented thematic navigation, key-path summaries, and coverage statements.
- Persistent project state for resumption and later updates.

### 3.2 Out of scope

- Synthesizing a rule of international law from retrieved authorities.
- Reconciling or evaluating competing scholarly positions.
- Recommending a legal or academic argument.
- Drafting a literature review, research memorandum, article section, or paper.
- Treating model memory as a retrieval or verification source.
- Claiming absolute comprehensiveness.

## 4. Architecture

The skill uses one user-facing entry point with six internal modules.

### 4.1 Interactive Intake

Identify the entry-point type and ask one material question at a time. Questions are adaptive rather than a fixed questionnaire. They normally establish:

- The research objective and issue boundaries.
- Relevant fields of international law.
- Primary and secondary source coverage.
- Time period and historical cutoffs.
- Required languages.
- Search depth and resource constraints.
- Known sources and local materials.
- Included and excluded platforms.
- Subscription and institutional access conditions.
- Required output formats.

### 4.2 Search Orchestrator

Convert the confirmed scope into executable branches. Decide whether the main agent can complete the task directly or whether subagents are justified by complexity. Assign consistent schemas, constraints, and stopping rules to every branch.

### 4.3 Source Discovery

Run two coordinated retrieval lines:

- Primary materials: treaties, judgments, advisory opinions, orders, international-organization resolutions and documents, and state practice.
- Secondary materials: monographs, edited-volume chapters, journal articles, commentaries, working papers, and institutional research reports.

Use an adaptive source map based on the subject, tribunal, organization, jurisdictional context, and required languages.

### 4.4 Citation Graph Expansion

Expand from seed and core materials in three directions:

- Backward: footnotes, references, cited cases, cited treaties, and cited institutional documents.
- Forward: later cases, documents, and scholarship that cite the material.
- Lateral: the same issue, case series, source, author network, or scholarly exchange.

The usual maximum depth is approximately five levels. Five levels are an experience-based guardrail, not a required quota or an absolute ceiling. Dynamic saturation remains the primary stopping condition.

### 4.5 Corpus and State Manager

Maintain the canonical corpus, citation graph, deduplication index, retrieval progress, open branches, and stopping evidence. Save enough state to resume the project or run a later update without restarting.

### 4.6 Exporter and Coverage Auditor

Produce user-selected combinations of Word, Markdown, HTML, CSV, JSONL, BibTeX, RIS, retrieval logs, and graph data. Ensure that all formats derive from the same canonical records.

## 5. Interaction and Approval Flow

1. Detect whether the user supplied a topic, question, draft, or seed corpus.
2. Inspect authorized local context and existing source lists.
3. Ask adaptive questions one at a time.
4. Split the request into searchable subquestions.
5. Draft a search plan containing:
   - Primary-source and secondary-literature branches.
   - Target platforms and databases.
   - Languages and time ranges.
   - Initial queries and query-expansion strategy.
   - Citation-tracing strategy.
   - Expected subagent allocation.
   - Initial depth or resource budget.
   - Exclusions, risks, and access constraints.
   - Selected output formats.
6. Present the plan for user approval.
7. Incorporate requested revisions and present the final plan.
8. Begin execution only after approval.
9. Continue autonomously unless an exception requires renewed user input.
10. Stop at dynamic saturation or an approved resource boundary and deliver the source package.

Execution should pause for user direction only when:

- A promising branch materially changes the approved scope.
- An important new language, field, or jurisdiction must be added.
- Subscription or full-text access failures materially impair coverage.
- The approved budget is exhausted before the search approaches saturation.
- Expansion beyond the usual five-level guardrail is justified by continuing high-value discoveries.

## 6. Access and Language Policy

### 6.1 Access

Do not assume that subscription databases are inaccessible. Attempt access through the user's current environment, including institutional Wi-Fi, existing browser sessions, connected services, and user-authorized accounts.

For every source, record one access status:

- Full text read.
- Abstract only.
- Metadata only.
- Full text not read.
- Access failed.

A source may remain in the corpus when full text is unavailable, but the limitation must remain visible. Abstracts, snippets, metadata, and model memory must never be presented as full-text review.

### 6.2 Languages

English is the baseline language. Add languages adaptively when required by the tribunal's official languages, relevant state practice, regional scholarship, or the field's academic traditions. The search plan must explain the role of each proposed language and obtain user confirmation.

### 6.3 Local materials and privacy

User-authorized local PDFs, OCR outputs, bibliographies, Zotero libraries, and project files are first-class retrieval sources. Reuse local full text instead of downloading duplicates.

Public citation information found in local materials may be used in external queries, including titles, authors, DOIs, formal citations, case numbers, treaty identifiers, and published footnotes or references.

Do not send unpublished prose, private annotations, confidential facts, or non-public attachments to external search services. If publication status is unclear, keep the content local or ask the user before external use.

## 7. Source Policy

### 7.1 Source classes

Separate the corpus into:

- Primary international-law materials.
- Authoritative secondary materials.
- General academic materials.
- Institutional and other gray literature.
- Discovery-only leads.

Institutional reports and working papers may remain as a separate source class. Blogs, news, and ordinary web pages normally serve only as discovery leads unless they are themselves the object of research.

### 7.2 Core selection

Use a two-stage approach:

1. Prioritize conventional authority signals: leading judgments, authoritative instruments, recognized scholars, major monographs, and prominent journals.
2. Where conventional signals are absent or insufficient, consider direct relevance, citation-network position, unique provenance, temporal importance, and verifiability.

Traditional reputation is an important priority signal but does not replace identity verification or relevance checking.

Maintain two visible collections:

- Core or canonical materials.
- Supplementary or emerging materials, including recent decisions, regional practice, minority positions, and Global South scholarship.

## 8. Canonical Data Model

Each source is stored as a structured node with at least:

- Internal unique ID.
- External identifiers: DOI, formal citation, case number, treaty number, or document number.
- Title.
- Author, court, tribunal, organization, or issuing body.
- Date.
- Publication, forum, or issuing institution.
- Source type.
- Field and search subquestion.
- Authority class.
- Collection tier: core/canonical or supplementary/emerging.
- Access status.
- Stable URL and local path where applicable.
- Retrieval platform, retrieval time, and language.
- Brief description of what the source addresses.
- Brief inclusion reason.
- Basis for the description: full text, abstract, or metadata.
- Discovery query, source, footnote, or subagent.
- Identity and metadata verification status.
- Human-review requirement where unresolved.

The description field may summarize the individual source faithfully. It must not exceed the material actually read and must not turn into cross-source legal analysis.

## 9. Graph Model

Supported directed relationships include:

- `cites`
- `cited_by`
- `interprets`
- `same_case_series`
- `same_issue`
- `response_to`
- `discovered_from`

Every verified relationship records its evidence location, such as a page, paragraph, footnote, reference entry, or database citation record. An unconfirmed relationship is marked `candidate` and cannot be presented as verified.

Subagents submit candidate nodes and edges. Only the main agent merges them into the canonical graph.

## 10. Subagent Orchestration

Use subagents only when task complexity justifies parallel or specialized retrieval. Branches may be divided by:

- Legal subquestion.
- Source type.
- Platform or database.
- Language.
- Horizontal discovery versus vertical citation tracing.

Every subagent receives:

- The approved question and scope.
- Its assigned platform, language, source type, or graph branch.
- Known source IDs to reduce duplication.
- Current depth and maximum authorized depth.
- The canonical node and relationship schema.
- Explicit prohibitions on legal conclusions, fabricated sources, and false full-text claims.

The main agent must:

1. Merge candidate records.
2. Deduplicate by formal identifiers and normalized metadata.
3. Resolve metadata conflicts or preserve them for human review.
4. Reassess collection tiers.
5. Measure marginal discovery and open branches.
6. Decide whether to expand, reassign, ask the user, or stop.
7. Generate all user-facing and machine-readable outputs from the canonical corpus.

Subagent failure should affect only the assigned branch. Preserve completed work and retry, reassign, or disclose the gap.

## 11. Dynamic Saturation

After every retrieval round, record:

- New candidate count.
- New high-relevance count.
- New core-material count.
- Newly covered source types, themes, languages, and platforms.
- Duplicate ratio.
- Untraced high-value citation branches.
- Important sources lacking full-text access.

Do not use one fixed numeric threshold. Evidence of approaching saturation includes:

- Consecutive rounds produce few new high-relevance sources.
- New results are predominantly duplicates or low-relevance peripheral items.
- Core citation networks repeatedly point to existing nodes.
- Major subquestions, source classes, languages, and platforms have reasonable coverage.
- No high-value branch remains in rapid expansion.

Branches may saturate independently. Stop early when justified; request an expanded budget when high-value discoveries continue beyond the usual depth guardrail.

Every completed or paused run records a specific stopping reason.

## 12. Deliverables

The deliverable has two coordinated layers.

### 12.1 Raw and structured layer

- Canonical source records.
- Full citation graph and evidence locations.
- Retrieval and access provenance.
- Deduplication and verification status.
- Search queries and retrieval log.
- Coverage and unresolved-access data.
- User-selected CSV, JSONL, BibTeX, RIS, and graph exports.

### 12.2 Reader-facing layer

Available in Word, Markdown, or HTML, with:

- A concise thematic overview of the source groups found.
- Source-by-source descriptions of what each item addresses and why it appears.
- Selected key citation paths and their retrieval value.
- A coverage statement listing searched and unsearched platforms, languages, periods, source classes, and full-text gaps.
- Navigation by subquestion, theme, source type, chronology, or citation path.

The reader-facing layer may organize and describe the retrieved corpus. It must not synthesize legal rules, decide scholarly disputes, or construct the user's argument.

## 13. Error Handling

- Database unavailable: record the failure and try authoritative public alternatives.
- Abstract or metadata only: retain with the correct access label.
- Metadata conflict: preserve conflicting values and their sources until resolved.
- Unresolvable citation: create a candidate record with the citation text and provenance; do not invent missing fields.
- Scope drift: pause the branch and ask whether to include it.
- Tool failure or interruption: save a checkpoint and resume from unfinished branches.
- Budget reached before saturation: report present coverage and remaining branches for user decision.

## 14. Validation Strategy

### 14.1 Workflow tests

- Broad topics trigger interactive scoping.
- Defined questions, drafts, and seed PDFs use the correct intake path.
- Large-scale retrieval cannot begin before plan approval.
- Simple tasks avoid unnecessary subagents.
- Complex tasks split and merge correctly.
- Interrupted tasks resume from saved state.

### 14.2 Retrieval-quality tests

Benchmark topics should verify that the skill:

- Covers both primary and secondary sources.
- Finds a curated set of known canonical materials.
- Performs backward, forward, and lateral tracing.
- Deduplicates alternate versions and case-series records correctly.
- Separates core/canonical and supplementary/emerging materials.
- Preserves multilingual, regional, and Global South sources.
- Distinguishes full text, abstract, metadata, and failed access.
- Produces an explainable saturation decision.

### 14.3 Output and safety tests

- Word, Markdown, HTML, and structured exports agree on canonical fields.
- Formal identifiers and stable links are traceable.
- Source descriptions do not exceed the text actually accessed.
- Relationships have evidence locations or remain candidates.
- Unpublished local content is not sent externally.
- Outputs do not contain substantive legal synthesis or paper drafting.
- Reader-facing navigation remains traceable to raw records.

## 15. Acceptance Criterion

A user can begin with a topic, question, draft, or seed corpus; interactively approve a retrieval plan; and receive a resumable, auditable, multilingual international-law source package with primary and secondary materials, citation-network provenance, accurate access labels, useful reader-facing navigation, and an explicit in-scope saturation statement, without relying on fabricated or untraceable sources and without the skill performing the user's substantive research or writing.

