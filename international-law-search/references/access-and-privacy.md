# Access and Privacy

Apply this policy before intake inspects any file or collection. Before plan approval, permit only authorized local intake inspection needed to define the plan; an external query or search may begin only after explicit plan approval. Local access does not authorize external disclosure.

## Access attempts

After approval, do not assume that paid material is unavailable. Within the approved plan, try the user's current institutional Wi-Fi, authorized browser sessions, connected services, and subscriptions, then authoritative public alternatives where useful. Use only access already authorized by the user or provided by the current environment. Never bypass authentication, authorization, paywalls, or technical access controls.

At project level, distinguish a reported network context from an authenticated session and from verified access to a specific source. Being on university Wi-Fi is an access assumption, not proof that a database session is authenticated; authentication is not proof that a particular full text opened successfully. Ask the user to authenticate only when an approved route requires it, and record source-level availability only after the source route succeeds.

Record source-level access on two independent evidence axes. `availability` records the best verified route currently known:

- `open_full_text`: full text is available through an authorized open or local route.
- `subscription_full_text`: full text is available through an authorized institutional or subscription route.
- `identified_inaccessible`: a full-text work or copy is identified, but the current authorized environment cannot retrieve it.
- `abstract_available`: an abstract is available, but no verified full-text route is currently available.
- `metadata_only`: usable bibliographic or official metadata is available, but no abstract or full-text route is verified.
- `access_failure`: the attempted route produced no usable source content or verified metadata.

`review_extent` records what the assistant actually examined through any authorized route:

- `full_text_substantively_reviewed`
- `selected_sections_reviewed`
- `abstract_reviewed`
- `metadata_verified`
- `not_reviewed`

Do not derive either axis from the other. Full-text availability does not mean that the text was read, and a failed route does not erase review completed through another route. A source may remain in the corpus without full text, but its record and coverage statement must expose both the access limitation and the actual review extent.

Record every access attempt, successful or failed, as its own event in `retrieval_history`, including platform, time, route-level `availability`, route-level `review_extent`, and any stable URL or local path. A metadata-only or abstract-only route cannot support selected-section or full-text review. A separate authorized local, open, or subscription route can support stronger review even when another attempt failed.

## Status examples

- A judgment available on an official website whose merits section was examined is `open_full_text` plus `selected_sections_reviewed`.
- A subscribed article whose publisher abstract was examined but whose PDF was not opened is `subscription_full_text` plus `abstract_reviewed`.
- A paywalled book chapter with no abstract is `identified_inaccessible` plus `metadata_verified` when its metadata was independently verified.
- A verified bibliographic record with no abstract or full-text route is `metadata_only` plus `metadata_verified`.
- A broken lead that yields no usable content or verified metadata is `access_failure` plus `not_reviewed` and remains only a minimal candidate.

## Description truthfulness

Record `description_basis` separately from both access axes and link it to the retrieval event supporting the description. Store its evidence kind and precise locations. Full-text descriptions require substantive full-text review; selected-section descriptions require those sections to have been reviewed; abstract descriptions require an examined abstract; metadata descriptions require verified metadata. Do not infer a source's argument from a title, snippet, citation, or model memory, and do not describe beyond the supporting material.

## Local materials

Treat user-authorized PDFs, OCR text, bibliographies, Zotero exports, and project folders as first-class retrieval sources. Reuse an authorized local copy instead of downloading a duplicate. Inspect only material placed in scope by the user.

Published citation information may be externalized for retrieval: titles, authors, DOIs, formal citations, case numbers, treaty or document identifiers, and published reference or footnote text.

Do not send unpublished prose, private annotations, confidential facts, non-public attachments, or other private content to external services. When publication status is ambiguous, keep the content local or ask the user for direction before externalizing it. A request to search a local collection does not waive these restrictions.
