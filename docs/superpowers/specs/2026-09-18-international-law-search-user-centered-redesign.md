# User-Centered International Law Search Redesign

## 1. Purpose

Refactor `international-law-search` into a user-centered academic research assistant for public international law. The skill should help users clarify a research question, explore a field in manageable rounds, choose which branches and sources deserve deeper retrieval, and receive readable, source-grounded outputs.

The existing audit engine remains valuable but becomes a mode-dependent backend. Machine artifacts must support the user experience rather than define it.

## 2. Product Principles

- User choices control scope, mode, seeds, depth, languages, budgets, stopping, and final outputs.
- A mode is an upgradeable service level, not a permanent fork. Existing sources, decisions, and provenance carry forward when a user moves from quick to standard or deep-audit mode.
- Retrieval proceeds in bounded rounds. The user sees substantive results before the search becomes large or expensive.
- Reader-facing outputs lead with field understanding, debates, and reading paths. Stable IDs, graph edges, state, and validation details remain available in the background.
- Source identity, access truthfulness, privacy, provenance, and non-exhaustiveness remain non-negotiable.
- Source-grounded descriptive synthesis is allowed only in research-report output. The skill does not select the user's position, turn disputed claims into settled law, provide unsupported legal conclusions, or draft the user's argumentative academic prose.

## 3. Modes and Upgrade Path

### 3.1 Quick mode

Quick mode supports time-bounded orientation and starting bibliographies. After minimum necessary clarification, it normally returns 10–20 reliable sources organized by theme and reading priority.

The user's approval of the quick-mode scope and budget also authorizes delivery when that budget is completed. Quick mode does not require a second closure confirmation unless the search encounters a material scope choice or the user asks to continue beyond the approved envelope.

Quick mode does not require a citation graph, canonical JSONL corpus, persistent project state, round metrics, or a recoverable audit workspace. It still requires verified source identity, honest availability and review labels, concise relevance descriptions, and disclosure of material gaps.

At delivery, the user may upgrade selected themes or sources into standard interactive mode or request a full deep-audit workspace. The upgrade reuses the existing source ledger and decisions.

### 3.2 Standard interactive mode

Standard interactive mode is the default recommendation for an ambiguous or substantial academic request. It uses:

1. Research interview and scope confirmation.
2. Breadth-first discovery.
3. A mandatory user decision checkpoint.
4. Depth-first tracing from user-confirmed seeds.
5. Optional targeted gap filling.
6. User-authorized closure and final delivery.

The user can delete or expand branches, select seeds, identify must-read materials, prohibit further tracing of an author or position, change language or date budgets, and stop at any checkpoint.

### 3.3 Deep-audit mode

Deep-audit mode supports systematic, long-running, recoverable, or reproducibility-sensitive projects. It enables the full canonical corpus, candidate and canonical record lifecycle, retrieval-event logs, project state, relationship graph, dynamic-saturation evidence, corpus-wide validation, and structured exports.

Deep-audit artifacts remain secondary in the user-facing package unless the user asks to inspect or analyze them.

Entering deep-audit mode requires persistent project state, canonical source records, retrieval logs, resumability, and corpus validation. Relationship graph construction and formal saturation analysis are enabled only when citation tracing or network coverage is part of the approved project; they are not mandatory for every deep-audit request.

## 4. Output Modes and Research Boundary

### 4.1 Retrieval archive

A retrieval archive organizes and faithfully describes sources without cross-source synthesis. It is appropriate when the user wants a bibliography, corpus, update set, or auditable retrieval package.

### 4.2 Research report

A research report may describe, with citations to reviewed sources:

- The field's conceptual boundaries and historical development.
- Major themes, scholarly positions, and disputes.
- Relationships among debates, institutions, cases, and instruments.
- Research gaps and underrepresented perspectives.
- A recommended reading path.

Every synthetic statement must be identifiable as one of:

- A position explicitly stated by a source.
- A trend supported by multiple sources.
- A cautious inference drawn from identified sources.

The report must not fabricate claims, exceed the material actually reviewed, present disputes as settled, choose the user's thesis, recommend an argumentative position, or become a paper section written on the user's behalf.

Standard-mode checkpoints may include the limited, cited descriptive synthesis needed to present a field map, debate map, and seed menu. This checkpoint synthesis follows the same evidence labels and boundaries as a research report but remains provisional and does not replace the final report.

