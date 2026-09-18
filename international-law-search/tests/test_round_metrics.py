from pathlib import Path
import importlib.util
import json
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "round_metrics.py"
ROOT = SCRIPT.parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location("round_metrics", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_record(record_id, relevance, collection_tier):
    return {
        "id": record_id,
        "external_ids": {},
        "title": f"Source {record_id}",
        "creators": ["Example Author"],
        "date": "2026",
        "publication": "Example Journal",
        "source_type": "journal_article",
        "fields": ["public international law"],
        "subquestions": ["q1"],
        "authority_class": "general_academic",
        "relevance": relevance,
        "collection_tier": collection_tier,
        "availability": "metadata_only",
        "review_extent": "metadata_verified",
        "stable_url": None,
        "local_path": None,
        "retrieval_history": [
            {
                "event_id": f"retrieval-{record_id}",
                "platform": "Example Index",
                "retrieved_at": "2026-09-17T00:00:00Z",
                "availability": "metadata_only",
                "review_extent": "metadata_verified",
                "stable_url": None,
                "local_path": None,
            }
        ],
        "language": "en",
        "description": "Metadata-only candidate used for metric testing.",
        "inclusion_reason": "Included to test round evidence.",
        "description_basis": {
            "kind": "metadata",
            "locations": ["Publisher record"],
        },
        "description_retrieval_id": f"retrieval-{record_id}",
        "discovery_history": [{"method": "query", "value": "test query"}],
        "verification": {
            "identity": "verified",
            "metadata_cross_checked": True,
            "human_review_required": False,
        },
    }


class RoundMetricTests(unittest.TestCase):
    def test_workflow_documents_endpoint_resolution_and_canonical_assignment(self):
        orchestration = (ROOT / "references" / "orchestration.md").read_text(
            encoding="utf-8"
        )
        graph = (ROOT / "references" / "graph-and-saturation.md").read_text(
            encoding="utf-8"
        )
        brief = (ROOT / "templates" / "subagent-brief.md").read_text(
            encoding="utf-8"
        )
        combined = orchestration + brief

        self.assertIn("known canonical ID", combined)
        self.assertIn("candidate_id submitted in the same return", combined)
        self.assertIn("relevance and collection_tier", orchestration)
        self.assertIn("before running round metrics", orchestration)
        self.assertIn("stores only `citing_node cites cited_node`", graph)
        self.assertIn("never a second stored edge", graph)
        self.assertNotIn("external source independently supplies", graph)

    def test_metrics_report_yield_without_automatic_stop(self):
        module = load_module()
        previous = [
            canonical_record("A", "high", "core/canonical"),
            canonical_record("B", "medium", "supplementary/emerging"),
        ]
        candidates = [
            canonical_record("B", "medium", "supplementary/emerging"),
            canonical_record("C", "high", "core/canonical"),
            canonical_record("D", "low", "supplementary/emerging"),
        ]

        result = module.calculate(
            previous,
            candidates,
            {
                "source_types": ["case_law"],
                "themes": ["attribution"],
                "languages": ["French"],
                "platforms": ["HUDOC"],
            },
            ["full-text:C"],
            ["forward:A"],
        )

        self.assertEqual(
            {
                "counts",
                "coverage_additions",
                "access_gaps",
                "open_high_value_branches",
            },
            set(result),
        )
        self.assertEqual(
            {
                "candidate_count": 3,
                "new_candidate_count": 2,
                "new_high_relevance_count": 1,
                "new_core_material_count": 1,
                "duplicate_count": 1,
                "duplicate_ratio": 1 / 3,
            },
            result["counts"],
        )
        self.assertEqual(["French"], result["coverage_additions"]["languages"])
        self.assertEqual(["full-text:C"], result["access_gaps"])
        self.assertEqual(["forward:A"], result["open_high_value_branches"])
        self.assertNotIn("decision", result)
        self.assertNotIn("saturation", result)
        self.assertNotIn("budget_status", result)

        state_schema = json.loads(
            (ROOT / "schemas" / "project-state.schema.json").read_text(
                encoding="utf-8"
            )
        )
        round_properties = state_schema["properties"]["rounds"]["items"][
            "properties"
        ]
        self.assertTrue(set(result).issubset(round_properties))
        self.assertEqual(
            set(round_properties["counts"]["properties"]),
            set(result["counts"]),
        )
        self.assertEqual(
            set(round_properties["coverage_additions"]["properties"]),
            set(result["coverage_additions"]),
        )

        source_schema = json.loads(
            (ROOT / "schemas" / "source-record.schema.json").read_text(
                encoding="utf-8"
            )
        )
        for record in previous + candidates:
            self.assertTrue(set(source_schema["required"]).issubset(record))
            self.assertTrue(set(record).issubset(source_schema["properties"]))
            self.assertIn(
                record["relevance"],
                source_schema["properties"]["relevance"]["enum"],
            )

    def test_empty_round_reports_zero_counts_and_all_coverage_dimensions(self):
        module = load_module()

        result = module.calculate([], [], {}, [], [])

        self.assertEqual(
            {
                "candidate_count": 0,
                "new_candidate_count": 0,
                "new_high_relevance_count": 0,
                "new_core_material_count": 0,
                "duplicate_count": 0,
                "duplicate_ratio": 0.0,
            },
            result["counts"],
        )
        self.assertEqual(
            {
                "source_types": [],
                "themes": [],
                "languages": [],
                "platforms": [],
            },
            result["coverage_additions"],
        )

    def test_duplicate_candidate_id_within_round_counts_once_as_new(self):
        module = load_module()
        duplicate = canonical_record("C", "high", "core/canonical")

        result = module.calculate([], [duplicate, dict(duplicate)], {}, [], [])

        self.assertEqual(2, result["counts"]["candidate_count"])
        self.assertEqual(1, result["counts"]["new_candidate_count"])
        self.assertEqual(1, result["counts"]["new_high_relevance_count"])
        self.assertEqual(1, result["counts"]["new_core_material_count"])
        self.assertEqual(1, result["counts"]["duplicate_count"])
        self.assertEqual(0.5, result["counts"]["duplicate_ratio"])

    def test_orchestration_is_mode_and_stage_aware(self):
        orchestration = (ROOT / "references" / "orchestration.md").read_text(
            encoding="utf-8"
        )
        brief = (ROOT / "templates" / "subagent-brief.md").read_text(
            encoding="utf-8"
        )
        combined = orchestration + brief

        self.assertIn("Initial Stage 1", orchestration)
        self.assertIn("must not launch vertical tracing", orchestration)
        self.assertIn("source-ledger-record.schema.json", combined)
        self.assertIn("deep-audit", combined)
        self.assertIn("optional edges", combined)
        self.assertIn("approved seed", combined)

    def test_graph_guidance_distinguishes_budget_pause_from_saturation(self):
        graph = (ROOT / "references" / "graph-and-saturation.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("budget_paused", graph)
        self.assertIn("cannot establish saturation", graph)
        self.assertIn("saturation_enabled", graph)
        self.assertIn("retrieval provenance", graph.lower())
        self.assertIn("not a relationship edge", graph.lower())


if __name__ == "__main__":
    unittest.main()
