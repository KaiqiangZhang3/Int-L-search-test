import json
from pathlib import Path
import re
import subprocess
import sys
import unittest


REPOSITORY = Path(__file__).resolve().parents[2]
FIXTURE = REPOSITORY / "docs/superpowers/evals/fixtures/nicaragua-e2e"
E2E = REPOSITORY / "docs/superpowers/evals/2026-09-17-international-law-search-e2e.md"
VALIDATOR = REPOSITORY / "international-law-search/scripts/validate_corpus.py"
SCHEMAS = REPOSITORY / "international-law-search/schemas"


class NicaraguaE2EFixtureTests(unittest.TestCase):
    def load_jsonl(self, name):
        records = []
        for line_number, line in enumerate(
            (FIXTURE / name).read_text(encoding="utf-8").splitlines(), start=1
        ):
            if line.strip():
                with self.subTest(file=name, line=line_number):
                    record = json.loads(line)
                    self.assertIsInstance(record, dict)
                    records.append(record)
        return records

    def test_fixture_is_linked_and_approval_checkpoint_is_consistent(self):
        plan_path = FIXTURE / "approved-search-plan.md"
        state = json.loads((FIXTURE / "state.json").read_text(encoding="utf-8"))
        plan = plan_path.read_text(encoding="utf-8")
        e2e = E2E.read_text(encoding="utf-8")

        self.assertIn("fixtures/nicaragua-e2e/", e2e)
        self.assertIn("Status: `approved`", plan)
        approved_by = re.search(r"Approved by: (.+)", plan).group(1)
        approved_at = re.search(r"Approved at: (.+)", plan).group(1)
        recorded_path = re.search(r"Plan path: (.+)", plan).group(1)
        self.assertEqual("complete", state["status"])
        self.assertEqual(approved_by, state["approved_plan"]["approved_by"])
        self.assertEqual(approved_at, state["approved_plan"]["approved_at"])
        self.assertEqual(recorded_path, state["approved_plan"]["plan_path"])
        self.assertEqual("approved-search-plan.md", recorded_path)

    def test_fixture_has_cumulative_coverage_and_parseable_jsonl(self):
        state = json.loads((FIXTURE / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "subquestions",
                "platforms",
                "languages",
                "periods",
                "authority_classes",
            },
            set(state["coverage"]),
        )
        for dimension in state["coverage"].values():
            self.assertIn("searched", dimension)
            self.assertIn("unsearched", dimension)

        self.assertEqual(6, len(self.load_jsonl("sources.jsonl")))
        self.assertEqual(3, len(self.load_jsonl("edges.jsonl")))
        self.assertGreaterEqual(len(self.load_jsonl("retrieval-log.jsonl")), 6)

    def test_state_sources_and_edges_match_declared_schema_fields(self):
        state = json.loads((FIXTURE / "state.json").read_text(encoding="utf-8"))
        sources = self.load_jsonl("sources.jsonl")
        edges = self.load_jsonl("edges.jsonl")

        for schema_name, records in (
            ("project-state.schema.json", [state]),
            ("source-record.schema.json", sources),
            ("edge-record.schema.json", edges),
        ):
            schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
            allowed = set(schema["properties"])
            required = set(schema["required"])
            for record in records:
                with self.subTest(schema=schema_name, record=record.get("id")):
                    self.assertTrue(required.issubset(record))
                    self.assertEqual(set(), set(record) - allowed)

    def test_fixture_corpus_passes_canonical_validator(self):
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--sources",
                str(FIXTURE / "sources.jsonl"),
                "--edges",
                str(FIXTURE / "edges.jsonl"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Validated 6 sources and 3 verified edges", result.stdout)


if __name__ == "__main__":
    unittest.main()