## 5. Research Readiness and Interview

The skill uses an adaptive readiness assessment rather than a fixed questionnaire. It asks one material question at a time, skips facts already supplied, and normally resolves the following dimensions before external retrieval:

- Research purpose and intended use.
- Core research question, primary issue, and secondary issues.
- Included and excluded adjacent fields.
- Preferred emphasis: theory, doctrine, cases, institutions, practice, or empirical work.
- Relevant international-law fields, institutions, tribunals, states, or regions.
- Time period.
- Languages and the retrieval purpose of each language.
- Subscription, institutional Wi-Fi, browser-session, and connected-service access.
- Existing PDFs, bibliographies, Zotero collections, authors, or seed sources.
- Desired source count and full-text review depth.
- Output mode, format, citation style, and ordering preference.

A user may select recommended defaults. If the user cannot yet choose a research direction, the skill offers a bounded exploratory round rather than forcing premature decisions.

Readiness is reached when the next round has a sufficiently clear question, inclusions, exclusions, language scope, access assumptions, budget, and stopping checkpoint. The scope card shown for confirmation must remain concise.

## 6. Round-Based Interaction

### 6.1 Stage 0: scope confirmation

The stage-0 output contains only the tentative research question, inclusion and exclusion boundaries, languages, access assumptions, selected mode, next-round budget, and first-round directions. The user confirms or revises this scope before external retrieval.

Quick and standard modes may record approval in the conversation or a lightweight session record. Deep-audit mode retains the formal plan and synchronized project-state approval checkpoint.

### 6.2 Stage 1: breadth-first discovery

Stage 1 maps the field without systematic citation tracing. A typical standard-mode round collects 15–30 candidates across relevant positions, source types, periods, regions, and languages while reviewing only a bounded number of important full texts.

The checkpoint provides:

- A concise field map.
- An initial classified bibliography.
- One or two sentences explaining each source's relevance.
- Major debates and possible branches.
- Five to ten candidate seeds for deeper tracing.
- Planned and actual budget use.
- Coverage and access gaps.

The workflow must stop here. It cannot begin Stage 2 until the user selects or confirms seeds and directions.

### 6.3 Stage 2: depth-first tracing

Stage 2 traces only user-confirmed seeds. It may inspect backward citations, forward citers, explicit responses, criticism, extensions, and related institutional or procedural materials.

For each seed, the checkpoint identifies new sources, duplicates, distinct positions, evidence gaps, and untraced high-value paths. A source designated only for full-text review does not automatically become a tracing seed. Newly suggested seeds require user confirmation before expansion.

### 6.4 Stage 3: targeted gap filling

The user may authorize a targeted round for a particular language, region, court, organization, recent period, minority position, practitioner commentary, or unresolved subquestion. This stage is optional.

### 6.5 Stage 4: closure

In standard and deep-audit modes, the final report or archive is generated only after the user explicitly authorizes closure. Saying "stop and deliver the current result" is closure authorization and produces a report accurately labeled with its interim coverage status. At every earlier checkpoint, the user may continue, change direction, upgrade mode, downgrade scope, or stop with the current result. Quick-mode closure follows Section 3.1.

### 6.6 Round budgets

Each round exposes the applicable dimensions rather than only a total source count:

- Maximum search time.
- Platform or database count.
- Query count.
- Candidate-source count.
- Full-text or selected-section review count.
- Seed count.
- Per-seed tracing depth and maximum additions.
- Language allocation.
- Required source classes.
- Mandatory user checkpoint.

The checkpoint reports planned and actual use. A budget-limited round is labeled as budget-paused; it cannot be used by itself as evidence of saturation.

## 7. Source Ledger

### 7.1 Progressive records

Quick and standard modes use a concise source ledger with the fields needed for identity, truthfulness, relevance, and delivery. Deep-audit mode enriches the same records with complete retrieval events, merge history, verification data, stable internal IDs, and machine exports.

All modes share a minimum upgrade-safe ledger containing a stable session source key, normalized identity evidence, discovery provenance, availability, review extent, description basis, links or local location where permitted, and the user decisions that affect the source. A later upgrade may enrich these records but must not discard provenance, change identity silently, or overstate prior review.

