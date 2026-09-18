# Access and Privacy

Apply this policy before intake inspects any file or collection. Before plan approval, permit only authorized local intake inspection needed to define the plan; an external query or search may begin only after explicit plan approval. Local access does not authorize external disclosure.

## Access attempts

After approval, do not assume that paid material is unavailable. Within the approved plan, try the user's current institutional Wi-Fi, authorized browser sessions, connected services, and subscriptions, then authoritative public alternatives where useful. Use only access already authorized by the user or provided by the current environment. Never bypass authentication, authorization, paywalls, or technical access controls.

Assign exactly one mutually exclusive source-level access status. Apply the first matching status in this precedence:

1. `Full text read`: substantive full text was examined.
2. `Full text not read`: a full-text work or copy is identified, but the full text was not examined because it was unavailable or intentionally unopened; the description basis may be abstract or metadata.
3. `Abstract only`: no full text is identified or available for the item, and an abstract was examined.
4. `Metadata only`: neither full text nor abstract was examined, but usable metadata exists.
5. `Access failed`: no usable source content was retrieved beyond the discovery citation or lead; retain it only as a candidate or limited record, and keep any description minimal with metadata basis.

Record every access attempt, successful or failed, as its own event in `retrieval_history`, including the platform, time, resulting access status, and available stable URL or local path. Across multiple attempts, the source-level status retains the most informative, highest-precedence outcome while `retrieval_history` preserves every route, including failed or weaker ones. A source may remain in the corpus without full text, but its source record and coverage statement must expose the limitation.

## Status examples

- A judgment whose merits section was opened and examined is `Full text read`.
- When a full-text copy is identified behind authorized access but remains unopened, an examined abstract still results in `Full text not read`.
- When no full text is identified or available but a publisher abstract is examined, use `Abstract only`.
- When a verified bibliographic record is the only examined material, use `Metadata only`.
- When a broken discovery lead yields no usable content or verified metadata, use `Access failed` and retain only a minimal candidate record.

## Description truthfulness

Record `description_basis` as a separate field from access status and link it to the retrieval event supporting the description. Its value reflects only the material used: full text, abstract, or metadata. Do not infer a source's argument from a title, snippet, citation, or model memory, and do not describe beyond the supporting material.

## Local materials

Treat user-authorized PDFs, OCR text, bibliographies, Zotero exports, and project folders as first-class retrieval sources. Reuse an authorized local copy instead of downloading a duplicate. Inspect only material placed in scope by the user.

Published citation information may be externalized for retrieval: titles, authors, DOIs, formal citations, case numbers, treaty or document identifiers, and published reference or footnote text.

Do not send unpublished prose, private annotations, confidential facts, non-public attachments, or other private content to external services. When publication status is ambiguous, keep the content local or ask the user for direction before externalizing it. A request to search a local collection does not waive these restrictions.
