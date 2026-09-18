from pathlib import Path
from copy import deepcopy
import importlib.util
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "corpus_ops.py"


def load_module():
    spec = importlib.util.spec_from_file_location("corpus_ops", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CorpusOpsTests(unittest.TestCase):
    def test_validate_retrieval_links_rejects_dangling_description_event(self):
        module = load_module()
        record = {
            "access_status": "Metadata only",
            "description_basis": "metadata",
            "description_retrieval_id": "missing-event",
            "retrieval_history": [
                {
                    "event_id": "retrieval-1",
                    "access_status": "Metadata only",
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "resolve"):
            module.validate_retrieval_links(record)

    def test_merge_rejects_retrieval_event_id_collision(self):
        module = load_module()
        left = {
            "id": "left",
            "external_ids": {"doi": "10.1000/lotus"},
            "access_status": "Metadata only",
            "description_basis": "metadata",
            "description_retrieval_id": "shared-event",
            "retrieval_history": [
                {
                    "event_id": "shared-event",
                    "platform": "Catalog A",
                    "access_status": "Metadata only",
                }
            ],
        }
        right = {
            "id": "right",
            "external_ids": {"doi": "10.1000/lotus"},
            "access_status": "Metadata only",
            "description_basis": "metadata",
            "description_retrieval_id": "shared-event",
            "retrieval_history": [
                {
                    "event_id": "shared-event",
                    "platform": "Catalog B",
                    "access_status": "Metadata only",
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "event_id collision"):
            module.merge_records(left, right)

    def test_validate_retrieval_links_rejects_duplicate_event_ids(self):
        module = load_module()
        record = {
            "access_status": "Metadata only",
            "description_basis": "metadata",
            "description_retrieval_id": "duplicate",
            "retrieval_history": [
                {"event_id": "duplicate", "access_status": "Metadata only"},
                {"event_id": "duplicate", "access_status": "Metadata only"},
            ],
        }
        with self.assertRaisesRegex(ValueError, "Duplicate retrieval event_id"):
            module.validate_retrieval_links(record)

    def test_validate_retrieval_links_enforces_access_and_basis(self):
        module = load_module()
        mismatched_access = {
            "access_status": "Metadata only",
            "description_basis": "metadata",
            "description_retrieval_id": "event-1",
            "retrieval_history": [
                {"event_id": "event-1", "access_status": "Abstract only"}
            ],
        }
        with self.assertRaisesRegex(ValueError, "canonical access_status"):
            module.validate_retrieval_links(mismatched_access)

        incompatible_basis = {
            "access_status": "Metadata only",
            "description_basis": "full_text",
            "description_retrieval_id": "event-1",
            "retrieval_history": [
                {"event_id": "event-1", "access_status": "Metadata only"}
            ],
        }
        with self.assertRaisesRegex(ValueError, "full_text descriptions"):
            module.validate_retrieval_links(incompatible_basis)

    def test_access_failed_requires_metadata_basis(self):
        module = load_module()
        metadata_record = {
            "access_status": "Access failed",
            "description_basis": "metadata",
            "description_retrieval_id": "failed-event",
            "retrieval_history": [
                {"event_id": "failed-event", "access_status": "Access failed"}
            ],
        }
        module.validate_retrieval_links(metadata_record)

        abstract_record = deepcopy(metadata_record)
        abstract_record["description_basis"] = "abstract"
        with self.assertRaisesRegex(ValueError, "metadata basis"):
            module.validate_retrieval_links(abstract_record)

    def test_full_text_not_read_allows_abstract_basis(self):
        module = load_module()
        record = {
            "access_status": "Full text not read",
            "description_basis": "abstract",
            "description_retrieval_id": "abstract-event",
            "retrieval_history": [
                {
                    "event_id": "abstract-event",
                    "access_status": "Full text not read",
                }
            ],
        }
        module.validate_retrieval_links(record)

    def test_merge_prefers_full_text_not_read_over_abstract_only(self):
        module = load_module()
        left = {
            "id": "left",
            "external_ids": {"doi": "10.1000/lotus"},
            "access_status": "Abstract only",
            "description": "Database abstract",
            "description_basis": "abstract",
            "description_retrieval_id": "abstract-only-event",
            "retrieval_history": [
                {
                    "event_id": "abstract-only-event",
                    "access_status": "Abstract only",
                }
            ],
        }
        right = {
            "id": "right",
            "external_ids": {"doi": "10.1000/lotus"},
            "access_status": "Full text not read",
            "description": "Publisher abstract",
            "description_basis": "abstract",
            "description_retrieval_id": "full-text-gap-event",
            "retrieval_history": [
                {
                    "event_id": "full-text-gap-event",
                    "access_status": "Full text not read",
                }
            ],
        }

        merged = module.merge_records(left, right)

        self.assertEqual("Full text not read", merged["access_status"])
        self.assertEqual("Publisher abstract", merged["description"])
        self.assertEqual("abstract", merged["description_basis"])
        self.assertEqual("full-text-gap-event", merged["description_retrieval_id"])
        self.assertEqual(2, len(merged["retrieval_history"]))
        module.validate_retrieval_links(merged)

    def test_valid_retrieval_link_merge_deduplicates_identical_event(self):
        module = load_module()
        event = {
            "event_id": "shared-event",
            "platform": "Catalog",
            "access_status": "Metadata only",
        }
        left = {
            "id": "left",
            "external_ids": {"doi": "10.1000/lotus"},
            "access_status": "Metadata only",
            "description_basis": "metadata",
            "description_retrieval_id": "shared-event",
            "retrieval_history": [deepcopy(event)],
        }
        right = {
            "id": "right",
            "external_ids": {"doi": "10.1000/lotus"},
            "access_status": "Metadata only",
            "description_basis": "metadata",
            "description_retrieval_id": "shared-event",
            "retrieval_history": [deepcopy(event)],
        }

        merged = module.merge_records(left, right)

        self.assertEqual([event], merged["retrieval_history"])
        module.validate_retrieval_links(merged)

    def test_normalize_text_preserves_unicode_alphanumerics(self):
        module = load_module()
        self.assertEqual("中国 国际法 2026", module.normalize_text(" 中国—国际法 ２０２６ "))
        self.assertEqual(
            "международное право",
            module.normalize_text("МЕЖДУНАРОДНОЕ-ПРАВО"),
        )

    def test_doi_wins_as_identity_key(self):
        module = load_module()
        record = {
            "external_ids": {"DOI": "https://doi.org/10.1000/ABC"},
            "title": "Other",
        }
        self.assertEqual("doi:10.1000/abc", module.identity_key(record))

    def test_empty_normalized_doi_is_not_an_identity_key(self):
        module = load_module()
        record = {"external_ids": {"doi": "DOI:   "}}
        self.assertIsNone(module.identity_key(record))

    def test_metadata_fallback_is_normalized(self):
        module = load_module()
        record = {
            "external_ids": {},
            "title": "  The   Lotus Case ",
            "date": "1927",
            "creators": ["P.C.I.J."],
        }
        self.assertEqual(
            "meta:the lotus case|1927|p c i j",
            module.identity_key(record),
        )

    def test_formal_identifier_precedes_metadata(self):
        module = load_module()
        record = {
            "external_ids": {"case_number": "  ICC-01/04-01/06  "},
            "title": "Alternate title",
            "date": "2006",
            "creators": ["ICC"],
        }
        self.assertEqual(
            "case_number:icc:icc 01 04 01 06",
            module.identity_key(record),
        )

    def test_formal_identifier_requires_issuer_namespace(self):
        module = load_module()
        record = {
            "external_ids": {"document_number": "A/RES/77/1"},
            "title": "Resolution",
            "date": "2022",
            "creators": [],
            "publication": None,
        }
        self.assertIsNone(module.identity_key(record))

    def test_insufficient_metadata_has_no_identity_key(self):
        module = load_module()
        self.assertIsNone(module.identity_key({"external_ids": {}}))
        self.assertIsNone(
            module.identity_key(
                {
                    "external_ids": {},
                    "title": "A common title",
                    "date": "2024",
                    "creators": [],
                }
            )
        )

    def test_merge_preserves_stronger_access_and_provenance(self):
        module = load_module()
        left = {
            "id": "left",
            "external_ids": {"doi": "10.1000/lotus"},
            "access_status": "Metadata only",
            "description": "Metadata description",
            "description_basis": "metadata",
            "discovery_history": [{"method": "query", "value": "lotus"}],
        }
        right = {
            "id": "right",
            "external_ids": {"doi": "10.1000/lotus"},
            "access_status": "Full text read",
            "description": "Full-text description",
            "description_basis": "full_text",
            "discovery_history": [
                {"method": "footnote", "value": "note 4"}
            ],
        }
        merged = module.merge_records(left, right)
        self.assertEqual("Full text read", merged["access_status"])
        self.assertEqual("Full-text description", merged["description"])
        self.assertEqual("full_text", merged["description_basis"])
        self.assertEqual(2, len(merged["discovery_history"]))

    def test_merge_preserves_conflicts_for_human_review(self):
        module = load_module()
        left = {
            "id": "left",
            "external_ids": {"doi": "10.1000/lotus"},
            "title": "Lotus",
            "verification": {
                "identity": "verified",
                "metadata_cross_checked": True,
                "human_review_required": False,
            },
        }
        right = {
            "id": "right",
            "external_ids": {"doi": "10.1000/lotus"},
            "title": "The Case of the S.S. Lotus",
        }

        merged = module.merge_records(left, right)

        self.assertEqual("Lotus", merged["title"])
        self.assertEqual(
            [
                {"value": "Lotus", "source_record_id": "left"},
                {
                    "value": "The Case of the S.S. Lotus",
                    "source_record_id": "right",
                },
            ],
            merged["merge_conflicts"]["title"],
        )
        self.assertEqual("conflict", merged["verification"]["identity"])
        self.assertTrue(merged["verification"]["human_review_required"])

    def test_merge_rejects_absent_or_mismatched_identity(self):
        module = load_module()
        with self.assertRaisesRegex(ValueError, "identity key"):
            module.merge_records({"id": "left"}, {"id": "right"})
        with self.assertRaisesRegex(ValueError, "do not match"):
            module.merge_records(
                {
                    "id": "left",
                    "external_ids": {"doi": "10.1000/left"},
                },
                {
                    "id": "right",
                    "external_ids": {"doi": "10.1000/right"},
                },
            )

    def test_merge_applies_field_specific_provenance_rules(self):
        module = load_module()
        left = {
            "id": "canonical",
            "aliases": ["earlier-alias"],
            "external_ids": {"doi": "10.1000/lotus"},
            "fields": ["general international law"],
            "subquestions": ["jurisdiction"],
            "discovery_history": [{"method": "query", "value": "lotus"}],
            "retrieval_history": [
                {
                    "event_id": "retrieval-1",
                    "platform": "Catalog",
                    "retrieved_at": "2026-01-01T00:00:00Z",
                    "access_status": "Metadata only",
                    "stable_url": "https://example.test/catalog",
                    "local_path": None,
                }
            ],
            "access_status": "Metadata only",
            "description": "Metadata description",
            "description_basis": "metadata",
            "description_retrieval_id": "retrieval-1",
            "stable_url": "https://example.test/canonical",
            "local_path": "/local/canonical.pdf",
        }
        right = {
            "id": "candidate",
            "external_ids": {
                "doi": "10.1000/lotus",
                "document_number": "Series A No. 10",
            },
            "fields": ["general international law", "state responsibility"],
            "subquestions": ["remedies"],
            "discovery_history": [{"method": "footnote", "value": "note 4"}],
            "retrieval_history": [
                {
                    "event_id": "retrieval-2",
                    "platform": "Repository",
                    "retrieved_at": "2026-01-02T00:00:00Z",
                    "access_status": "Full text read",
                    "stable_url": "https://example.test/full-text",
                    "local_path": "/local/candidate.pdf",
                }
            ],
            "access_status": "Full text read",
            "description": "Full-text description",
            "description_basis": "full_text",
            "description_retrieval_id": "retrieval-2",
            "stable_url": "https://example.test/full-text",
            "local_path": "/local/candidate.pdf",
        }
        original_left = deepcopy(left)
        original_right = deepcopy(right)

        merged = module.merge_records(left, right)

        self.assertEqual("canonical", merged["id"])
        self.assertEqual(["earlier-alias", "candidate"], merged["aliases"])
        self.assertEqual(
            ["general international law", "state responsibility"],
            merged["fields"],
        )
        self.assertEqual(["jurisdiction", "remedies"], merged["subquestions"])
        self.assertEqual(2, len(merged["discovery_history"]))
        self.assertEqual(2, len(merged["retrieval_history"]))
        self.assertEqual("Series A No. 10", merged["external_ids"]["document_number"])
        self.assertEqual("Full text read", merged["access_status"])
        self.assertEqual("Full-text description", merged["description"])
        self.assertEqual("full_text", merged["description_basis"])
        self.assertEqual("retrieval-2", merged["description_retrieval_id"])
        self.assertEqual("https://example.test/canonical", merged["stable_url"])
        self.assertEqual("/local/canonical.pdf", merged["local_path"])
        self.assertEqual(original_left, left)
        self.assertEqual(original_right, right)

    def test_blank_description_does_not_replace_existing_description_binding(self):
        module = load_module()
        left = {
            "id": "left",
            "external_ids": {"doi": "10.1000/lotus"},
            "access_status": "Abstract only",
            "description": "Abstract description",
            "description_basis": "abstract",
            "description_retrieval_id": "abstract-event",
            "retrieval_history": [
                {
                    "event_id": "abstract-event",
                    "access_status": "Abstract only",
                }
            ],
        }
        for blank_description in ("", " \t\n"):
            with self.subTest(description=repr(blank_description)):
                right = {
                    "id": "right",
                    "external_ids": {"doi": "10.1000/lotus"},
                    "access_status": "Full text read",
                    "description": blank_description,
                    "description_basis": "full_text",
                    "description_retrieval_id": "full-text-event",
                    "retrieval_history": [
                        {
                            "event_id": "full-text-event",
                            "access_status": "Full text read",
                        }
                    ],
                }

                merged = module.merge_records(left, right)

                self.assertEqual("Full text read", merged["access_status"])
                self.assertEqual("Abstract description", merged["description"])
                self.assertEqual("abstract", merged["description_basis"])
                self.assertEqual(
                    "abstract-event", merged["description_retrieval_id"]
                )

    def test_external_id_conflict_is_provenanced_identity_conflict(self):
        module = load_module()
        left = {
            "id": "left",
            "external_ids": {
                "doi": "10.1000/lotus",
                "case_number": "A-1",
            },
            "verification": {
                "identity": "verified",
                "metadata_cross_checked": True,
                "human_review_required": False,
            },
        }
        right = {
            "id": "right",
            "external_ids": {
                "doi": "10.1000/lotus",
                "case_number": "A-2",
            },
        }

        merged = module.merge_records(left, right)

        self.assertEqual(
            [
                {"value": "A-1", "source_record_id": "left"},
                {"value": "A-2", "source_record_id": "right"},
            ],
            merged["merge_conflicts"]["external_ids.case_number"],
        )
        self.assertEqual("conflict", merged["verification"]["identity"])

    def test_non_identity_conflict_does_not_change_identity_status(self):
        module = load_module()
        left = {
            "id": "left",
            "external_ids": {"doi": "10.1000/lotus"},
            "source_type": "journal_article",
            "verification": {
                "identity": "verified",
                "metadata_cross_checked": True,
                "human_review_required": False,
            },
        }
        right = {
            "id": "right",
            "external_ids": {"doi": "10.1000/lotus"},
            "source_type": "book_chapter",
        }

        merged = module.merge_records(left, right)

        self.assertEqual("verified", merged["verification"]["identity"])
        self.assertTrue(merged["verification"]["human_review_required"])
        self.assertIn("source_type", merged["merge_conflicts"])

    def test_preexisting_conflicts_merge_without_nesting(self):
        module = load_module()
        left = {
            "id": "left",
            "external_ids": {"doi": "10.1000/lotus"},
            "publication": "Reporter A",
            "merge_conflicts": {
                "publication": [
                    {"value": "Reporter A", "source_record_id": "left"},
                    {"value": "Reporter B", "source_record_id": "older"},
                ]
            },
        }
        right = {
            "id": "right",
            "external_ids": {"doi": "10.1000/lotus"},
            "publication": "Reporter A",
            "merge_conflicts": {
                "publication": [
                    {"value": "Reporter B", "source_record_id": "older"},
                    {"value": "Reporter C", "source_record_id": "right"},
                ]
            },
        }

        merged = module.merge_records(left, right)

        self.assertEqual(
            [
                {"value": "Reporter A", "source_record_id": "left"},
                {"value": "Reporter B", "source_record_id": "older"},
                {"value": "Reporter C", "source_record_id": "right"},
            ],
            merged["merge_conflicts"]["publication"],
        )
        self.assertNotIn("merge_conflicts", merged["merge_conflicts"])


if __name__ == "__main__":
    unittest.main()