### 7.2 Availability and review extent

Availability and actual review are independent axes.

`availability` values:

- `open_full_text`
- `subscription_full_text`
- `identified_inaccessible`
- `abstract_available`
- `metadata_only`
- `access_failure`

`review_extent` values:

- `full_text_substantively_reviewed`
- `selected_sections_reviewed`
- `abstract_reviewed`
- `metadata_verified`
- `not_reviewed`

`availability` records the best verified route known to the project, not merely the result of the latest attempt. Retrieval history may preserve weaker or failed routes. Review extent records what the agent actually examined through any authorized route, including a local copy. Combinations must be evidence-consistent: an abstract or metadata-only route cannot by itself support selected-section or full-text review, and an access failure cannot support review unless a separate successful route is recorded.

Substantive full-text review requires more than opening a page. For scholarship, it normally includes the abstract or opening, structure, conclusion, and sections directly relevant to the question. For legal materials, it includes the relevant provisions, paragraphs, procedural stage, or institutional context. Search snippets and indexed fragments never support `full_text_substantively_reviewed`.

Descriptions and synthesis cannot exceed the recorded review basis.

### 7.3 Reader-facing source fields

Each displayed source includes, where applicable:

- Normalized citation and useful links.
- Source type and legal status.
- Availability and review extent in reader-friendly language.
- What the source does.
- Why it is included.
- The position, method, or research direction it represents.
- Reading priority and a short reason.

Reading priorities are:

- Priority reading.
- Read according to research direction.
- Background or supplementary reading.

The ledger records relevant factors separately, including direct relevance, legal or institutional authority, scholarly influence, citation-network position, unique viewpoint, recency, regional or linguistic representation, verification strength, introductory value, and usefulness for a particular research issue. These factors do not become an unexplained composite score.

## 8. International-Law Source Rules

The source model distinguishes binding law, interpretive material, soft law, policy documents, scholarship, and commentary.

Legal status is contextual rather than a global `binding` boolean. Records identify the source category, issuing authority, addressees or parties, procedural posture, relevant jurisdictional context, and status date needed to understand its legal significance.

Type-specific metadata includes:

- Cases: court or tribunal, case number, decision date, procedural stage, and relevant paragraphs.
- Treaties: adoption, signature, entry into force, and relevant status information.
- International-organization documents: organization, organ, document number, session, version, and institutional status.
- Journal articles: journal, volume, issue, pages, and DOI.
- Books and chapters: publisher, edition, editors, ISBN, and chapter pages.
- Working papers and later publications: explicit version relationships rather than silent duplication.

Version relationships also cover original, revised, consolidated, corrected, interpreted, and implementation-stage texts; protocols and annexes; judgments and later correction, interpretation, or enforcement stages; and draft versus final international-organization documents.

The skill must distinguish international legal personality, subject status, procedural standing, direct rights, and direct obligations. It must not collapse corporate rights under investment law into corporate obligations in business and human rights. Domestic corporate-governance literature enters the corpus only when its connection to international norms is explicit and relevant to the approved question.

High-quality international-law blogs and practitioner commentary may appear in a separate commentary class when useful for recent developments or debate mapping. They must not be presented as binding authority or peer-reviewed scholarship.

Title capitalization differences do not create identity conflicts. A publication field cannot contain an entire formatted citation. Official, publisher, open-access, and other stable links remain separately identified. Unresolved identity or version issues must be resolved before final delivery or clearly disclosed.

## 9. Multilingual Retrieval

Each substantive retrieval language is a distinct branch with:

- A stated research purpose and expected coverage contribution.
- A local conceptual vocabulary and field-specific synonyms.
- Selected databases and access assumptions.
- A separate query, candidate, and review budget.
- A checkpoint statement of its marginal contribution.

A language branch cannot be implemented merely by translating English queries. For Chinese retrieval, the plan considers relevant Chinese academic terminology and available services such as CNKI, PKULaw, Wanfang, and institutional library access. Official texts, official translations, and unofficial translations must be distinguished.

Language selection is driven by the research question, not by a fixed English baseline. A lightweight auxiliary language used only to verify an isolated item may be recorded within an existing branch; any substantive new language branch with meaningful cost requires user confirmation. Where regional or Global South coverage matters, the plan states a concrete coverage objective, applicable languages or platforms, actual round results, and remaining gaps.

