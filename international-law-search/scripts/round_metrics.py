#!/usr/bin/env python3


def calculate(previous, candidates, coverage_additions, access_gaps, open_branches):
    """Measure canonicalized source records without making a stop decision."""
    previous_ids = {item["id"] for item in previous}
    seen_ids = set(previous_ids)
    new_items = []
    for item in candidates:
        if item["id"] in seen_ids:
            continue
        seen_ids.add(item["id"])
        new_items.append(item)
    duplicate_count = len(candidates) - len(new_items)

    return {
        "counts": {
            "candidate_count": len(candidates),
            "new_candidate_count": len(new_items),
            "new_high_relevance_count": sum(
                item["relevance"] == "high" for item in new_items
            ),
            "new_core_material_count": sum(
                item["collection_tier"] == "core/canonical" for item in new_items
            ),
            "duplicate_count": duplicate_count,
            "duplicate_ratio": (
                duplicate_count / len(candidates) if candidates else 0.0
            ),
        },
        "coverage_additions": {
            dimension: sorted(set(coverage_additions.get(dimension, [])))
            for dimension in ("source_types", "themes", "languages", "platforms")
        },
        "access_gaps": sorted(set(access_gaps)),
        "open_high_value_branches": sorted(set(open_branches)),
    }
