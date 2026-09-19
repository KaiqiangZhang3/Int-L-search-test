import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLAIM_SCHEMA = ROOT / "schemas" / "claim-record.schema.json"
KNOWLEDGE_REFERENCE = ROOT / "references" / "knowledge-and-synthesis.md"
sys.path.insert(0, str(ROOT / "scripts"))

from validate_claim_ledger import (
    current_claim_ids,
    validate_claim_ledger,
    validate_records,
)


def write_jsonl(path, records):
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def source_record(source_key, review_extent):
    return {
        "source_key": source_key,
        "review_extent": review_extent,
    }


def evidence(source_key="SRC-1", locator="p. 12"):
    return {
        "source_key": source_key,
        "locator": locator,
        "evidence_function": "direct_support",
        "review_basis": "selected_sections_reviewed",
    }


def claim_record(
    claim_id,
    *,
    status="provisional",
    supporting_evidence=None,
    contrary_evidence=None,
    predecessors=None,
    successors=None,
):
    return {
        "claim_id": claim_id,
        "claim_text": f"Claim text for {claim_id}.",
        "claim_type": "doctrinal",
        "scope": "The defined research question.",
        "status": status,
        "first_seen_round": "R1",
        "last_verified_round": "R1" if status != "provisional" else None,
        "supporting_evidence": supporting_evidence or [],
        "contrary_evidence": contrary_evidence or [],
        "predecessor_claim_ids": predecessors or [],
        "successor_claim_ids": successors or [],
        "reader_qualification": "Limited to the sources reviewed so far.",
    }


class ClaimLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_claim_schema_exposes_stable_evidence_and_revision_contract(self):
        schema = json.loads(CLAIM_SCHEMA.read_text(encoding="utf-8"))

        self.assertTrue(
            {
                "claim_id",
                "claim_text",
                "claim_type",
                "scope",
                "status",
                "first_seen_round",
                "last_verified_round",
                "supporting_evidence",
                "contrary_evidence",
                "predecessor_claim_ids",
                "successor_claim_ids",
                "reader_qualification",
            }.issubset(schema["required"])
        )
        self.assertEqual(
            [
                "provisional",
                "supported",
                "contested",
                "revised",
                "superseded",
            ],
            schema["properties"]["status"]["enum"],
        )
        self.assertTrue(
            {
                "source_key",
                "locator",
                "evidence_function",
                "review_basis",
            }.issubset(schema["$defs"]["evidence"]["required"])
        )

    def test_reference_explains_claim_lifecycle_and_synthesis_boundary(self):
        text = KNOWLEDGE_REFERENCE.read_text(encoding="utf-8").lower()

        for phrase in (
            "source ledger",
            "claim ledger",
            "review basis",
            "reciprocal",
            "current conclusions",
            "historical label",
            "living synthesis",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_supported_claim_requires_reviewed_evidence_and_locator(self):
        write_jsonl(
            self.tmp_path / "sources.jsonl",
            [source_record("SRC-1", review_extent="metadata_verified")],
        )
        write_jsonl(
            self.tmp_path / "claims.jsonl",
            [
                claim_record(
                    "CLM-1",
                    status="supported",
                    supporting_evidence=[evidence(locator=None)],
                )
            ],
        )

        errors = validate_claim_ledger(
            self.tmp_path / "claims.jsonl",
            self.tmp_path / "sources.jsonl",
        )

        self.assertTrue(any("reviewed evidence" in error for error in errors))
        self.assertTrue(any("locator" in error for error in errors))

    def test_supported_claim_requires_supporting_evidence(self):
        write_jsonl(
            self.tmp_path / "sources.jsonl",
            [
                source_record(
                    "SRC-1", review_extent="selected_sections_reviewed"
                )
            ],
        )
        write_jsonl(
            self.tmp_path / "claims.jsonl",
            [claim_record("CLM-1", status="supported")],
        )

        errors = validate_claim_ledger(
            self.tmp_path / "claims.jsonl",
            self.tmp_path / "sources.jsonl",
        )

        self.assertTrue(
            any("requires supporting evidence" in error for error in errors)
        )

    def test_supported_claim_requires_a_verification_round(self):
        claim = claim_record(
            "CLM-1",
            status="supported",
            supporting_evidence=[evidence()],
        )
        claim["last_verified_round"] = None

        errors = validate_records(
            [claim],
            [
                source_record(
                    "SRC-1", review_extent="selected_sections_reviewed"
                )
            ],
        )

        self.assertTrue(
            any("last_verified_round" in error for error in errors)
        )

    def test_last_verified_round_must_be_string_or_null(self):
        claim = claim_record("CLM-1")
        claim["last_verified_round"] = 2

        errors = validate_records([claim], [])

        self.assertTrue(
            any("last_verified_round must be a string or null" in error for error in errors)
        )

    def test_first_seen_round_must_be_a_nonempty_string(self):
        claim = claim_record("CLM-1")
        claim["first_seen_round"] = ""

        errors = validate_records([claim], [])

        self.assertTrue(
            any("first_seen_round must be a non-empty string" in error for error in errors)
        )

    def test_evidence_source_must_resolve(self):
        write_jsonl(self.tmp_path / "sources.jsonl", [])
        write_jsonl(
            self.tmp_path / "claims.jsonl",
            [
                claim_record(
                    "CLM-1",
                    status="supported",
                    supporting_evidence=[evidence("SRC-MISSING")],
                )
            ],
        )

        errors = validate_claim_ledger(
            self.tmp_path / "claims.jsonl",
            self.tmp_path / "sources.jsonl",
        )

        self.assertTrue(any("unknown source_key" in error for error in errors))

    def test_provisional_evidence_must_also_resolve(self):
        errors = validate_records(
            [
                claim_record(
                    "CLM-1",
                    supporting_evidence=[evidence("SRC-MISSING")],
                )
            ],
            [],
        )

        self.assertTrue(any("unknown source_key" in error for error in errors))

    def test_malformed_evidence_is_reported_without_crashing(self):
        claim = claim_record("CLM-1")
        claim["supporting_evidence"] = ["not-an-object"]

        errors = validate_records([claim], [])

        self.assertTrue(any("evidence must be an object" in error for error in errors))

    def test_evidence_collections_must_be_arrays(self):
        claim = claim_record("CLM-1")
        claim["supporting_evidence"] = None

        errors = validate_records([claim], [])

        self.assertTrue(
            any("supporting_evidence must be an array" in error for error in errors)
        )

    def test_contested_claim_requires_evidence_on_both_sides(self):
        write_jsonl(
            self.tmp_path / "sources.jsonl",
            [
                source_record(
                    "SRC-1", review_extent="selected_sections_reviewed"
                )
            ],
        )
        write_jsonl(
            self.tmp_path / "claims.jsonl",
            [
                claim_record(
                    "CLM-1",
                    status="contested",
                    supporting_evidence=[evidence()],
                )
            ],
        )

        errors = validate_claim_ledger(
            self.tmp_path / "claims.jsonl",
            self.tmp_path / "sources.jsonl",
        )

        self.assertTrue(
            any("requires contrary evidence" in error for error in errors)
        )

    def test_evidence_review_basis_cannot_overstate_source_review(self):
        write_jsonl(
            self.tmp_path / "sources.jsonl",
            [
                source_record(
                    "SRC-1", review_extent="selected_sections_reviewed"
                )
            ],
        )
        item = evidence()
        item["review_basis"] = "full_text_substantively_reviewed"
        write_jsonl(
            self.tmp_path / "claims.jsonl",
            [
                claim_record(
                    "CLM-1",
                    status="supported",
                    supporting_evidence=[item],
                )
            ],
        )

        errors = validate_claim_ledger(
            self.tmp_path / "claims.jsonl",
            self.tmp_path / "sources.jsonl",
        )

        self.assertTrue(any("review_basis" in error for error in errors))

    def test_evidence_requires_a_substantive_review_basis(self):
        item = evidence()
        item["review_basis"] = "metadata_verified"
        errors = validate_records(
            [claim_record("CLM-1", supporting_evidence=[item])],
            [
                source_record(
                    "SRC-1", review_extent="selected_sections_reviewed"
                )
            ],
        )

        self.assertTrue(any("invalid review_basis" in error for error in errors))

    def test_evidence_requires_a_known_function(self):
        item = evidence()
        item["evidence_function"] = "proves_everything"
        errors = validate_records(
            [claim_record("CLM-1", supporting_evidence=[item])],
            [
                source_record(
                    "SRC-1", review_extent="selected_sections_reviewed"
                )
            ],
        )

        self.assertTrue(
            any("invalid evidence_function" in error for error in errors)
        )

    def test_evidence_shape_rejects_missing_and_additional_fields(self):
        item = evidence()
        del item["source_key"]
        item["note"] = "Uncontrolled field"

        errors = validate_records(
            [claim_record("CLM-1", supporting_evidence=[item])], []
        )

        self.assertTrue(any("source_key is required" in error for error in errors))
        self.assertTrue(
            any("unsupported evidence fields: note" in error for error in errors)
        )

    def test_evidence_source_key_must_be_a_nonempty_string(self):
        item = evidence(source_key="")

        errors = validate_records(
            [claim_record("CLM-1", supporting_evidence=[item])], []
        )

        self.assertTrue(
            any("evidence source_key must be a non-empty string" in error for error in errors)
        )

    def test_claim_ids_must_be_unique(self):
        write_jsonl(self.tmp_path / "sources.jsonl", [])
        write_jsonl(
            self.tmp_path / "claims.jsonl",
            [claim_record("CLM-1"), claim_record("CLM-1")],
        )

        errors = validate_claim_ledger(
            self.tmp_path / "claims.jsonl",
            self.tmp_path / "sources.jsonl",
        )

        self.assertTrue(any("duplicate claim_id" in error for error in errors))

    def test_claim_id_must_be_nonempty(self):
        errors = validate_records([claim_record("")], [])

        self.assertTrue(
            any("claim_id must be a non-empty string" in error for error in errors)
        )

    def test_revised_claim_links_to_current_successor(self):
        claims = [
            claim_record("CLM-1", status="revised", successors=["CLM-2"]),
            claim_record(
                "CLM-2",
                status="supported",
                predecessors=["CLM-1"],
                supporting_evidence=[evidence()],
            ),
        ]
        sources = [
            source_record(
                "SRC-1", review_extent="selected_sections_reviewed"
            )
        ]

        self.assertEqual([], validate_records(claims, sources))
        self.assertEqual({"CLM-2"}, current_claim_ids(claims))

    def test_revision_links_must_be_reciprocal(self):
        claims = [
            claim_record("CLM-1", status="revised", successors=["CLM-2"]),
            claim_record("CLM-2"),
        ]

        errors = validate_records(claims, [])

        self.assertTrue(any("not reciprocal" in error for error in errors))

    def test_revision_lineage_must_not_contain_cycles(self):
        claims = [
            claim_record(
                "CLM-1",
                status="revised",
                predecessors=["CLM-2"],
                successors=["CLM-2"],
            ),
            claim_record(
                "CLM-2",
                status="revised",
                predecessors=["CLM-1"],
                successors=["CLM-1"],
            ),
        ]

        errors = validate_records(claims, [])

        self.assertTrue(any("revision cycle" in error for error in errors))

    def test_validator_rejects_missing_required_claim_fields(self):
        incomplete = claim_record("CLM-1")
        del incomplete["reader_qualification"]

        errors = validate_records([incomplete], [])

        self.assertTrue(
            any("reader_qualification is required" in error for error in errors)
        )

    def test_validator_rejects_unknown_claim_status(self):
        claim = claim_record("CLM-1")
        claim["status"] = "confirmed"

        errors = validate_records([claim], [])

        self.assertTrue(any("unsupported status" in error for error in errors))

    def test_reader_text_fields_must_be_nonempty_strings(self):
        for field in (
            "claim_text",
            "claim_type",
            "scope",
            "reader_qualification",
        ):
            with self.subTest(field=field):
                claim = claim_record("CLM-1")
                claim[field] = ""

                errors = validate_records([claim], [])

                self.assertTrue(
                    any(
                        f"{field} must be a non-empty string" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_claim_rejects_additional_top_level_fields(self):
        claim = claim_record("CLM-1")
        claim["private_note"] = "Not part of the claim contract."

        errors = validate_records([claim], [])

        self.assertTrue(
            any("unsupported claim fields: private_note" in error for error in errors),
            errors,
        )

    def test_revision_link_collections_must_be_arrays(self):
        for field in ("predecessor_claim_ids", "successor_claim_ids"):
            with self.subTest(field=field):
                claim = claim_record("CLM-1")
                claim[field] = None

                errors = validate_records([claim], [])

                self.assertTrue(
                    any(f"{field} must be an array" in error for error in errors),
                    errors,
                )

    def test_revision_link_ids_must_be_unique(self):
        claim = claim_record(
            "CLM-1",
            status="revised",
            successors=["CLM-2", "CLM-2"],
        )

        errors = validate_records([claim], [])

        self.assertTrue(
            any("successor_claim_ids must contain unique IDs" in error for error in errors),
            errors,
        )

    def test_historical_claim_requires_a_successor(self):
        errors = validate_records(
            [claim_record("CLM-1", status="superseded")], []
        )

        self.assertTrue(any("requires a successor" in error for error in errors))

    def test_cli_reports_a_valid_claim_ledger(self):
        write_jsonl(
            self.tmp_path / "sources.jsonl",
            [
                source_record(
                    "SRC-1", review_extent="selected_sections_reviewed"
                )
            ],
        )
        write_jsonl(
            self.tmp_path / "claims.jsonl",
            [
                claim_record(
                    "CLM-1",
                    status="supported",
                    supporting_evidence=[evidence()],
                )
            ],
        )

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_claim_ledger.py"),
                "--claims",
                str(self.tmp_path / "claims.jsonl"),
                "--sources",
                str(self.tmp_path / "sources.jsonl"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Claim ledger is valid", result.stdout)


if __name__ == "__main__":
    unittest.main()
