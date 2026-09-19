from pathlib import Path
import csv
import json
import re
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_research_outputs import BundleValidationError, render_outputs


def write_jsonl(path, records):
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def source_record(source_key, title):
    return {
        "source_key": source_key,
        "identity_evidence": {
            "normalized_title": title,
            "raw_citation": f"Author, {title} (2026)",
        },
        "source_type": "article",
        "language": "en",
        "links": [
            {"kind": "publisher", "url": f"https://example.test/{source_key}"}
        ],
        "scholarly_importance": {"level": "major", "reason": "Directly relevant."},
        "acquisition_priority": "should_obtain",
        "availability": "open_full_text",
        "review_extent": "selected_sections_reviewed",
        "reading_priority": "priority_reading",
        "round_membership": [{"round_id": "R1", "functions": ["reviewed"]}],
        "description": f"{title} examines the research question.",
        "inclusion_reason": "It supports the selected checkpoint.",
    }


def claim_record():
    return {
        "claim_id": "CLM-1",
        "claim_text": "The reviewed literature identifies more than one corporate role.",
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
        "reader_qualification": "The finding is limited to the reviewed literature.",
    }


def round_record():
    return {
        "round_id": "R1",
        "kind": "main",
        "round_type": "breadth",
        "status": "completed",
        "research_question": "What roles do corporations play in public international law?",
        "actual_budget": {
            "bibliographic_discovery": 2,
            "full_text_acquisition": 2,
            "substantive_review": 2,
        },
        "next_round_options": [],
    }


def bundle():
    return {
        "checkpoint_id": "CP-R1",
        "round_id": "R1",
        "generated_at": "2026-09-18T12:00:00Z",
        "reader_language": "en",
        "research_question": "What roles do corporations play in public international law?",
        "narrative_sections": [
            {
                "section_id": "finding",
                "title": "Finding",
                "body": "The reviewed literature identifies more than one role.",
                "source_keys": ["SRC-1", "SRC-2"],
                "claim_ids": ["CLM-1"],
            }
        ],
        "featured_source_keys": ["SRC-1", "SRC-2"],
        "claim_ids": ["CLM-1"],
        "budget_summary": {
            "bibliographic_discovery": 2,
            "full_text_acquisition": 2,
            "substantive_review": 2,
        },
        "gaps": ["State practice remains underrepresented."],
        "next_round_options": [],
        "bibliography_selection": ["SRC-1", "SRC-2"],
        "privacy_classification": "public_research_output",
        "externalizable": True,
    }


