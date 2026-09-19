from pathlib import Path
import importlib.util
import json
import shutil
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate_v2_workspace.py"
ROUND_OPS = ROOT / "scripts" / "round_ops.py"
SOURCE_VALIDATOR = ROOT / "scripts" / "validate_source_ledger.py"
FIXTURE = ROOT / "tests" / "fixtures" / "v3" / "v2-workspace"


def load_module():
    spec = importlib.util.spec_from_file_location("migrate_v2_workspace", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_script(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class V2MigrationTests(unittest.TestCase):
    def test_migration_preserves_identity_decisions_provenance_review_graph_and_logs(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "v2"
            target = Path(tmp) / "v3"
            shutil.copytree(FIXTURE, source)
            source_snapshot = {
                path.relative_to(source): path.read_bytes()
                for path in source.rglob("*")
                if path.is_file()
            }

            result = module.migrate(source, target)

            migrated_sources = read_jsonl(result / "knowledge" / "sources.jsonl")
            original_sources = read_jsonl(source / "corpus" / "sources.jsonl")
            self.assertEqual(
                [record["id"] for record in original_sources],
                [record["source_key"] for record in migrated_sources],
            )
            self.assertEqual(
                [record["review_extent"] for record in original_sources],
                [record["review_extent"] for record in migrated_sources],
            )
            self.assertEqual(
                [record["discovery_history"] for record in original_sources],
                [record["discovery_provenance"] for record in migrated_sources],
            )
            self.assertEqual(
                original_sources[0]["user_decisions"],
                migrated_sources[0]["user_decisions"],
            )
            original_state = json.loads((source / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(
                original_state["decision_log"],
                read_jsonl(result / "knowledge" / "decisions.jsonl"),
            )
            self.assertEqual(
                (source / "corpus" / "edges.jsonl").read_bytes(),
                (result / "knowledge" / "edges.jsonl").read_bytes(),
            )
            self.assertEqual(
                (source / "logs" / "retrieval.jsonl").read_bytes(),
                (result / "logs" / "retrieval.jsonl").read_bytes(),
            )
            self.assertEqual(
                source_snapshot,
                {
                    path.relative_to(source): path.read_bytes()
                    for path in source.rglob("*")
                    if path.is_file()
                },
            )

    def test_migration_links_legacy_rounds_and_sources_without_inventing_claims(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "v2"
            target = Path(tmp) / "v3"
            shutil.copytree(FIXTURE, source)

            result = module.migrate(source, target)

            rounds = read_jsonl(result / "knowledge" / "rounds.jsonl")
            sources = read_jsonl(result / "knowledge" / "sources.jsonl")
            self.assertEqual(["R1"], [record["round_id"] for record in rounds])
            self.assertEqual(
                ["source-001", "source-002"],
                rounds[0]["added_source_keys"],
            )
            self.assertEqual(
                [[{"round_id": "R1", "functions": ["discovered"]}]] * 2,
                [record["round_membership"] for record in sources],
            )
            self.assertEqual([], read_jsonl(result / "knowledge" / "claims.jsonl"))
            report = json.loads(
                (result / "migration-report.json").read_text(encoding="utf-8")
            )
            self.assertEqual({"round-1": "R1"}, report["round_id_map"])
            self.assertEqual(
                ["full_text_acquisition", "substantive_review"],
                report["unknown_historic_counts"]["R1"],
            )

    def test_migrated_sources_and_rounds_pass_v3_validators(self):
        module = load_module()
        source_validator = load_script(SOURCE_VALIDATOR, "validate_source_ledger")
        round_ops = load_script(ROUND_OPS, "round_ops")
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "v2"
            target = Path(tmp) / "v3"
            shutil.copytree(FIXTURE, source)
            result = module.migrate(source, target)

            self.assertEqual(
                [],
                source_validator.validate_source_ledger(
                    result / "knowledge" / "sources.jsonl"
                ),
            )
            validation_ledger = Path(tmp) / "validated-rounds.jsonl"
            for record in read_jsonl(result / "knowledge" / "rounds.jsonl"):
                round_ops.append_round(validation_ledger, record)

    def test_migration_is_atomic_when_building_fails(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "v2"
            target = Path(tmp) / "v3"
            shutil.copytree(FIXTURE, source)

            with mock.patch.object(
                module, "_build_migration", side_effect=RuntimeError("injected failure")
            ):
                with self.assertRaisesRegex(RuntimeError, "injected failure"):
                    module.migrate(source, target)

            self.assertFalse(target.exists())
            self.assertEqual([], list(Path(tmp).glob(".v3.*.tmp")))

    def test_migration_refuses_overwrite_and_repeat_migration(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "v2"
            target = Path(tmp) / "v3"
            shutil.copytree(FIXTURE, source)
            target.mkdir()

            with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite"):
                module.migrate(source, target)

            shutil.rmtree(target)
            first = module.migrate(source, target)
            second_target = Path(tmp) / "v3-again"
            with self.assertRaisesRegex(ValueError, "expected schema_version 2"):
                module.migrate(first, second_target)
            self.assertFalse(second_target.exists())


if __name__ == "__main__":
    unittest.main()
