from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SchemaTests(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))

    def assert_access_combination_allowed(self, schema, record):
        self.assertIn(record["availability"], schema["properties"]["availability"]["enum"])
        allowed_reviews = set(schema["properties"]["review_extent"]["enum"])
        kind = record["description_basis"]["kind"]
        for rule in schema.get("allOf", []):
            kind_rule = (
                rule.get("if", {})
                .get("properties", {})
                .get("description_basis", {})
                .get("properties", {})
                .get("kind", {})
            )
            if kind_rule.get("const") == kind:
                allowed_reviews &= set(
                    rule["then"]["properties"]["review_extent"]["enum"]
                )
        self.assertIn(record["review_extent"], allowed_reviews)

    def canonical_record(self, **overrides):
        record = {
            "id": "source-1",
            "external_ids": {"doi": "10.1000/example"},
            "title": "Example",
            "creators": ["Researcher"],
            "date": "2026",
            "publication": "Journal",
            "source_type": "journal_article",
            "fields": ["international law"],
            "subquestions": ["corporate roles"],
            "authority_class": "general_academic",
            "collection_tier": "core/canonical",
            "relevance": "high",
            "availability": "metadata_only",
            "review_extent": "metadata_verified",
            "stable_url": "https://example.test/source-1",
            "local_path": None,
            "retrieval_history": [
                {
                    "event_id": "event-1",
                    "platform": "Publisher",
                    "retrieved_at": "2026-09-18T00:00:00Z",
                    "availability": "metadata_only",
                    "review_extent": "metadata_verified",
                    "stable_url": "https://example.test/source-1",
                    "local_path": None,
                }
            ],
            "language": "en",
            "description": "The article addresses corporate roles.",
            "inclusion_reason": "It directly addresses the research question.",
            "description_basis": {
                "kind": "metadata",
                "locations": ["Publisher record"],
            },
            "description_retrieval_id": "event-1",
            "discovery_history": [{"method": "query", "value": "corporate role"}],
            "verification": {
                "identity": "verified",
                "metadata_cross_checked": True,
                "human_review_required": False,
            },
        }
        record.update(overrides)
        return record

    def test_subscription_full_text_can_coexist_with_abstract_review(self):
        schema = self.load("source-record.schema.json")
        record = self.canonical_record(
            availability="subscription_full_text",
            review_extent="abstract_reviewed",
            description_basis={
                "kind": "abstract",
                "locations": ["Publisher abstract"],
            },
            retrieval_history=[
                {
                    "event_id": "event-1",
                    "platform": "Publisher",
                    "retrieved_at": "2026-09-18T00:00:00Z",
                    "availability": "subscription_full_text",
                    "review_extent": "abstract_reviewed",
                    "stable_url": "https://example.test/source-1",
                    "local_path": None,
                }
            ],
        )

        self.assert_access_combination_allowed(schema, record)

    def allowed_reviews_for_description_basis(self, schema, basis):
        all_reviews = set(schema["properties"]["review_extent"]["enum"])
        for rule in schema.get("allOf", []):
            basis_rule = (
                rule.get("if", {})
                .get("properties", {})
                .get("description_basis", {})
                .get("properties", {})
                .get("kind", {})
            )
            if basis_rule.get("const") == basis:
                return set(
                    rule["then"]["properties"]["review_extent"]["enum"]
                )
        return all_reviews

    def allowed_reviews_for_retrieval_route(self, schema, availability):
        event = schema["properties"]["retrieval_history"]["items"]
        all_reviews = set(event["properties"]["review_extent"]["enum"])
        for rule in event.get("allOf", []):
            route_rule = (
                rule.get("if", {})
                .get("properties", {})
                .get("availability", {})
            )
            if route_rule.get("const") == availability:
                return set(rule["then"]["properties"]["review_extent"]["enum"])
        return all_reviews

    def test_metadata_route_cannot_support_section_or_full_text_review(self):
        for name in (
            "source-record.schema.json",
            "candidate-source-record.schema.json",
        ):
            with self.subTest(schema=name):
                schema = self.load(name)
                self.assertEqual(
                    {"metadata_verified", "not_reviewed"},
                    self.allowed_reviews_for_retrieval_route(
                        schema, "metadata_only"
                    ),
                )

    def approved_plan_type_for_status(self, schema, status):
        for rule in schema.get("allOf", []):
            status_rule = rule.get("if", {}).get("properties", {}).get("status", {})
            if status_rule.get("const") == status or status in status_rule.get(
                "enum", []
            ):
                return rule["then"]["properties"]["approved_plan"]["type"]
        return schema["properties"]["approved_plan"]["type"]

    def test_source_schema_preserves_an_auditable_canonical_record(self):
        schema = self.load("source-record.schema.json")
        required = set(schema["required"])

        self.assertTrue(
            {
                "id",
                "title",
                "source_type",
                "subquestions",
                "authority_class",
                "collection_tier",
                "availability",
                "review_extent",
                "language",
                "description",
                "inclusion_reason",
                "description_basis",
                "discovery_history",
                "verification",
            }.issubset(required)
        )
        self.assertNotIn("discovery", schema["properties"])
        self.assertEqual(
            [
                "open_full_text",
                "subscription_full_text",
                "identified_inaccessible",
                "abstract_available",
                "metadata_only",
                "access_failure",
            ],
            schema["properties"]["availability"]["enum"],
        )
        self.assertEqual(
            [
                "full_text_substantively_reviewed",
                "selected_sections_reviewed",
                "abstract_reviewed",
                "metadata_verified",
                "not_reviewed",
            ],
            schema["properties"]["review_extent"]["enum"],
        )
        self.assertEqual(
            ["full_text", "selected_sections", "abstract", "metadata"],
            schema["properties"]["description_basis"]["properties"]["kind"][
                "enum"
            ],
        )
        self.assertEqual(
            "object", schema["properties"]["merge_conflicts"]["type"]
        )

    def test_source_schema_supports_non_destructive_migration_markers(self):
        schema = self.load("source-record.schema.json")

        self.assertEqual(
            {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "uniqueItems": True,
            },
            schema["properties"]["legacy_ids"],
        )
        self.assertEqual(
            {"type": "boolean"},
            schema["properties"]["migration_review_required"],
        )

    def test_case_extension_records_procedural_context(self):
        schema = self.load("source-record.schema.json")
        case = schema["$defs"]["case_details"]

        self.assertTrue(
            {"court", "decision_date", "procedural_stage"}.issubset(
                case["required"]
            )
        )

    def test_source_schema_exposes_type_specific_details(self):
        schema = self.load("source-record.schema.json")
        expected = {
            "case_details",
            "treaty_details",
            "international_organization_document_details",
            "article_details",
            "book_details",
            "chapter_details",
            "working_paper_details",
            "institutional_report_details",
            "commentary_details",
        }

        self.assertTrue(expected.issubset(schema["$defs"]))
        article = schema["$defs"]["article_details"]
        self.assertIn("journal", article["required"])
        self.assertTrue(
            {"journal", "volume", "issue", "pages"}.issubset(
                article["properties"]
            )
        )
        self.assertIn("source_details", schema["properties"])
        self.assertIn("legal_status_context", schema["properties"])
        self.assertIn("version_relationships", schema["properties"])
        self.assertIn("links", schema["properties"])

    def test_lightweight_ledger_preserves_type_details_for_mode_upgrades(self):
        schema = self.load("source-ledger-record.schema.json")

        self.assertIn("source_details", schema["properties"])
        self.assertIn("article_details", schema["$defs"])
        self.assertIn(
            "journal", schema["$defs"]["article_details"]["required"]
        )
        self.assertIn("case_details", schema["$defs"])
        self.assertIn("legal_status_context", schema["properties"])

    def test_candidate_source_schema_accepts_unresolved_submissions(self):
        schema = self.load("candidate-source-record.schema.json")
        required = set(schema["required"])

        self.assertEqual(
            {
                "candidate_id",
                "discovery_history",
                "availability",
                "review_extent",
                "description_basis",
                "description",
                "description_retrieval_id",
                "retrieval_history",
            },
            required,
        )
        self.assertNotIn("collection_tier", schema["properties"])
        self.assertNotIn("verification", schema["properties"])
        for field in (
            "title",
            "creators",
            "external_ids",
            "raw_citation_text",
            "source_type",
            "authority_class",
            "language",
            "relevance",
        ):
            with self.subTest(field=field):
                self.assertIn("null", schema["properties"][field]["type"])

    def test_candidate_description_basis_matches_review_evidence(self):
        schema = self.load("candidate-source-record.schema.json")

        self.assertEqual(
            {"full_text_substantively_reviewed"},
            self.allowed_reviews_for_description_basis(schema, "full_text"),
        )
        self.assertEqual(
            {
                "full_text_substantively_reviewed",
                "selected_sections_reviewed",
                "abstract_reviewed",
            },
            self.allowed_reviews_for_description_basis(schema, "abstract"),
        )
        self.assertNotIn(
            "not_reviewed",
            self.allowed_reviews_for_description_basis(schema, "metadata"),
        )

    def test_candidate_description_links_to_a_retrieval_event(self):
        schema = self.load("candidate-source-record.schema.json")

        self.assertIn("description_retrieval_id", schema["required"])
        self.assertEqual(
            "string",
            schema["properties"]["description_retrieval_id"]["type"],
        )
        self.assertEqual(
            1,
            schema["properties"]["description_retrieval_id"]["minLength"],
        )
        self.assertIn(
            "event_id",
            schema["properties"]["retrieval_history"]["items"]["required"],
        )

    def test_source_schema_links_descriptions_to_retrieval_events(self):
        schema = self.load("source-record.schema.json")
        required = set(schema["required"])

        self.assertNotIn("retrieval", schema["properties"])
        self.assertTrue(
            {"retrieval_history", "description_retrieval_id"}.issubset(required)
        )
        event = schema["properties"]["retrieval_history"]["items"]
        self.assertTrue(
            {
                "event_id",
                "platform",
                "retrieved_at",
                "availability",
                "review_extent",
                "stable_url",
                "local_path",
            }.issubset(event["required"])
        )
        self.assertEqual(
            schema["properties"]["availability"]["enum"],
            event["properties"]["availability"]["enum"],
        )
        self.assertEqual(
            schema["properties"]["review_extent"]["enum"],
            event["properties"]["review_extent"]["enum"],
        )

    def test_description_basis_is_compatible_with_review_extent(self):
        schema = self.load("source-record.schema.json")

        self.assertEqual(
            {"full_text_substantively_reviewed"},
            self.allowed_reviews_for_description_basis(schema, "full_text"),
        )
        self.assertEqual(
            {
                "full_text_substantively_reviewed",
                "selected_sections_reviewed",
                "abstract_reviewed",
            },
            self.allowed_reviews_for_description_basis(schema, "abstract"),
        )
        self.assertEqual(
            {
                "full_text_substantively_reviewed",
                "selected_sections_reviewed",
                "abstract_reviewed",
                "metadata_verified",
            },
            self.allowed_reviews_for_description_basis(schema, "metadata"),
        )

    def test_source_schema_preserves_aliases_and_attributed_conflicts(self):
        schema = self.load("source-record.schema.json")
        aliases = schema["properties"]["aliases"]
        conflict_candidate = schema["properties"]["merge_conflicts"][
            "additionalProperties"
        ]["items"]

        self.assertTrue(aliases["uniqueItems"])
        self.assertEqual(1, aliases["items"]["minLength"])
        self.assertEqual(
            {"value", "source_record_id"}, set(conflict_candidate["required"])
        )
        self.assertEqual(
            1,
            conflict_candidate["properties"]["source_record_id"]["minLength"],
        )

    def test_canonical_source_requires_a_relevance_level(self):
        schema = self.load("source-record.schema.json")

        self.assertIn("relevance", schema["required"])
        self.assertEqual(
            ["high", "medium", "low"],
            schema["properties"]["relevance"]["enum"],
        )

    def test_canonical_source_requires_nonempty_reader_descriptions(self):
        schema = self.load("source-record.schema.json")

        self.assertEqual(1, schema["properties"]["description"]["minLength"])
        self.assertEqual(
            1, schema["properties"]["inclusion_reason"]["minLength"]
        )

    def test_edge_schema_requires_evidence_only_for_verified_edges(self):
        schema = self.load("edge-record.schema.json")

        self.assertEqual(
            ["verified", "candidate"], schema["properties"]["status"]["enum"]
        )
        self.assertNotIn("evidence", schema["required"])
        verified_rule = next(
            rule
            for rule in schema["allOf"]
            if rule["if"]["properties"].get("status", {}).get("const")
            == "verified"
        )
        candidate_rule = next(
            rule
            for rule in schema["allOf"]
            if rule["if"]["properties"].get("status", {}).get("const")
            == "candidate"
        )
        self.assertIn("evidence", verified_rule["then"]["required"])
        self.assertNotIn("required", candidate_rule["then"])

    def test_edge_schema_separates_candidate_and_canonical_storage(self):
        schema = self.load("edge-record.schema.json")

        self.assertIn("record_scope", schema["required"])
        self.assertEqual(
            ["candidate", "canonical"],
            schema["properties"]["record_scope"]["enum"],
        )
        canonical_rule = next(
            rule
            for rule in schema["allOf"]
            if rule["if"]["properties"].get("record_scope", {}).get("const")
            == "canonical"
        )
        self.assertNotIn(
            "cited_by",
            canonical_rule["then"]["properties"]["relation"]["enum"],
        )
        self.assertIn("cited_by", schema["properties"]["relation"]["enum"])

    def test_edge_schema_separates_relation_families_from_provenance(self):
        schema = self.load("edge-record.schema.json")
        relations = set(schema["properties"]["relation"]["enum"])

        self.assertIn("relation_family", schema["required"])
        self.assertEqual(
            {"literature", "institutional"},
            set(schema["properties"]["relation_family"]["enum"]),
        )
        self.assertTrue(
            {"cites", "cited_by", "responds_to", "criticizes", "extends"}
            .issubset(relations)
        )
        self.assertTrue(
            {"amends", "implements", "interprets", "same_proceeding"}
            .issubset(relations)
        )
        self.assertNotIn("discovered_from", relations)
        self.assertNotIn("same_issue", relations)

    def test_judgmental_relations_require_locatable_textual_evidence(self):
        schema = self.load("edge-record.schema.json")
        judgmental = {"responds_to", "criticizes", "extends", "interprets"}
        rule = next(
            item
            for item in schema["allOf"]
            if set(
                item.get("if", {})
                .get("properties", {})
                .get("relation", {})
                .get("enum", [])
            )
            == judgmental
        )

        self.assertIn("evidence", rule["then"]["required"])
        self.assertEqual(
            "object", rule["then"]["properties"]["evidence"]["type"]
        )

    def test_state_schema_tracks_approval_rounds_branches_and_stopping(self):
        schema = self.load("project-state.schema.json")
        required = set(schema["required"])

        self.assertTrue(
            {
                "schema_version",
                "graph_enabled",
                "saturation_enabled",
                "approved_plan",
                "branches",
                "rounds",
                "stopping",
            }.issubset(required)
        )
        self.assertEqual(2, schema["properties"]["schema_version"]["const"])
        self.assertEqual("boolean", schema["properties"]["graph_enabled"]["type"])
        self.assertEqual(
            "boolean", schema["properties"]["saturation_enabled"]["type"]
        )
        self.assertEqual(
            ["continue", "pause_for_user", "stop"],
            schema["properties"]["stopping"]["properties"]["decision"]["enum"],
        )
        self.assertIn(
            "open_high_value_branches",
            schema["properties"]["stopping"]["required"],
        )

    def test_state_schema_requires_cumulative_searched_and_unsearched_coverage(self):
        schema = self.load("project-state.schema.json")

        self.assertIn("coverage", schema["required"])
        coverage = schema["properties"]["coverage"]
        dimensions = {
            "subquestions",
            "platforms",
            "languages",
            "periods",
            "authority_classes",
        }
        self.assertEqual(dimensions, set(coverage["required"]))
        for dimension in dimensions:
            with self.subTest(dimension=dimension):
                entry = coverage["properties"][dimension]
                if "$ref" in entry:
                    entry = schema["$defs"][entry["$ref"].rsplit("/", 1)[-1]]
                self.assertEqual(
                    {"searched", "unsearched"}, set(entry["required"])
                )
                self.assertEqual("array", entry["properties"]["searched"]["type"])
                self.assertEqual("array", entry["properties"]["unsearched"]["type"])

    def test_state_schema_enforces_the_approval_gate(self):
        schema = self.load("project-state.schema.json")

        self.assertEqual(
            "null", self.approved_plan_type_for_status(schema, "planning")
        )
        for status in ("approved", "retrieving", "paused", "complete"):
            with self.subTest(status=status):
                self.assertEqual(
                    "object", self.approved_plan_type_for_status(schema, status)
                )

    def test_state_schema_contains_resumable_branches_and_deduplication(self):
        schema = self.load("project-state.schema.json")
        branch = schema["properties"]["branches"]["items"]
        deduplication = schema["properties"]["deduplication"]

        self.assertIn("deduplication", schema["required"])
        self.assertEqual(
            {
                "branch_id",
                "source_track",
                "retrieval_mode",
                "vertical_seed_id",
                "tracing_direction",
                "known_id_snapshot",
                "status",
                "assignment",
                "scope",
                "exclusions",
                "source_types",
                "period",
                "privacy_constraints",
                "last_checkpoint",
                "platform_errors",
                "unresolved_items",
                "current_depth",
                "max_authorized_depth",
                "queries",
                "platforms",
                "languages",
                "pending_items",
            },
            set(branch["required"]),
        )
        self.assertEqual(
            ["primary", "secondary", "mixed"],
            branch["properties"]["source_track"]["enum"],
        )
        self.assertEqual(
            ["horizontal", "vertical"],
            branch["properties"]["retrieval_mode"]["enum"],
        )
        self.assertEqual(
            ["string", "null"],
            branch["properties"]["vertical_seed_id"]["type"],
        )
        self.assertEqual(
            ["backward", "forward", "lateral", None],
            branch["properties"]["tracing_direction"]["enum"],
        )
        self.assertTrue(
            branch["properties"]["known_id_snapshot"]["uniqueItems"]
        )
        horizontal_rule = next(
            rule
            for rule in branch["allOf"]
            if rule["if"]["properties"]["retrieval_mode"].get("const")
            == "horizontal"
        )
        self.assertEqual(
            "null",
            horizontal_rule["then"]["properties"]["vertical_seed_id"]["type"],
        )
        self.assertEqual(
            "null",
            horizontal_rule["then"]["properties"]["tracing_direction"]["type"],
        )
        self.assertNotIn("kind", branch["properties"])
        self.assertEqual(
            {
                "identity_index",
                "unresolved_record_ids",
                "last_merged_at",
            },
            set(deduplication["required"]),
        )
        self.assertTrue(
            deduplication["properties"]["unresolved_record_ids"]["uniqueItems"]
        )

    def test_state_schema_records_round_evidence_and_a_nonempty_stop_reason(self):
        schema = self.load("project-state.schema.json")
        round_record = schema["properties"]["rounds"]["items"]

        self.assertEqual(
            {
                "round_id",
                "timestamp",
                "budget_status",
                "decision",
                "decision_reason",
                "unresolved_gaps",
                "branch_depth",
                "attempted_queries_or_paths",
                "access_failures",
                "counts",
                "coverage_additions",
                "access_gaps",
                "open_high_value_branches",
            },
            set(round_record["required"]),
        )
        self.assertEqual(
            ["continue", "pause_for_user", "stop"],
            round_record["properties"]["decision"]["enum"],
        )
        self.assertIn("budget_status", round_record["required"])
        self.assertEqual(
            ["within_budget", "budget_paused"],
            round_record["properties"]["budget_status"]["enum"],
        )
        self.assertEqual(
            1, round_record["properties"]["decision_reason"]["minLength"]
        )
        self.assertEqual(
            {
                "candidate_count",
                "new_candidate_count",
                "new_high_relevance_count",
                "new_core_material_count",
                "duplicate_count",
                "duplicate_ratio",
            },
            set(round_record["properties"]["counts"]["required"]),
        )
        self.assertNotIn("duplicate_ratio", round_record["properties"])
        ratio = round_record["properties"]["counts"]["properties"][
            "duplicate_ratio"
        ]
        self.assertEqual(0, ratio["minimum"])
        self.assertEqual(1, ratio["maximum"])
        self.assertEqual(
            1, schema["properties"]["stopping"]["properties"]["reason"]["minLength"]
        )


if __name__ == "__main__":
    unittest.main()
