# Search Plan

## Retrieval question

{{question}}

## User-approved scope and method

- Entry type: {{topic_question_draft_or_seed_corpus}}
- Included issues: {{included_issues}}
- Excluded issues: {{excluded_issues}}
- Period: {{date_range}}
- Source tracks: {{primary_and_secondary_source_tracks}}
- Languages and reasons: {{languages}}
- Access assumptions: {{access}}
- Initial resource budget: {{budget}}
- Depth guardrail: {{usual_and_maximum_depth}}
- Citation-tracing method: {{backward_forward_lateral_strategy}}
- Platforms/databases: {{platforms}}
- Output formats: {{output_formats}}
- Dynamic-saturation assessment: {{saturation_method}}
- Reapproval triggers: scope drift; new language, field, or jurisdiction; material access gap; budget reached before saturation; justified depth expansion.

## Internal execution appendix

Operational details below may evolve without reapproval only within the approved envelope above.

### Branch specification

Repeat this specification for every branch. A vertical branch cannot execute unless both depth fields are populated.

- Branch ID: {{branch_id}}
- Search subquestion: {{subquestion}}
- `source_track`: {{primary_or_secondary}}
- `retrieval_mode`: {{horizontal_discovery_or_vertical_tracing}}
- Starting depth: {{starting_depth}}
- Maximum authorized depth: {{maximum_authorized_depth}}
- Assigned platforms/databases: {{branch_platforms}}
- Exact query strings: {{queries}}
- Branch mechanics: {{branch_mechanics}}
- Local seeds: {{local_seeds}}
- Expected agent allocation: {{agent_plan}}
- Open risks: {{branch_risks}}

## Approval

Status: `{{pending_or_approved}}`
Approved by: {{user}}
Approved at: {{timestamp}}
Workspace state: {{workspace_state_path}}
Plan path: {{plan_path}}

Update all three fields atomically before execution. Approval is complete only after one coordinated checkpoint also writes `state.status=approved` and:

```json
{
  "approved_by": "{{user}}",
  "approved_at": "{{timestamp}}",
  "plan_path": "{{plan_path}}"
}
```

Store that object as `state.approved_plan`. Before external execution, re-read both artifacts and verify their status, user, timestamp, and plan path agree. If the checkpoint is interrupted or inconsistent, repair it from unambiguous explicit approval or seek user confirmation. Do not execute while the artifacts disagree.
