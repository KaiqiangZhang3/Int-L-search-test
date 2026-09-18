from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SchemaTests(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))

    def allowed_accesses_for_description_basis(self, schema, basis):
        all_accesses = set(schema["properties"]["access_status"]["enum"])
        for rule in schema.get("allOf", []):
            basis_rule = rule.get("if", {}).get("properties", {}).get(
                "description_basis", {}
            )
            if basis_rule.get("const") == basis:
                return set(
                    rule["then"]["properties"]["access_status"].get(
                        "enum",
                        [rule["then"]["properties"]["access_status"].get("const")],
                    )
                )
        return all_accesses

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
                "access_status",
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
                "Full text read",
                "Abstract only",
                "Metadata only",
                "Full text not read",
                "Access failed",
            ],
            schema["properties"]["access_status"]["enum"],
        )
        self.assertEqual(
            ["full_text", "abstract", "metadata"],
            schema["properties"]["description_basis"]["enum"],
        )
        self.assertEqual(
            "object", schema["properties"]["merge_conflicts"]["type"]
        )

    def test_candidate_source_schema_accepts_unresolved_submissions(self):
        schema = self.load("candidate-source-record.schema.json")
        required = set(schema["required"])

        self.assertEqual(
            {
                "candidate_id",
                "discovery_history",
                "access_status",
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

    def test_candidate_description_basis_preserves_limited_access_leads(self):
        schema = self.load("candidate-source-record.schema.json")

        self.assertEqual(
            {"Full text read"},
            self.allowed_accesses_for_description_basis(schema, "full_text"),
        )
        self.assertEqual(
            {"Abstract only", "Full text not read", "Full text read"},
            self.allowed_accesses_for_description_basis(schema, "abstract"),
        )
        self.assertIn(
            "Access failed",
            self.allowed_accesses_for_description_basis(schema, "metadata"),
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
                "access_status",
                "stable_url",
                "local_path",
            }.issubset(event["required"])
        )
        self.assertEqual(
            schema["properties"]["access_status"]["enum"],
            event["properties"]["access_status"]["enum"],
        )

    def test_description_basis_is_compatible_with_canonical_access(self):
        schema = self.load("source-record.schema.json")

        self.assertEqual(
            {"Full text read"},
            self.allowed_accesses_for_description_basis(schema, "full_text"),
        )
        self.assertEqual(
            {"Abstract only", "Full text not read", "Full text read"},
            self.allowed_accesses_for_description_basis(schema, "abstract"),
        )
        self.assertEqual(
            set(schema["properties"]["access_status"]["enum"]),
            self.allowed_accesses_for_description_basis(schema, "metadata"),
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

    def test_edge_schema_requires_evidence_only_for_verified_edges(self):
        schema = self.load("edge-record.schema.json")

        self.assertEqual(
            ["verified", "candidate"], schema["properties"]["status"]["enum"]
        )
        self.assertNotIn("evidence", schema["required"])
        verified_rule = next(
            rule
            for rule in schema["allOf"]
            if rule["if"]["properties"]["status"].get("const") == "verified"
        )
        candidate_rule = next(
            rule
            for rule in schema["allOf"]
            if rule["if"]["properties"]["status"].get("const") == "candidate"
        )
        self.assertIn("evidence", verified_rule["then"]["required"])
        self.assertNotIn("required", candidate_rule["then"])

    def test_state_schema_tracks_approval_rounds_branches_and_stopping(self):
        schema = self.load("project-state.schema.json")
        required = set(schema["required"])

        self.assertTrue(
            {"approved_plan", "branches", "rounds", "stopping"}.issubset(required)
        )
        self.assertEqual(
            ["continue", "pause_for_user", "stop"],
            schema["properties"]["stopping"]["properties"]["decision"]["enum"],
        )
        self.assertIn(
            "open_high_value_branches",
            schema["properties"]["stopping"]["required"],
        )

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
