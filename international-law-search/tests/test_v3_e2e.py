import json
from pathlib import Path
import sys
import tempfile
import unittest


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "v3"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from round_ops import allocate_round, append_round
from validate_claim_ledger import validate_claim_ledger


def load_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class FixtureProject:
    def __init__(self, name):
        self.root = FIXTURES / name
        self.rounds = load_jsonl(self.root / "rounds.jsonl")
        self.sources = load_jsonl(self.root / "sources.jsonl")
        claims_path = self.root / "claims.jsonl"
        self.claims = load_jsonl(claims_path) if claims_path.exists() else []

    def source(self, source_key):
        return next(item for item in self.sources if item["source_key"] == source_key)

    def claim(self, claim_id):
        return next(item for item in self.claims if item["claim_id"] == claim_id)


class V3EndToEndFixtureTests(unittest.TestCase):
    def test_doctoral_round_separates_discovery_acquisition_and_review(self):
        project = FixtureProject("doctoral-corpus")
        first_round = project.rounds[0]

        self.assertEqual(80, first_round["planned_budget"]["bibliographic_discovery"])
        self.assertEqual(25, first_round["planned_budget"]["full_text_acquisition"])
        self.assertEqual(12, first_round["planned_budget"]["substantive_review"])
        book = project.source("SRC-BOOK-1")
        self.assertEqual("must_obtain", book["acquisition_priority"])
        self.assertEqual("not_reviewed", book["review_extent"])

    def test_user_may_choose_breadth_expansion_after_breadth(self):
        project = FixtureProject("doctoral-corpus")

        self.assertEqual(
            ["breadth", "breadth_expansion"],
            [item["round_type"] for item in project.rounds[:2]],
        )

    def test_primary_materials_round_records_an_honest_real_surface_check(self):
        project = FixtureProject("doctoral-corpus")
        checks = load_jsonl(project.root / "surface-checks.jsonl")

        self.assertEqual("primary_materials", project.rounds[2]["round_type"])
        self.assertEqual("official_case_law", checks[0]["surface_type"])
        self.assertTrue(checks[0]["surface_url"].startswith("https://www.icj-cij.org/"))
        self.assertIn(
            checks[0]["result"],
            {"responsive_results", "zero_responsive_results"},
        )
        if checks[0]["result"] == "zero_responsive_results":
            self.assertEqual([], checks[0]["responsive_source_keys"])
            self.assertIn("not proof", checks[0]["coverage_statement"])

    def test_side_round_updates_claims_without_advancing_main_round(self):
        project = FixtureProject("side-round")
        side_round = next(item for item in project.rounds if item["kind"] == "side")
        next_main = allocate_round(
            project.rounds, kind="main", round_type="gap_filling"
        )

        self.assertEqual("R2.S1", side_round["round_id"])
        self.assertEqual("R3", next_main["round_id"])
        self.assertEqual("contested", project.claim("CLM-1")["status"])

    def test_side_round_contested_claim_has_reviewed_evidence_on_both_sides(self):
        project = FixtureProject("side-round")

        self.assertEqual(
            [],
            validate_claim_ledger(
                project.root / "claims.jsonl", project.root / "sources.jsonl"
            ),
        )
        claim = project.claim("CLM-1")
        self.assertTrue(claim["supporting_evidence"])
        self.assertTrue(claim["contrary_evidence"])

    def test_side_round_preserves_multilingual_non_equivalence(self):
        project = FixtureProject("side-round")
        terminology = load_jsonl(project.root / "terminology.jsonl")[0]

        self.assertEqual(
            {"obsolete", "desuetude", "obsolescence", "dead letter", "inapplicable"},
            {item["term"] for item in terminology["members"]},
        )
        self.assertFalse(terminology["legally_equivalent"])
        self.assertTrue(terminology["non_equivalence_note"].strip())
        self.assertTrue(all(item["search_function"] for item in terminology["members"]))

    def test_fixture_rounds_pass_the_public_append_contract(self):
        for fixture_name in ("doctoral-corpus", "side-round"):
            with self.subTest(fixture=fixture_name), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / "rounds.jsonl"
                for record in FixtureProject(fixture_name).rounds:
                    append_round(target, record)


if __name__ == "__main__":
    unittest.main()
