from pathlib import Path
import importlib.util
import json
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate_v1_workspace.py"
FIXTURE = ROOT / "tests" / "fixtures" / "user-centered" / "v1-workspace"


def load_module():
    spec = importlib.util.spec_from_file_location("migrate_v1_workspace", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class MigrationTests(unittest.TestCase):
    def test_migration_preserves_source_ids_and_flags_ambiguous_access(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "project"
            destination = Path(tmp) / "project-v2"
            shutil.copytree(FIXTURE, source)

            result = module.migrate(source, destination)
            migrated = read_jsonl(result / "corpus" / "sources.jsonl")

            self.assertEqual("source-001", migrated[0]["id"])
            self.assertEqual(["source-001"], migrated[0]["legacy_ids"])
            self.assertTrue(migrated[0]["migration_review_required"])
            report = json.loads(
                (result / "migration-report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(["source-001"], report["review_required_source_ids"])
            self.assertTrue((source / "corpus" / "sources.jsonl").exists())

            self.assertEqual("subscription_full_text", migrated[0]["availability"])
            self.assertEqual(
                "full_text_substantively_reviewed",
                migrated[0]["review_extent"],
            )
            self.assertEqual(
                "full_text", migrated[0]["description_basis"]["kind"]
            )

    def test_preserved_local_full_text_route_resolves_access_ambiguity(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "project"
            destination = Path(tmp) / "project-v2"
            shutil.copytree(FIXTURE, source)
            records = read_jsonl(source / "corpus" / "sources.jsonl")
            records[0]["local_path"] = "private/article.pdf"
            records[0]["retrieval_history"][0]["local_path"] = "private/article.pdf"
            (source / "corpus" / "sources.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )

            result = module.migrate(source, destination)
            migrated = read_jsonl(result / "corpus" / "sources.jsonl")[0]

            self.assertEqual("open_full_text", migrated["availability"])
            self.assertFalse(migrated["migration_review_required"])

    def test_migration_preserves_state_history_and_separates_provenance_edges(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "project"
            destination = Path(tmp) / "project-v2"
            shutil.copytree(FIXTURE, source)
            original_state = json.loads(
                (source / "state.json").read_text(encoding="utf-8")
            )
            original_log = read_jsonl(source / "logs" / "retrieval.jsonl")

            result = module.migrate(source, destination)
            migrated_state = json.loads(
                (result / "state.json").read_text(encoding="utf-8")
            )
            migrated_sources = read_jsonl(result / "corpus" / "sources.jsonl")
            migrated_edges = read_jsonl(result / "corpus" / "edges.jsonl")
            migrated_log = read_jsonl(result / "logs" / "retrieval.jsonl")

            self.assertEqual(2, migrated_state["schema_version"])
            for field in ("approved_plan", "rounds", "coverage", "stopping"):
                self.assertEqual(original_state[field], migrated_state[field])
            self.assertEqual(
                [event["event_id"] for event in original_log],
                [event["event_id"] for event in migrated_log],
            )
            self.assertNotIn(
                "discovered_from", {edge["relation"] for edge in migrated_edges}
            )
            citation = next(
                edge for edge in migrated_edges if edge["relation"] == "cites"
            )
            interpretation = next(
                edge for edge in migrated_edges if edge["relation"] == "interprets"
            )
            self.assertEqual("verified", citation["status"])
            self.assertEqual("candidate", interpretation["status"])
            source_002 = next(
                record for record in migrated_sources if record["id"] == "source-002"
            )
            self.assertIn(
                {"method": "source", "value": "source-001 (bibliography)"},
                source_002["discovery_history"],
            )


if __name__ == "__main__":
    unittest.main()
