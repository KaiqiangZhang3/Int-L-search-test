# Intake and Approval

## Entry detection

Read `access-and-privacy.md` before inspecting any local file or collection. Then classify the input as a topic, question, draft, or seed corpus. Before asking questions, inspect only user-authorized local context for scope, existing sources, stated exclusions, dates, languages, and requested deliverables. Do not ask the user to repeat information that is already clear. This intake inspection does not authorize external searching or citation expansion.

## Adaptive questions

Ask one material question at a time. Skip settled issues and ask only about choices that can change retrieval:

- Objective, issue boundaries, and excluded issues.
- Relevant international-law fields, institutions, tribunals, or states.
- Desired primary-source and secondary-literature coverage.
- Date range and historical cutoff.
- Baseline and additional languages, with a retrieval reason for each.
- Quick, standard, deep, as-comprehensive-as-possible, or custom initial budget.
- Known authorities, authors, journals, databases, and local seed materials.
- Available subscription, institutional Wi-Fi, browser-session, and connected-service access.
- Required Word, Markdown, HTML, CSV, JSONL, BibTeX, RIS, retrieval-log, or graph output formats.

Presets establish an initial depth or resource budget. They do not establish the final stopping rule: assess dynamic saturation separately during execution.

## Search-plan construction

Split the request into searchable subquestions. Complete [`../templates/search-plan.md`](../templates/search-plan.md). Its user-approved section states the scope, source tracks, languages, access assumptions, initial budget, depth guardrail, exclusions, and output formats. Its internal appendix stores exact queries, branch mechanics, and assignments within that approved envelope. Every vertical branch must state its `source_track`, `retrieval_mode`, starting depth, and maximum authorized depth.

Present only the choices and constraints the user needs to review in a concise user-facing plan. Keep exact queries, branch mechanics, and other operational detail in the internal execution appendix; these details may evolve without reapproval only within the approved envelope.

Wait for explicit approval of the written plan. Do not infer approval from silence, a prior request to search, or permission to inspect local context. Do not begin external retrieval, database searching, or citation expansion before approval. Urgency does not override this gate; when time is limited, present a shorter provisional plan and still wait for explicit approval.

On explicit approval, write one coordinated checkpoint across the plan artifact and workspace `state.json`. In that checkpoint:

- Atomically set the plan status to `approved`, the approving user, and the approval timestamp.
- Set `state.status` to `approved`.
- Set `state.approved_plan` with `approved_by`, `approved_at`, and `plan_path` matching the plan artifact.

Approval is not complete until both artifacts have been updated. Before external execution, re-read the plan artifact and `state.json`; verify that both artifacts agree on approval status, user, timestamp, and plan path. If the checkpoint was interrupted or inconsistent, repair both artifacts only when the user's explicit approval is unambiguous; otherwise seek confirmation. Do not execute until the coordinated checkpoint is complete and consistent.

## Reapproval triggers

After approval, continue autonomously within the plan. Pause for renewed direction only when:

- A promising branch would materially change the approved scope.
- An important new language, field, or jurisdiction is needed.
- Subscription or full-text failures materially impair coverage.
- The approved resource budget ends before the search approaches dynamic saturation.
- High-value discoveries justify expansion beyond the usual depth guardrail.
