# Readiness and Research Scale

## Readiness threshold

Readiness is a decision aid, not a questionnaire to finish. Ask one material question at a time. Do not ask again for a fact that the user supplied or that reliable existing context already answers. Record each topic in the readiness matrix as `known`, `default_accepted`, `deferred`, or `not_applicable`, together with evidence whose origin is `user` or `existing_context`.

Stop intake once the next bounded round is designable. Uncertainty about the eventual thesis or final research question is not a blocker when an exploratory round can clarify it. A round is designable when its question, material inclusions and exclusions, source emphasis, language and access assumptions, round type, three-axis budget, output, and next checkpoint are sufficiently clear for the user to approve.

Ask about the following only when the answer could materially change the next round:

- research purpose and current writing stage;
- tentative question and known or uncertain disputes;
- inclusion, exclusion, date, region, jurisdiction, and institution boundaries;
- desired balance among primary materials, cases, state practice, doctrine, theory, and empirical work;
- languages and the research purpose of each language branch;
- existing sources, authors, bibliographies, reference libraries, PDFs, and local collections;
- desired footnote, reference, cited-by, and author-lineage tracing;
- database, institutional, subscription, library, interlibrary-loan, and physical-book access;
- research scale, interaction cadence, citation style, and output formats;
- HTML presentation preference; and
- whether this begins a project or supports a narrow claim during writing.

If the user does not know an answer, recommend a bounded default or mark the topic `deferred`; do not manufacture certainty. A default becomes `default_accepted` only after the user accepts it. Under a hard deadline, compress the same decisions into one concise scope card and explain the tradeoff between discovery, acquisition, and review.

## Scale profiles

These profiles are expectations, not quotas. Never add marginal material to reach a number, and never describe a discovered or acquired item as substantively reviewed.

| Profile | Bibliographic discovery expectation | Substantive review expectation | Typical use |
| --- | ---: | ---: | --- |
| Orientation | 15–30 | 5–10 | Initial map and bounded reading path |
| Seminar paper | 30–60 | 10–20 | Course or seminar paper |
| Thesis chapter | 60–120 | 15–30 | A substantial thesis or dissertation chapter |
| Doctoral corpus | 100–300+ over repeated rounds | Iterative and question-led | Dissertation-scale or long-running work |

The user may select a custom profile. The chosen profile informs planning across rounds; it does not authorize a single large retrieval round. Continue, narrow, pause, or close according to user decisions and evidence of convergence across positions, source genealogies, source types, periods, jurisdictions, regions, and languages.

## Readiness record

Use `schemas/readiness-matrix.schema.json`. The matrix must preserve the value and its basis, not merely a completion flag. Set `next_round_designable` to true only when a concise approval card can accurately state what the next round will and will not do. Keep unresolved but non-blocking questions in `remaining_material_questions` so later rounds can revisit them without repeating intake.
