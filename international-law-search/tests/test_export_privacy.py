import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_export_manifest import validate_export_manifest


class ExportPrivacyGuardTests(unittest.TestCase):
    def write_manifest(self, suffix, content):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / f"export{suffix}"
        path.write_text(content, encoding="utf-8")
        return path

    def test_jsonl_rejects_private_note_reference(self):
        record = {
            "export_item_id": "item-1",
            "privacy_classification": "private_note_reference",
            "externalizable": False,
            "content": "Private note placeholder",
        }
        path = self.write_manifest(".jsonl", json.dumps(record) + "\n")

        errors = validate_export_manifest(path)

        self.assertTrue(any("private_note_reference" in error for error in errors))

    def test_jsonl_rejects_non_externalizable_item(self):
        record = {
            "export_item_id": "item-2",
            "privacy_classification": "public_citation_extract",
            "externalizable": False,
            "content": "Published citation text",
        }
        path = self.write_manifest(".jsonl", json.dumps(record) + "\n")

        errors = validate_export_manifest(path)

        self.assertTrue(any("externalizable=false" in error for error in errors))

    def test_public_jsonl_manifest_with_https_link_passes(self):
        record = {
            "export_item_id": "item-public",
            "privacy_classification": "public_citation_extract",
            "externalizable": True,
            "content": "Published citation text",
            "stable_url": "https://example.test/article",
        }
        path = self.write_manifest(".jsonl", json.dumps(record) + "\n")

        self.assertEqual([], validate_export_manifest(path))

    def test_public_research_output_markdown_passes(self):
        text = (
            "---\n"
            "privacy_classification: public_research_output\n"
            "externalizable: true\n"
            "---\n\n"
            "# Research report\n\nSource-grounded public synthesis.\n"
        )
        path = self.write_manifest(".md", text)

        self.assertEqual([], validate_export_manifest(path))

    def test_jsonl_requires_explicit_privacy_fields(self):
        path = self.write_manifest(
            ".jsonl",
            json.dumps({"export_item_id": "item-3", "content": "Citation"}) + "\n",
        )

        errors = validate_export_manifest(path)

        self.assertTrue(any("privacy_classification" in error for error in errors))
        self.assertTrue(any("externalizable" in error for error in errors))

    def test_jsonl_rejects_file_uri_anywhere_in_record(self):
        record = {
            "export_item_id": "item-4",
            "privacy_classification": "public_citation_extract",
            "externalizable": True,
            "content": "Published citation text",
            "provenance": {"locator": "file:///Users/researcher/private.pdf"},
        }
        path = self.write_manifest(".jsonl", json.dumps(record) + "\n")

        errors = validate_export_manifest(path)

        self.assertTrue(any("file://" in error for error in errors))

    def test_jsonl_rejects_absolute_local_paths(self):
        for local_path in (
            "/Users/researcher/project/article.pdf",
            "/private.pdf",
            r"C:\Users\researcher\project\article.pdf",
        ):
            with self.subTest(local_path=local_path):
                record = {
                    "export_item_id": "item-path",
                    "privacy_classification": "public_citation_extract",
                    "externalizable": True,
                    "content": f"Loaded from {local_path}",
                }
                path = self.write_manifest(".jsonl", json.dumps(record) + "\n")

                errors = validate_export_manifest(path)

                self.assertTrue(any("absolute local path" in error for error in errors))

    def test_reader_bundle_rejects_local_path_in_narrative_text(self):
        record = {
            "privacy_classification": "public_research_output",
            "externalizable": True,
            "narrative_sections": [
                {"text": "/Users/example/private-note.pdf"}
            ],
        }
        path = self.write_manifest(".jsonl", json.dumps(record) + "\n")

        errors = validate_export_manifest(path)

        self.assertTrue(any("local path" in error for error in errors))

    def test_jsonl_rejects_nested_non_externalizable_content(self):
        record = {
            "export_item_id": "item-nested",
            "privacy_classification": "public_citation_extract",
            "externalizable": True,
            "content": "Public report text",
            "provenance": {
                "privacy_classification": "private_note_reference",
                "externalizable": False,
            },
        }
        path = self.write_manifest(".jsonl", json.dumps(record) + "\n")

        errors = validate_export_manifest(path)

        self.assertTrue(any("nested private_note_reference" in error for error in errors))
        self.assertTrue(any("nested externalizable=false" in error for error in errors))

    def test_markdown_rejects_private_manifest(self):
        text = (
            "---\n"
            "privacy_classification: private_note_reference\n"
            "externalizable: false\n"
            "---\n\n"
            "# Search output\n\nPrivate note placeholder\n"
        )
        path = self.write_manifest(".md", text)

        errors = validate_export_manifest(path)

        self.assertTrue(any("private_note_reference" in error for error in errors))
        self.assertTrue(any("externalizable=false" in error for error in errors))

    def test_markdown_rejects_private_marker_hidden_in_body(self):
        text = (
            "---\n"
            "privacy_classification: public_citation_extract\n"
            "externalizable: true\n"
            "---\n\n"
            "# Search output\n\n"
            "Internal provenance: externalizable=false\n"
        )
        path = self.write_manifest(".md", text)

        errors = validate_export_manifest(path)

        self.assertTrue(any("forbidden privacy marker" in error for error in errors))


class PrivacySchemaContractTests(unittest.TestCase):
    def load_schema(self, name):
        return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))

    def test_discovery_records_define_privacy_classification_and_externalizability(self):
        paths = {
            "source-ledger-record.schema.json": "discovery_provenance",
            "candidate-source-record.schema.json": "discovery_history",
            "source-record.schema.json": "discovery_history",
        }
        for name, field in paths.items():
            with self.subTest(schema=name):
                item = self.load_schema(name)["properties"][field]["items"]
                self.assertEqual(
                    ["public_citation_extract", "private_note_reference"],
                    item["properties"]["privacy_classification"]["enum"],
                )
                self.assertEqual(
                    "boolean", item["properties"]["externalizable"]["type"]
                )
                local_seed_rule = next(
                    rule
                    for rule in item["allOf"]
                    if rule["if"]["properties"]["method"].get("const")
                    == "local_seed"
                )
                self.assertTrue(
                    {"privacy_classification", "externalizable"}.issubset(
                        local_seed_rule["then"]["required"]
                    )
                )
                private_rule = next(
                    rule
                    for rule in item["allOf"]
                    if rule["if"].get("properties", {})
                    .get("privacy_classification", {})
                    .get("const")
                    == "private_note_reference"
                )
                self.assertIn("externalizable", private_rule["then"]["required"])
                self.assertFalse(
                    private_rule["then"]["properties"]["externalizable"]["const"]
                )


class PrivacyWorkflowContractTests(unittest.TestCase):
    def test_privacy_policy_covers_every_outbound_surface_and_validator(self):
        access = (ROOT / "references/access-and-privacy.md").read_text(
            encoding="utf-8"
        ).lower()
        deliverables = (ROOT / "references/deliverables.md").read_text(
            encoding="utf-8"
        ).lower()
        brief = (ROOT / "templates/subagent-brief.md").read_text(
            encoding="utf-8"
        ).lower()

        for term in (
            "public_citation_extract",
            "private_note_reference",
            "externalizable",
            "external queries",
            "outbound logs",
            "reader-facing output",
        ):
            with self.subTest(term=term):
                self.assertIn(term, access)
        self.assertIn("scripts/validate_export_manifest.py", deliverables)
        self.assertIn("private_note_reference", brief)
        self.assertIn("opaque local id", brief)


if __name__ == "__main__":
    unittest.main()
