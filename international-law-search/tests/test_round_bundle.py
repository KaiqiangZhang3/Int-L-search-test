from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_round_bundle import validate_bundle
from validate_reader_report import main as validate_reader_report_main


def valid_bundle():
    return {
        "checkpoint_id": "CP-R1",
        "round_id": "R1",
        "generated_at": "2026-09-18T12:00:00Z",
        "reader_language": "en",
        "research_question": "What role do corporations play in public international law?",
        "narrative_sections": [
            {
                "section_id": "findings",
                "title": "Findings",
                "body": "The literature identifies several roles.",
                "source_keys": ["SRC-1"],
                "claim_ids": ["CLM-1"],
            }
        ],
        "featured_source_keys": ["SRC-1"],
        "claim_ids": ["CLM-1"],
        "budget_summary": {
            "bibliographic_discovery": 1,
            "full_text_acquisition": 1,
            "substantive_review": 1,
        },
        "gaps": ["Regional practice remains underrepresented."],
        "next_round_options": [],
        "bibliography_selection": ["SRC-1"],
        "privacy_classification": "public_research_output",
        "externalizable": True,
    }


def reviewed_source(source_key):
    return {
        "source_key": source_key,
        "review_extent": "selected_sections_reviewed",
    }


def supported_claim(claim_id):
    return {
        "claim_id": claim_id,
        "status": "supported",
        "supporting_evidence": [
            {
                "source_key": "SRC-1",
                "locator": "pp. 10-12",
                "evidence_function": "direct_support",
                "review_basis": "selected_sections_reviewed",
            }
        ],
        "contrary_evidence": [],
    }


def round_record(round_id, round_type):
    return {
        "round_id": round_id,
        "round_type": round_type,
        "research_question": "What role do corporations play in public international law?",
        "actual_budget": {
            "bibliographic_discovery": 1,
            "full_text_acquisition": 1,
            "substantive_review": 1,
        },
        "next_round_options": [],
    }