class RenderResearchOutputsTests(unittest.TestCase):
    def setUp(self):
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary_directory.name)
        self.bundle_path = self.root / "round-bundle.json"
        self.source_path = self.root / "sources.jsonl"
        self.claim_path = self.root / "claims.jsonl"
        self.round_path = self.root / "rounds.jsonl"
        self.output_root = self.root / "project"
        self.bundle_path.write_text(json.dumps(bundle()), encoding="utf-8")
        write_jsonl(
            self.source_path,
            [source_record("SRC-1", "First Source"), source_record("SRC-2", "Second Source")],
        )
        write_jsonl(self.claim_path, [claim_record()])
        write_jsonl(self.round_path, [round_record()])

    def tearDown(self):
        self._temporary_directory.cleanup()

    def test_one_bundle_renders_matching_source_sets(self):
        outputs = render_outputs(
            bundle_path=self.bundle_path,
            source_path=self.source_path,
            claim_path=self.claim_path,
            round_path=self.round_path,
            output_root=self.output_root,
        )

        expected = {"SRC-1", "SRC-2"}
        markdown_keys = set(re.findall(r"\[(SRC-[^\]]+)\]", outputs.round_markdown.read_text()))
        html_keys = set(re.findall(r'data-source-key="(SRC-[^"]+)"', outputs.round_html.read_text()))
        with outputs.bibliography_csv.open(newline="", encoding="utf-8") as handle:
            csv_keys = {row["source_key"] for row in csv.DictReader(handle)}

        self.assertEqual(expected, markdown_keys)
        self.assertEqual(expected, html_keys)
        self.assertEqual(expected, csv_keys)
        self.assertTrue(outputs.synthesis_markdown.is_file())
        self.assertTrue(outputs.project_index_html.is_file())

    def test_failed_render_keeps_last_valid_index(self):
        index_path = self.output_root / "presentations" / "index.html"
        index_path.parent.mkdir(parents=True)
        previous = b"previous valid project index"
        index_path.write_bytes(previous)
        invalid = bundle()
        invalid["featured_source_keys"].append("SRC-MISSING")
        self.bundle_path.write_text(json.dumps(invalid), encoding="utf-8")

        with self.assertRaises(BundleValidationError):
            render_outputs(
                bundle_path=self.bundle_path,
                source_path=self.source_path,
                claim_path=self.claim_path,
                round_path=self.round_path,
                output_root=self.output_root,
            )

        self.assertEqual(previous, index_path.read_bytes())

    def test_render_creates_versioned_synthesis_and_self_contained_hub(self):
        outputs = render_outputs(
            bundle_path=self.bundle_path,
            source_path=self.source_path,
            claim_path=self.claim_path,
            round_path=self.round_path,
            output_root=self.output_root,
        )

        self.assertEqual(
            self.output_root / "synthesis" / "synthesis-CP-R1.md",
            outputs.synthesis_markdown,
        )
        current = self.output_root / "synthesis" / "current-synthesis.md"
        versioned_html = self.output_root / "presentations" / "versions" / "CP-R1.html"
        self.assertEqual(outputs.synthesis_markdown.read_bytes(), current.read_bytes())
        self.assertEqual(versioned_html.read_bytes(), outputs.project_index_html.read_bytes())
        rendered = outputs.project_index_html.read_text(encoding="utf-8")
        self.assertIn("@media print", rendered)
        self.assertIn("<main", rendered)
        self.assertIn("<table", rendered)
        self.assertIn("<caption", rendered)
        self.assertNotRegex(rendered, r'<(?:link|script|img)[^>]+(?:href|src)=["\']https?://')
        self.assertNotRegex(rendered, r"url\(\s*[\"']?https?://")
        self.assertIn('data-claim-id="CLM-1"', rendered)

    def test_immutable_round_report_is_not_replaced_by_changed_content(self):
        outputs = render_outputs(
            bundle_path=self.bundle_path,
            source_path=self.source_path,
            claim_path=self.claim_path,
            round_path=self.round_path,
            output_root=self.output_root,
        )
        previous_report = outputs.round_markdown.read_bytes()
        previous_index = outputs.project_index_html.read_bytes()
        changed = bundle()
        changed["checkpoint_id"] = "CP-R1-CORRECTED"
        changed["narrative_sections"][0]["body"] = "Changed after publication."
        self.bundle_path.write_text(json.dumps(changed), encoding="utf-8")

        with self.assertRaises(FileExistsError):
            render_outputs(
                bundle_path=self.bundle_path,
                source_path=self.source_path,
                claim_path=self.claim_path,
                round_path=self.round_path,
                output_root=self.output_root,
            )

        self.assertEqual(previous_report, outputs.round_markdown.read_bytes())
        self.assertEqual(previous_index, outputs.project_index_html.read_bytes())

    def test_render_rejects_private_path_in_selected_reader_content(self):
        source = source_record("SRC-1", "First Source")
        source["identity_evidence"]["raw_citation"] = "/Users/researcher/private.pdf"
        write_jsonl(self.source_path, [source, source_record("SRC-2", "Second Source")])

        with self.assertRaisesRegex(BundleValidationError, "private local path"):
            render_outputs(
                bundle_path=self.bundle_path,
                source_path=self.source_path,
                claim_path=self.claim_path,
                round_path=self.round_path,
                output_root=self.output_root,
            )

        self.assertFalse((self.output_root / "presentations" / "index.html").exists())

    def test_render_requires_a_completed_round(self):
        active = round_record()
        active["status"] = "active"
        write_jsonl(self.round_path, [active])

        with self.assertRaisesRegex(BundleValidationError, "completed round"):
            render_outputs(
                bundle_path=self.bundle_path,
                source_path=self.source_path,
                claim_path=self.claim_path,
                round_path=self.round_path,
                output_root=self.output_root,
            )


if __name__ == "__main__":
    unittest.main()
