# International-Law Search Results

Generated from the canonical corpus at `{{export_checkpoint}}`. Reader format: `{{word_markdown_or_html}}`.

## Scope, stopping reason, and coverage conclusion

{{approved_scope_and_stopping_reason}}

Coverage conclusion: {{coverage_conclusion}}

Use only `Approaches saturation within the approved scope`, `Paused—not saturated: {{reason}}`, or `In progress—not saturated: {{reason}}`. It must not claim exhaustive coverage.

## Retrieval-oriented navigation

- Approved subquestion: {{approved_subquestion_navigation}}
- Theme: {{theme_navigation}}
- Source type: {{source_type_navigation}}
- Chronology: {{chronology_navigation}}
- Citation path: {{citation_path_navigation}}

## Core/canonical sources

For each selected source:

- `{{stable_id}}` — {{citation}}
  - Access status: {{access_status}}
  - Description basis: {{description_basis}}
  - What the source addresses: {{source_description}}
  - Why it was included: {{inclusion_reason}}

## Supplementary/emerging sources

{{selected_supplementary_sources_using_the_same_fields}}

## Key citation paths

Path retrieval value: {{retrieval_value}}

| From ID | Canonical relation | To ID | Status | Evidence location |
| --- | --- | --- | --- | --- |
| {{from_id}} | {{relation}} | {{to_id}} | {{edge_status}} | {{evidence_location}} |

List each edge separately. Candidate status must remain visible even when an evidence location is present.

## Coverage and gaps

Populate this table from the cumulative `coverage` object in project state at
the export checkpoint.

| Dimension | Searched | Not searched |
| --- | --- | --- |
| Approved subquestion | {{searched_subquestions}} | {{not_searched_subquestions}} |
| Platform | {{searched_platforms}} | {{not_searched_platforms}} |
| Language | {{searched_languages}} | {{not_searched_languages}} |
| Period / chronology | {{searched_periods}} | {{not_searched_periods}} |
| Source class | {{searched_source_classes}} | {{not_searched_source_classes}} |

- Full-text gap: `{{gap_source_id}}` — {{full_text_gap}}
- Verification gap (source): `{{gap_source_id}}` — {{source_verification_gap}}
- Verification gap (edge): `{{gap_from_id}}` | `{{gap_relation}}` | `{{gap_to_id}}` | `{{gap_edge_status}}` — {{edge_verification_gap}}

Every gap entry must use one of these source or edge identifiers. Record unsearched surfaces in the coverage table rather than as untraceable gap prose.

This concise report and the structured exports derive from the same corpus checkpoint. Use stable IDs to trace entries to canonical records. It does not synthesize legal rules, resolve scholarly disputes, recommend an argument, or draft academic prose.
