from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "init_workspace.py"


def load_module():
    spec = importlib.util.spec_from_file_location("init_workspace", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkspaceTests(unittest.TestCase):
    def test_initializer_creates_resumable_layout_without_overwrite(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "pil-search"
            module.initialize(target, "pil-search")
            expected = [
                "state.json",
                "plan/search-plan.md",
                "corpus/sources.jsonl",
                "corpus/edges.jsonl",
                "logs/retrieval.jsonl",
                "exports/.gitkeep",
            ]
            self.assertTrue(all((target / path).exists() for path in expected))
            state = json.loads((target / "state.json").read_text(encoding="utf-8"))
            self.assertEqual("planning", state["status"])
            with self.assertRaises(FileExistsError):
                module.initialize(target, "pil-search")

    def test_initializer_uses_utc_timestamps(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "pil-search"
            module.initialize(target, "pil-search")
            state = json.loads((target / "state.json").read_text(encoding="utf-8"))

            for field in ["created_at", "updated_at"]:
                timestamp = datetime.fromisoformat(state[field])
                self.assertEqual(timezone.utc, timestamp.tzinfo)

    def test_failed_initialization_removes_staging_and_allows_retry(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            target = parent / "pil-search"

            def fail_build(staging, project_id, timestamp):
                raise RuntimeError("injected build failure")

            with self.assertRaisesRegex(RuntimeError, "injected build failure"):
                module.initialize(target, "pil-search", _builder=fail_build)

            self.assertFalse(target.exists())
            self.assertEqual([], list(parent.glob(".pil-search.*.tmp")))
            module.initialize(target, "pil-search")
            self.assertTrue((target / "state.json").is_file())

    def test_initializer_rejects_blank_and_stores_stripped_project_id(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "pil-search"

            with self.assertRaisesRegex(ValueError, "Project ID must not be empty"):
                module.initialize(target, "   ")

            self.assertFalse(target.exists())
            module.initialize(target, "  pil-search  ")
            state = json.loads((target / "state.json").read_text(encoding="utf-8"))
            self.assertEqual("pil-search", state["project_id"])

    def test_initializer_records_empty_deduplication_state(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "pil-search"
            module.initialize(target, "pil-search")
            state = json.loads((target / "state.json").read_text(encoding="utf-8"))

            self.assertEqual(
                {
                    "identity_index": {},
                    "unresolved_record_ids": [],
                    "last_merged_at": None,
                },
                state["deduplication"],
            )
            self.assertEqual("planning", state["status"])
            self.assertIsNone(state["approved_plan"])

    def test_initializer_records_empty_cumulative_coverage(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "pil-search"
            module.initialize(target, "pil-search")
            state = json.loads((target / "state.json").read_text(encoding="utf-8"))

            self.assertEqual(
                {
                    dimension: {"searched": [], "unsearched": []}
                    for dimension in (
                        "subquestions",
                        "platforms",
                        "languages",
                        "periods",
                        "authority_classes",
                    )
                },
                state["coverage"],
            )

    def test_cli_reports_existing_target_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "pil-search"
            target.mkdir()
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(target),
                    "--project-id",
                    "pil-search",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("Refusing to overwrite existing path", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_cli_reports_blank_project_id_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "pil-search"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(target),
                    "--project-id",
                    "   ",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("Project ID must not be empty", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
