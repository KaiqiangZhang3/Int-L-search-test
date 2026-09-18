import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_corpus.py"


def source_record(source_id, *, doi=None):
    external_ids = {"doi": doi} if doi else {}
    return {
        "id": source_id,
        "external_ids": external_ids,
        "title": f"Source {source_id}",
        "creators": ["Author"],
        "date": "2026",
        "publication": "Journal",
        "access_status": "Metadata only",
        "description": "Identifies the source's subject and retrieval value.",
        "inclusion_reason": "Directly addresses the approved search question.",
        "description_basis": "metadata",
        "description_retrieval_id": f"retrieval-{source_id}",
        "retrieval_history": [
            {
                "event_id": f"retrieval-{source_id}",
                "access_status": "Metadata only",
            }
        ],
    }


def verified_edge(source_id="source-1", target_id="source-2"):
    return {
        "source_id": source_id,
        "target_id": target_id,
        "relation": "cites",
        "status": "verified",
        "record_scope": "canonical",
        "evidence": {"source": "Source source-1", "location": "p. 12 n. 4"},
    }


class ValidateCorpusCliTests(unittest.TestCase):
    def run_validator(self, sources, edges):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "sources.jsonl"
            edge_path = root / "edges.jsonl"
            source_path.write_text(
                "".join(json.dumps(item) + "\n" for item in sources),
                encoding="utf-8",
            )
            edge_path.write_text(
                "".join(json.dumps(item) + "\n" for item in edges),
                encoding="utf-8",
            )
            return subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--sources",
                    str(source_path),
                    "--edges",
                    str(edge_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

    def assert_failure(self, result, location, message):
        self.assertNotEqual(0, result.returncode)
        self.assertIn(location, result.stderr)
        self.assertIn(message, result.stderr)

    def test_accepts_a_valid_canonical_corpus(self):
        result = self.run_validator(
            [
                source_record("source-1", doi="10.1000/one"),
                source_record("source-2", doi="10.1000/two"),
            ],
            [verified_edge()],
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Validated 2 sources and 1 verified edge", result.stdout)

    def test_rejects_duplicate_source_ids_with_line_number(self):
        result = self.run_validator(
            [source_record("duplicate"), source_record("duplicate")],
            [],
        )

        self.assert_failure(result, "sources.jsonl:2", "duplicate source id")

    def test_rejects_source_without_sufficient_identity_key(self):
        record = source_record("source-1")
        record["creators"] = []
        result = self.run_validator([record], [])

        self.assert_failure(result, "sources.jsonl:1", "sufficient identity key")

    def test_reports_retrieval_link_error_at_source_line(self):
        record = source_record("source-1")
        record["description_retrieval_id"] = "missing"
        result = self.run_validator([record], [])

        self.assert_failure(result, "sources.jsonl:1", "description_retrieval_id")

    def test_rejects_blank_reader_facing_source_fields(self):
        for field, value in (("description", ""), ("inclusion_reason", "   ")):
            with self.subTest(field=field):
                record = source_record("source-1")
                record[field] = value
                result = self.run_validator([record], [])

                self.assert_failure(result, "sources.jsonl:1", field)
                self.assertIn("non-empty", result.stderr)

    def test_rejects_unresolved_template_placeholders(self):
        for field in ("description", "inclusion_reason"):
            with self.subTest(field=field):
                record = source_record("source-1")
                record[field] = f"Still unresolved: {{{{{field}}}}}"
                result = self.run_validator([record], [])

                self.assert_failure(result, "sources.jsonl:1", field)
                self.assertIn("placeholder", result.stderr)

    def test_rejects_todo_and_tbd_placeholder_values(self):
        for field, value in (
            ("description", "TODO: add source description"),
            ("inclusion_reason", "TBD"),
        ):
            with self.subTest(field=field):
                record = source_record("source-1")
                record[field] = value
                result = self.run_validator([record], [])

                self.assert_failure(result, "sources.jsonl:1", field)
                self.assertIn("placeholder", result.stderr)

    def test_rejects_canonical_cited_by_edges(self):
        edge = verified_edge()
        edge["relation"] = "cited_by"
        result = self.run_validator(
            [source_record("source-1"), source_record("source-2")],
            [edge],
        )

        self.assert_failure(result, "edges.jsonl:1", "cited_by")

    def test_rejects_candidate_edges_from_final_corpus(self):
        edge = verified_edge()
        edge["status"] = "candidate"
        edge["record_scope"] = "candidate"
        result = self.run_validator(
            [source_record("source-1"), source_record("source-2")],
            [edge],
        )

        self.assert_failure(result, "edges.jsonl:1", "candidate edge")

    def test_rejects_noncanonical_edge_scope(self):
        edge = verified_edge()
        edge["record_scope"] = "candidate"
        result = self.run_validator(
            [source_record("source-1"), source_record("source-2")],
            [edge],
        )

        self.assert_failure(result, "edges.jsonl:1", "record_scope")

    def test_rejects_verified_edge_without_complete_evidence(self):
        edge = verified_edge()
        edge["evidence"] = {"source": "", "location": "p. 12"}
        result = self.run_validator(
            [source_record("source-1"), source_record("source-2")],
            [edge],
        )

        self.assert_failure(result, "edges.jsonl:1", "evidence")

    def test_rejects_edge_with_missing_endpoint(self):
        result = self.run_validator(
            [source_record("source-1")],
            [verified_edge(target_id="missing")],
        )

        self.assert_failure(result, "edges.jsonl:1", "unknown target_id")
