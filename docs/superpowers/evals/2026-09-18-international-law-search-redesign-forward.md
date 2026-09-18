# International Law Search Redesign: Forward Evaluation

Date: 2026-09-18

## Method

Two fresh evaluators received only the finished skill directory and realistic
user prompts. They did not read the design specification, prior feedback,
implementation plan, or tests. They evaluated expected user-visible behavior
and artifacts rather than matching phrases in `SKILL.md`.

## Initial evaluation

| Scenario | Initial result | Observed behavior or gap |
| --- | --- | --- |
| Ambiguous corporate-role topic | Pass | The skill recommends Standard interactive mode, narrows scope through bounded exploration, and stops after breadth discovery for user seed selection. Project-level decisions were not yet guaranteed to persist across sessions. |
| Thirty-minute bibliography followed by later upgrade | Fail | The current-session upgrade reused the ledger, but Quick mode did not guarantee a resumable cross-session handoff. Deadline intake could also consume too much of the time budget. |
| Chinese and English retrieval with institutional access | Pass | Language branches were independent and availability was separated from actual review. The scope card did not yet expose branch details or distinguish network context, authentication, and verified source access. |
| Retrieval archive with source explanations | Pass | The archive boundary allowed per-source narrative descriptions and inclusion reasons without cross-source synthesis. Its repeated source layout was underspecified. |
| Research report plus a request to choose the thesis | Pass | The skill allowed sourced descriptive synthesis and refused thesis selection, but lacked a concise mixed-request response pattern. |
| Deep-audit search from published PDFs and private notes | Fail | Textual privacy rules and recovery fields existed, but vertical branches were not machine-linked to a user authorization decision and outbound privacy isolation lacked a deterministic gate. |

## Evaluation-supported corrections

1. Added a minimum resumable handoff for Quick and Standard modes, including
   project-level decisions, ledger location, pending choices, and open paths.
2. Added a hard-deadline intake path using one compact scope card after the
   topic is known, with an explicit candidate-count versus full-text-review
   tradeoff.
3. Expanded the scope card with output format, citation style, multilingual
   branch purpose, local vocabulary, platforms, branch budgets, and separate
   network, authentication, and verified-source-access fields.
4. Added a required deep-audit `decision_log`. Every vertical branch now links
   to a matching trace authorization whose seed and direction are checked by
   the corpus validator.
5. Added an atomic checkpoint tool for breadth pauses, seed approvals, budget
   pauses, failures, and resumptions. Seed approval creates or authorizes the
   vertical branch in the same atomic state replacement.
6. Added local-seed privacy classifications and an outbound manifest validator
   that rejects private or non-externalizable content and local paths.
7. Added a repeatable retrieval-archive item layout and a mixed-request rule
   that provides neutral argument paths while leaving thesis choice to the
   user.

## Verification

The corrected scenarios were returned to the original independent evaluators
for focused reassessment.

| Reassessed scenario | Final result | Basis |
| --- | --- | --- |
| Thirty-minute Quick search followed by later upgrade | Pass | The handoff and ledger preserve project- and source-level decisions across sessions; the hard-deadline path uses one compact approval card and states the candidate-versus-review tradeoff. |
| Chinese and English retrieval with institutional access | Pass | Each language branch now records purpose, local vocabulary, platforms, budget, access assumptions, and text-authority relationships; project access distinguishes network context, authentication, and verified source access. |
| Deep-audit local-seed project with private notes | Pass | Trace decisions require complete branch, seed, direction, and budget authorization; the validator cross-checks them. Pause and failure transitions atomically save recovery cursors and round evidence. Local discovery records carry privacy classifications, and outbound manifests reject private or local-path content. |

The evaluators reported no remaining blocking gap in the reassessed scope. A
manifest validator cannot prove that deliberately mislabeled prose is public,
so the structural checks remain paired with the rule that classification must
be based on publication status and that ambiguous material stays local.

The final automated verification must include the full unit suite, the official
skill package validator, and `git diff --check`.