## 10. Subagent Orchestration

The main agent handles small, single-surface tasks. It delegates only when independent languages, platforms, source types, legal subquestions, or citation branches justify parallel or specialized retrieval.

Subagents may run horizontal discovery and user-approved vertical tracing concurrently only after the relevant vertical seeds and tracing budget have been approved. Initial Stage-1 breadth discovery cannot silently dispatch vertical tracing. The main agent alone controls the approved scope, user decisions, normalized source ledger, final corpus, and user-facing outputs.

In quick and standard modes, subagents may return concise candidate records. Full candidate schemas, candidate-edge lifecycles, and corpus-wide validation are mandatory only in deep-audit mode. A subagent cannot change scope, select final seeds, claim saturation, or maintain a competing canonical corpus.

## 11. Relationships and Citation Tracing

Citation tracing is optional. Stage 1 does not perform systematic tracing, and quick mode does not require a graph.

When enabled, relationships are separated into:

- Literature relationships: cites, responds to, criticizes, or extends.
- Institutional relationships: amends, implements, interprets, or belongs to the same proceeding or instrument series.
- Retrieval provenance: discovered through a query, platform, seed, footnote, bibliography, or subagent.

Retrieval provenance is not stored as a scholarly relationship. A database cited-by record proves a citation lead, not interpretation, criticism, or response. Judgmental relationships require locatable textual evidence. Thematic similarity is a tag or candidate grouping, not a verified edge.

Five levels is a possible guardrail for approved deep tracing, not a default target. Depth and per-seed additions are approved by the user. Dynamic saturation is a reasoned deep-search conclusion based on consecutive marginal yield, duplicate rates, coverage, access failures, and remaining high-value paths. No single metric establishes saturation.

## 12. Deliverables

### 12.1 Reader-facing package

For Chinese requests, headings, descriptions, status labels, and decision prompts are written in consistent natural Chinese. A research report is organized as:

1. Question definition and scope.
2. Field development and chronology.
3. Major themes, positions, and disputes.
4. Important institutions, instruments, and cases.
5. Research gaps and uncovered questions.
6. Recommended reading path.
7. Thematic annotated bibliography ordered by reading priority.
8. Coverage, access limitations, and concise method note.
9. User-selected appendices.

Each annotation answers what the source does, why it is included, and when it should be read. A timeline is added when chronology materially improves understanding.

The default organization is theme followed by reading priority. The user may instead order or navigate sources by chronology, authority, direct relevance, reading priority, position, or source type. The report and bibliography use the approved citation style, including OSCOLA, Bluebook, Chicago, or GB/T 7714 when selected.

The report distinguishes a search or corpus coverage gap from a source-supported claim that the literature itself contains a gap. A proposed literature gap based on incomplete evidence is labeled as a cautious inference requiring further verification.

The retrieval-archive format omits cross-source synthesis but retains thematic navigation, annotations, reading priority, coverage, and limitations.

### 12.2 Structured package

The reader-facing report may be delivered in Word, Markdown, or HTML as selected by the user. Default primary deliverables are the selected reader-facing report, annotated bibliography, and a CSV or XLSX bibliography when useful. Optional outputs include BibTeX, RIS, JSONL, retrieval logs, relationship data, project state, and validation results.

Reader-facing and structured outputs derive from the same source ledger. Internal IDs, English enums, edge statuses, and validation details do not lead the reader-facing report.

## 13. Privacy and Access Invariants

User-authorized PDFs, OCR, bibliographies, Zotero exports, and project folders are first-class sources. An authorized local copy should be reused where practical.

Only publicly published citation facts may be externalized for retrieval, including titles, authors, formal citations, identifiers, case or document numbers, and published footnote or reference text. Unpublished prose, private annotations, confidential facts, and non-public attachments remain local unless the user gives separate informed authorization.

The skill may use already authorized institutional Wi-Fi, browser sessions, subscriptions, and connected services. It must not bypass authentication, authorization, paywalls, or technical access controls. Failed access attempts and unread full text remain visible at the level appropriate to the selected mode.

Model memory is never retrieval or verification evidence. The skill never claims exhaustive coverage.

## 14. State and Upgrade Semantics

