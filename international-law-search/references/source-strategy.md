# Source Strategy

Run primary international-law materials and secondary academic literature as separate, coordinated tracks. Search each approved subquestion in both tracks where relevant, and pass verified identifiers and citations between them without collapsing their authority classes.

## Version 1 scope

Version 1 covers general public international law, international human rights law, international humanitarian law, international criminal law, international investment law, the law of the sea, international environmental law, and international economic law.

Private international law, conflict of laws, and general cross-border commercial law are excluded. If a branch would require one of them, preserve the lead and seek renewed approval rather than silently expanding scope.

## Adaptive platform map

Build an adaptive platform map for the approved field, institutions, tribunals, states, languages, dates, and source types. Prefer authoritative originators and stable repositories, then add suitable legal or multidisciplinary indexes, publisher platforms, library discovery systems, repositories, and author or institution pages. Record which surfaces were selected and why. Do not treat a fixed platform list as exhaustive or assume that a platform remains available merely because it was useful in an earlier search.

For the primary track, retrieve relevant treaties, judgments, advisory opinions, orders, resolutions, institutional documents, and state practice from official or otherwise authoritative sources. For the secondary track, retrieve monographs, edited-volume chapters, commentaries, journal articles, working papers, and institutional research reports. Use each track to identify leads for the other while retaining provenance.

## Schema vocabulary

`source_track` classifies a retrieval branch as `primary`, `secondary`, or `mixed`; it describes how a branch is assigned, not the format or final authority classification of each item.

`source_type` records the document format or kind, such as treaty, judgment, advisory opinion, resolution, state-practice document, monograph, chapter, article, commentary, report, or working paper.

`authority_class` records the corpus class as `primary`, `authoritative_secondary`, `general_academic`, `gray_literature`, or `discovery_only`. It is not a scalar prestige score; apply conventional authority signals and the transparent ranking factors below separately.

`collection_tier` is a separate curatorial field using `core/canonical` or `supplementary/emerging`; it does not replace `source_track`, `source_type`, or `authority_class`.

## Ranking and collections

Start with conventional authority signals: leading judgments and instruments, recognized scholars, major monographs, and prominent journals. Authority is a priority signal, not a substitute for identity verification or relevance.

When conventional signals are absent, incomplete, or contested, apply and record transparent factors: direct relevance, citation-network centrality, unique provenance, recency, and verifiability. Do not convert these factors into an unexplained composite score.

Keep two visible collection tiers:

- `core/canonical`: sources central to the approved retrieval question under the stated authority and relevance criteria.
- `supplementary/emerging`: useful newer, less central, or differently situated sources that broaden or qualify coverage.

Preserve relevant regional practice, minority positions, multilingual materials, and Global South scholarship. Do not allow conventional prestige signals alone to erase them. Source class and collection tier remain separate fields.

## Gray literature

Retain authoritative institutional reports and working papers as gray literature in a distinct source class when they meet the approved criteria. Treat blogs, news, and ordinary web pages as discovery-only leads unless the item itself is the research object. Promote a lead only after resolving and verifying the underlying source.

## Languages

Use English as the baseline. Propose additional languages when justified by official languages, relevant state practice, regional scholarship, or field-specific academic traditions. State the retrieval purpose and expected coverage value of each language in the search plan and obtain user approval before adding it. A newly necessary language after approval triggers reapproval.
