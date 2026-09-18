# International Law Search: Live End-to-End Evaluation

Date: 2026-09-17

Machine-verifiable fixture: [`fixtures/nicaragua-e2e/`](fixtures/nicaragua-e2e/)

## Purpose

Test the skill against a constrained public-international-law retrieval task using live web sources. The approved task was to build a shallow citation network around the ICJ's 1986 *Military and Paramilitary Activities in and against Nicaragua* merits judgment. The test did not authorize legal synthesis, argument selection, or academic drafting.

## Approved limits

- One horizontal discovery round and one vertical citation-following round.
- English-language materials were sufficient for this smoke test.
- Primary authorities and a small scholarship sample were in scope.
- Stop when the approved round and depth budget was exhausted; do not claim saturation.

## Retrieved nodes

| Material | Type | Availability | Review extent | Why included |
| --- | --- | --- | --- | --- |
| [ICJ, *Nicaragua v. United States*, Merits (1986)](https://www.icj-cij.org/node/103143) | Judgment | Open full text | Full text substantively reviewed | Seed authority and source of verified citation edges. |
| [Charter of the United Nations](https://www.un.org/en/node/125814) | Treaty | Open full text | Full text substantively reviewed | Primary authority cited in the seed judgment. |
| [UNGA Resolution 2625 (XXV)](https://docs.un.org/en/A/RES/2625(XXV)) | Resolution | Open full text | Full text substantively reviewed | Primary authority cited in the seed judgment. |
| [P. P. Rijpkema, “Customary International Law in the Nicaragua Case”](https://doi.org/10.1017/S0167676800001951) | Scholarship | Metadata only | Metadata verified | Scholarship discovered in the horizontal round; retained with an accurate access label. |
| [Roman Kwiecień, “The Nicaragua Judgement and the Use of Force – 30 Years Later”](https://ssrn.com/abstract=3025599) | Scholarship | Abstract available | Abstract reviewed | Later scholarly treatment discovered in the horizontal round. |
| [ICJ, *Oil Platforms*, Judgment (2003)](https://www.icj-cij.org/node/103215) | Judgment | Open full text | Full text substantively reviewed | Later authority that cites the seed judgment. |

## Verified paths

- *Nicaragua* paragraphs 176, 188, and 193 support citation links to the UN Charter and Resolution 2625.
- *Oil Platforms* paragraphs 43 and 76 support backward links to *Nicaragua*; the canonical graph stores these in the one-way `cites` direction.
- The scholarship records were retained as discovered nodes without inventing citation edges that were not verified from accessible text.

## Coverage and stopping statement

The exercise covered official ICJ and UN sources plus Cambridge and SSRN discovery surfaces. It demonstrated primary-source retrieval, later-case tracing, mixed access states, and evidence-bearing graph edges. It did not establish multilingual, database-wide, or subject-wide coverage. Retrieval stopped because the approved round and depth budget was exhausted, not because the network was saturated.

## Result

Pass. The skill supported the intended retrieval-only workflow and preserved the distinction between verified evidence, discoverable metadata, and unread full text. The exercise also confirmed that user-facing summaries can remain concise while the raw corpus retains source identity, availability, review extent, discovery provenance, and edge evidence. The version-2 fixture enables the graph while leaving saturation assessment disabled, because the approved budget—not saturation—caused retrieval to stop.
