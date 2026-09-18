import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LEDGER_REFERENCE = ROOT / "references/source-ledger.md"


def load_schema(name):
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


class SourceLedgerContractTests(unittest.TestCase):
    def test_lightweight_ledger_requires_upgrade_safe_fields(self):
        schema = load_schema("source-ledger-record.schema.json")

        self.assertTrue(
            {
                "source_key",
                "identity_evidence",
                "discovery_provenance",
                "availability",
                "review_extent",
                "description_basis",
                "description",
                "inclusion_reason",
                "user_decisions",
            }.issubset(schema["required"])
        )

    def test_quick_record_does_not_require_graph_or_audit_events(self):
        schema = load_schema("source-ledger-record.schema.json")

        self.assertNotIn("retrieval_history", schema["required"])
        self.assertNotIn("audit_events", schema["required"])
        self.assertNotIn("edges", schema["properties"])

    def test_ledger_exposes_two_access_axes_and_upgrade_fields(self):
        schema = load_schema("source-ledger-record.schema.json")

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
        for field in (
            "identifiers",
            "links",
            "local_paths",
            "source_type",
            "language",
            "ranking_factors",
            "reading_priority",
            "version_relationships",
            "retrieval_history",
        ):
            with self.subTest(field=field):
                self.assertIn(field, schema["properties"])

    def test_reference_maps_reader_labels_and_protects_upgrade_history(self):
        text = LEDGER_REFERENCE.read_text(encoding="utf-8")
        lower = text.lower()

        for enum_value in (
            "open_full_text",
            "subscription_full_text",
            "full_text_substantively_reviewed",
            "selected_sections_reviewed",
            "priority_reading",
        ):
            with self.subTest(enum_value=enum_value):
                self.assertIn(enum_value, text)
        self.assertIn("reader-facing labels", lower)
        self.assertIn("must not discard provenance", lower)
        self.assertIn("must not silently change identity", lower)
        self.assertIn("must not overstate prior review", lower)

    def test_reviewed_sections_require_description_locations(self):
        schema = load_schema("source-ledger-record.schema.json")
        locations = schema["properties"]["description_basis"]["properties"][
            "locations"
        ]

        self.assertEqual(1, locations["minItems"])


if __name__ == "__main__":
    unittest.main()