class RoundBundleValidationTests(unittest.TestCase):
    def test_bundle_rejects_unknown_source_and_claim_references(self):
        bundle = valid_bundle()
        bundle["featured_source_keys"].append("SRC-MISSING")
        bundle["claim_ids"].append("CLM-MISSING")

        errors = validate_bundle(
            bundle,
            sources=[reviewed_source("SRC-1")],
            claims=[supported_claim("CLM-1")],
            rounds=[round_record("R1", "breadth")],
        )

        self.assertTrue(any("SRC-MISSING" in error for error in errors))
        self.assertTrue(any("CLM-MISSING" in error for error in errors))

    def test_bundle_requires_the_complete_output_contract(self):
        bundle = valid_bundle()
        del bundle["generated_at"]

        errors = validate_bundle(
            bundle,
            sources=[reviewed_source("SRC-1")],
            claims=[supported_claim("CLM-1")],
            rounds=[round_record("R1", "breadth")],
        )

        self.assertTrue(any("generated_at" in error for error in errors))

    def test_bundle_resolves_nested_and_bibliography_references(self):
        bundle = valid_bundle()
        bundle["narrative_sections"][0]["source_keys"] = ["SRC-NARRATIVE-MISSING"]
        bundle["narrative_sections"][0]["claim_ids"] = ["CLM-NARRATIVE-MISSING"]
        bundle["bibliography_selection"] = ["SRC-BIBLIOGRAPHY-MISSING"]

        errors = validate_bundle(
            bundle,
            sources=[reviewed_source("SRC-1")],
            claims=[supported_claim("CLM-1")],
            rounds=[round_record("R1", "breadth")],
        )

        for missing_id in [
            "SRC-NARRATIVE-MISSING",
            "CLM-NARRATIVE-MISSING",
            "SRC-BIBLIOGRAPHY-MISSING",
        ]:
            with self.subTest(missing_id=missing_id):
                self.assertTrue(any(missing_id in error for error in errors))

    def test_bundle_rejects_historical_or_unsupported_current_claims(self):
        historical = supported_claim("CLM-1")
        historical["status"] = "superseded"
        historical["supporting_evidence"] = []

        errors = validate_bundle(
            valid_bundle(),
            sources=[reviewed_source("SRC-1")],
            claims=[historical],
            rounds=[round_record("R1", "breadth")],
        )

        self.assertTrue(any("CLM-1" in error and "current" in error for error in errors))
        self.assertTrue(any("CLM-1" in error and "evidence" in error for error in errors))

    def test_bundle_matches_the_round_checkpoint_budget_and_options(self):
        bundle = valid_bundle()
        bundle["budget_summary"]["substantive_review"] = 2
        bundle["next_round_options"] = [{"option_id": "different"}]

        errors = validate_bundle(
            bundle,
            sources=[reviewed_source("SRC-1")],
            claims=[supported_claim("CLM-1")],
            rounds=[round_record("R1", "breadth")],
        )

        self.assertTrue(any("budget_summary" in error for error in errors))
        self.assertTrue(any("next_round_options" in error for error in errors))

        bundle["round_id"] = "R2"
        errors = validate_bundle(
            bundle,
            sources=[reviewed_source("SRC-1")],
            claims=[supported_claim("CLM-1")],
            rounds=[round_record("R1", "breadth")],
        )
        self.assertTrue(any("R2" in error and "round" in error.lower() for error in errors))

    def test_bundle_rejects_private_markers_and_local_paths(self):
        bundle = valid_bundle()
        bundle["narrative_sections"][0]["body"] = (
            "Drafted from /Users/researcher/private/notes.docx and file:///tmp/seed.pdf"
        )
        bundle["privacy_classification"] = "private_note_reference"
        bundle["externalizable"] = False

        errors = validate_bundle(
            bundle,
            sources=[reviewed_source("SRC-1")],
            claims=[supported_claim("CLM-1")],
            rounds=[round_record("R1", "breadth")],
        )

        self.assertTrue(any("privacy" in error.lower() for error in errors))
        self.assertTrue(any("externalizable" in error for error in errors))
        self.assertTrue(any("local path" in error.lower() for error in errors))

    def test_reader_validator_can_validate_a_bundle_and_preserves_standalone_mode(self):
        report = "# Report\n\n## Findings\n\nA concise finding [SRC-1].\n"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            report_path = root / "report.md"
            bundle_path = root / "bundle.json"
            sources_path = root / "sources.jsonl"
            claims_path = root / "claims.jsonl"
            rounds_path = root / "rounds.jsonl"
            report_path.write_text(report, encoding="utf-8")
            bundle_path.write_text(json.dumps(valid_bundle()), encoding="utf-8")
            sources_path.write_text(
                json.dumps(reviewed_source("SRC-1")) + "\n", encoding="utf-8"
            )
            claims_path.write_text(
                json.dumps(supported_claim("CLM-1")) + "\n", encoding="utf-8"
            )
            rounds_path.write_text(
                json.dumps(round_record("R1", "breadth")) + "\n", encoding="utf-8"
            )

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(0, validate_reader_report_main([str(report_path)]))

            invalid_bundle = valid_bundle()
            invalid_bundle["featured_source_keys"].append("SRC-MISSING")
            bundle_path.write_text(json.dumps(invalid_bundle), encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                result = validate_reader_report_main(
                    [
                        str(report_path),
                        "--bundle",
                        str(bundle_path),
                        "--sources",
                        str(sources_path),
                        "--claims",
                        str(claims_path),
                        "--rounds",
                        str(rounds_path),
                    ]
                )

            self.assertEqual(1, result)
            self.assertIn("SRC-MISSING", stderr.getvalue())

    def test_bundle_keeps_narrative_references_in_rendering_selections(self):
        bundle = valid_bundle()
        bundle["bibliography_selection"] = []
        bundle["claim_ids"] = []

        errors = validate_bundle(
            bundle,
            sources=[reviewed_source("SRC-1")],
            claims=[supported_claim("CLM-1")],
            rounds=[round_record("R1", "breadth")],
        )

        self.assertTrue(
            any(
                "SRC-1" in error and "bibliography_selection" in error
                for error in errors
            )
        )
        self.assertTrue(
            any("CLM-1" in error and "claim_ids" in error for error in errors)
        )

    def test_bundle_question_matches_the_round_checkpoint(self):
        bundle = valid_bundle()
        bundle["research_question"] = "A different question"

        errors = validate_bundle(
            bundle,
            sources=[reviewed_source("SRC-1")],
            claims=[supported_claim("CLM-1")],
            rounds=[round_record("R1", "breadth")],
        )

        self.assertTrue(any("research_question" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
