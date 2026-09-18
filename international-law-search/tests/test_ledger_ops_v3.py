from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ledger_ops.py"
VALIDATOR_SCRIPT = ROOT / "scripts" / "validate_source_ledger.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ledger_ops", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_source_ledger", VALIDATOR_SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def provenance(method="query", value="Initial query"):
    return {"method": method, "value": value}


def source_record(source_key, title, creator="Author A", doi=None):
    record = {
        "source_key": source_key,
        "identity_evidence": {
            "normalized_title": title,
            "creators": [creator],
            "publication_date": "2025",
            "publication": "Example Journal",
            "identity_status": "verified",
            "evidence": [{"kind": "publisher_record", "value": "Catalog"}],
        },
        "source_type": "journal_article",
        "discovery_provenance": [provenance()],
        "availability": "metadata_only",
        "review_extent": "metadata_verified",
        "description_basis": {"kind": "metadata", "locations": ["Catalog"]},
        "description": "The catalog identifies this source.",
        "inclusion_reason": "It is relevant to the approved question.",
        "user_decisions": [],
    }
    if doi:
        record["identifiers"] = {"doi": doi}
    return record


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class LedgerOpsV3Tests(unittest.TestCase):
    def setUp(self):
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._temporary_directory.name)

    def tearDown(self):
        self._temporary_directory.cleanup()

    def test_upsert_merges_equivalent_doi_records_and_preserves_provenance(self):
        module = load_module()
        ledger = self.tmp_path / "sources.jsonl"
        first = source_record("SRC-001", title="Example Title", doi="10.1000/ABC")
        second = source_record(
            "TEMP-9",
            title="EXAMPLE TITLE",
            doi="https://doi.org/10.1000/abc",
        )
        second["discovery_provenance"] = [
            provenance("reference", "Seed A, note 14")
        ]

        module.upsert_source(ledger, first)
        result = module.upsert_source(ledger, second)

        rows = read_jsonl(ledger)
        self.assertEqual({"action": "merged", "source_key": "SRC-001"}, result)
        self.assertEqual(1, len(rows))
        self.assertEqual(2, len(rows[0]["discovery_provenance"]))

    def test_repeated_upsert_is_idempotent(self):
        module = load_module()
        ledger = self.tmp_path / "sources.jsonl"
        record = source_record("SRC-001", title="Example", doi="10.1000/example")

        module.upsert_source(ledger, record)
        result = module.upsert_source(ledger, record)

        self.assertEqual({"action": "unchanged", "source_key": "SRC-001"}, result)
        self.assertEqual([record], read_jsonl(ledger))

    def test_ambiguous_metadata_does_not_silently_merge(self):
        module = load_module()
        ledger = self.tmp_path / "sources.jsonl"
        module.upsert_source(
            ledger,
            source_record("SRC-001", title="Common Title", creator="Author A"),
        )

        result = module.upsert_source(
            ledger,
            source_record("SRC-002", title="Common Title", creator="Author B"),
        )

        self.assertEqual("inserted", result["action"])
        self.assertEqual(2, len(read_jsonl(ledger)))

    def test_conflicting_strong_identifiers_override_matching_metadata(self):
        module = load_module()
        ledger = self.tmp_path / "sources.jsonl"
        first = source_record("SRC-001", title="Same Title", doi="10.1000/first")
        second = source_record("SRC-002", title="Same Title", doi="10.1000/second")

        module.upsert_source(ledger, first)
        result = module.upsert_source(ledger, second)

        self.assertEqual("inserted", result["action"])
        self.assertEqual(2, len(read_jsonl(ledger)))

    def test_merge_preserves_new_identifiers_and_attributed_metadata_conflicts(self):
        module = load_module()
        ledger = self.tmp_path / "sources.jsonl"
        first = source_record("SRC-001", title="Example", doi="10.1000/example")
        first["identity_evidence"]["publication"] = "Journal A"
        second = source_record("TEMP-2", title="Example", doi="10.1000/example")
        second["identity_evidence"]["publication"] = "Journal B"
        second["identifiers"]["oclc"] = "12345"

        module.upsert_source(ledger, first)
        module.upsert_source(ledger, second)

        merged = read_jsonl(ledger)[0]
        self.assertEqual("12345", merged["identifiers"]["oclc"])
        conflicts = merged["metadata_conflicts"]["identity_evidence.publication"]
        self.assertEqual(
            {"Journal A", "Journal B"},
            {candidate["value"] for candidate in conflicts},
        )
        self.assertEqual(
            {"SRC-001", "TEMP-2"},
            {candidate["source_key"] for candidate in conflicts},
        )
        self.assertEqual([], load_validator().validate_source_ledger(ledger))

    def test_isbn_identity_is_edition_aware_and_merges_round_functions(self):
        module = load_module()
        ledger = self.tmp_path / "sources.jsonl"
        first = source_record("SRC-001", title="Treatise")
        first["identifiers"] = {"isbn_10": "0-306-40615-2"}
        first["source_details"] = {"publisher": "Example", "edition": "2nd"}
        first["round_membership"] = [
            {"round_id": "R-1", "functions": ["discovered"]}
        ]
        second = source_record("TEMP-2", title="Treatise")
        second["identifiers"] = {"isbn_13": "978-0-306-40615-7"}
        second["source_details"] = {"publisher": "Example", "edition": "2nd"}
        second["round_membership"] = [
            {"round_id": "R-1", "functions": ["reviewed"]}
        ]

        module.upsert_source(ledger, first)
        result = module.upsert_source(ledger, second)

        self.assertEqual("merged", result["action"])
        membership = read_jsonl(ledger)[0]["round_membership"]
        self.assertEqual(
            [{"round_id": "R-1", "functions": ["discovered", "reviewed"]}],
            membership,
        )

    def test_validator_rejects_duplicate_strong_identity(self):
        validator = load_validator()
        ledger = self.tmp_path / "sources.jsonl"
        records = [
            source_record("SRC-001", title="First", doi="10.1000/duplicate"),
            source_record(
                "SRC-002",
                title="Second",
                doi="https://doi.org/10.1000/DUPLICATE",
            ),
        ]
        ledger.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )

        errors = validator.validate_source_ledger(ledger)

        self.assertTrue(
            any("duplicate strong identity" in error.lower() for error in errors)
        )

    def test_validator_rejects_description_beyond_review_evidence(self):
        validator = load_validator()
        ledger = self.tmp_path / "sources.jsonl"
        record = source_record("SRC-001", title="Example")
        record["description_basis"] = {
            "kind": "full_text",
            "locations": ["pages 1-10"],
        }
        ledger.write_text(json.dumps(record) + "\n", encoding="utf-8")

        errors = validator.validate_source_ledger(ledger)

        self.assertTrue(any("unsupported description evidence" in error for error in errors))

    def test_validator_rejects_externalizable_local_acquisition_path(self):
        validator = load_validator()
        ledger = self.tmp_path / "sources.jsonl"
        record = source_record("SRC-001", title="Example")
        record["acquisition_routes"] = [
            {
                "route_type": "physical_copy",
                "status": "acquired",
                "local_path": "/Users/researcher/private/book.pdf",
                "externalizable": True,
            }
        ]
        ledger.write_text(json.dumps(record) + "\n", encoding="utf-8")

        errors = validator.validate_source_ledger(ledger)

        self.assertTrue(any("externalizable local paths" in error for error in errors))

    def test_schema_exposes_v3_priority_route_and_round_fields(self):
        schema = json.loads(
            (ROOT / "schemas" / "source-ledger-record.schema.json").read_text(
                encoding="utf-8"
            )
        )

        for field in (
            "scholarly_importance",
            "acquisition_priority",
            "acquisition_routes",
            "round_membership",
        ):
            with self.subTest(field=field):
                self.assertIn(field, schema["properties"])
        identifiers = schema["properties"]["identifiers"]["properties"]
        for identifier in ("isbn", "isbn_10", "isbn_13", "oclc", "lccn"):
            with self.subTest(identifier=identifier):
                self.assertIn(identifier, identifiers)

    def test_validator_cli_distinguishes_invalid_and_unreadable_input(self):
        validator = load_validator()
        invalid = self.tmp_path / "invalid.jsonl"
        invalid.write_text("{}\n", encoding="utf-8")
        missing = self.tmp_path / "missing.jsonl"

        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            invalid_exit = validator.main([str(invalid)])
            missing_exit = validator.main([str(missing)])

        self.assertEqual(1, invalid_exit)
        self.assertEqual(2, missing_exit)


if __name__ == "__main__":
    unittest.main()