The workflow state must prevent unauthorized stage transitions. Standard mode minimally represents:

`intake_ready → round_1_approved → round_1_waiting_for_user → round_2_approved → round_2_complete → optional_gap_round → user_authorized_close`

Quick mode may end after its bibliography or upgrade into `round_1_waiting_for_user` with its existing materials treated as the breadth result. A standard project may upgrade to deep-audit mode by enriching existing records and creating the audit workspace; it must not discard prior provenance or silently relabel review extent.

The user may stop at any checkpoint. Stopping produces an interim package with an accurate status rather than forcing a final-saturation claim.

### 14.1 Existing-project migration

The redesign must preserve recoverability of existing version-1 workspaces. Migration is explicit and non-destructive:

- Old `access_status` values are mapped into proposed availability and review values, with ambiguous cases flagged rather than guessed.
- Existing canonical IDs remain aliases or stable identifiers in migrated records.
- Historical retrieval events, approval state, round evidence, and coverage data remain available.
- Existing edges are separated into literature, institutional, or retrieval-provenance records; judgmental relations without sufficient evidence remain candidates.
- Original workspace files are retained until the migrated corpus validates successfully.

The migration tool or procedure reports every lossy or ambiguous conversion and never upgrades a prior access or review claim without supporting evidence.

## 15. Error Handling

- Platform failure: record the failure, try approved authoritative alternatives, and expose material coverage gaps.
- Access failure: retain the verified identity when useful, label availability and review accurately, and do not infer the source's argument.
- Metadata conflict: preserve attributed alternatives until resolved; do not silently overwrite identifiers or versions.
- Budget exhaustion: pause with planned-versus-actual usage and concrete continuation choices.
- Scope drift: preserve the lead and request direction before expanding.
- Interrupted branch: retain completed work and resume only unfinished branches.
- Validation failure in deep-audit mode: block affected structured exports until corrected; do not block an unrelated reader-facing interim report if its underlying records remain trustworthy and the limitation is disclosed.

## 16. Behavioral Acceptance Tests

The real user-feedback request concerning the role of corporations in public international law serves as the redesign's baseline failure case. Acceptance is based on observable agent behavior rather than keyword-only file checks.

Required scenarios include:

1. An ambiguous corporate-role topic triggers adaptive issue clarification instead of immediate broad retrieval.
2. Stage 1 stops after breadth discovery and asks the user to select branches and seeds.
3. Stage 2 traces only user-confirmed seeds and honors deleted branches and read-only sources.
4. Quick mode returns a reliable lightweight bibliography without mandatory graph or audit artifacts.
5. A quick result upgrades without loss into standard or deep-audit mode.
6. Chinese retrieval uses an independent vocabulary, platform plan, budget, and coverage account.
7. Availability and review extent accept valid combinations and reject snippet-based full-text claims.
8. A Chinese reader-facing report leads with field understanding, debates, and reading priorities rather than IDs and edge tables.
9. Retrieval archive and research report enforce different synthesis boundaries against the same corpus.
10. Deep-audit mode preserves recoverability, privacy, deduplication, evidence-bearing relationships, and corpus validation.
11. Budget-limited stopping cannot be mislabeled as saturation.
12. User authorization is required before closure and before every substantive mode, scope, language, seed, or depth expansion.

## 17. Implementation Strategy

Implementation proceeds through vertical behavior slices:

1. Research readiness and concise scope confirmation.
2. Stage-1 checkpoint and user-owned seed selection.
3. Quick mode and lossless mode upgrades.
4. Two-axis availability and review model.
5. Reader-first reporting and mode-specific synthesis.
6. Independent multilingual branches.
7. Optional relationship graph and deep-audit compatibility.

Each slice begins with a failing behavior or contract test, implements the minimum coherent change, and preserves already passing privacy, identity, and provenance invariants. Existing tests that enforce the rejected one-plan workflow, single access status, universal no-synthesis boundary, or graph-first report must be migrated rather than treated as valid regressions.

## 18. Success Criteria

The redesign succeeds when a user can begin with an uncertain international-law topic, progressively shape the project through meaningful choices, receive useful results after each bounded round, understand what to read and why without inspecting machine files, and deepen the same project without restarting. The skill must retain auditable truthfulness and privacy while making those controls largely invisible until the user needs them.
