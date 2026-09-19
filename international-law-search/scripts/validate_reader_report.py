#!/usr/bin/env python3
"""Validate deterministic structure and traceability rules for reader reports."""

import argparse
from pathlib import Path
import re
import sys

from validate_round_bundle import validate_bundle_files


FORBIDDEN_MARKERS = ("{{", "}}", "TODO", "TBD")
MANUAL_REVIEW = re.compile(
    r"manual review required|需(?:要)?人工复核|待人工复核",
    re.IGNORECASE,
)
SOURCE_CITATION = re.compile(r"\[[A-Za-z0-9][A-Za-z0-9._:-]*\]")
DECLARED_CLAIM = re.compile(
    r"^\s*(?:[-*]\s+)?(?:"
    r"来源陈述|多来源趋势|谨慎归纳|"
    r"Source statement|Multi-source trend|Cautious inference"
    r")(?:（|\(|：|:)",
    re.IGNORECASE,
)
MACHINE_OPENING_HEADINGS = {
    "检索范围与限制",
    "档案检索范围与限制",
    "覆盖与缺口",
    "机器附件",
    "数据状态",
    "图谱导航",
    "Scope, stopping reason, and coverage conclusion",
    "Retrieval-oriented navigation",
}


def _section_headings(text: str) -> list[str]:
    return [
        line.removeprefix("## ").strip()
        for line in text.splitlines()
        if line.startswith("## ")
    ]


def _is_chinese(language: str) -> bool:
    return language.strip().lower() in {"zh", "zh-cn", "zh-tw", "chinese"}


def validate_report(text: str, *, language: str, final: bool) -> list[str]:
    """Return deterministic report-contract errors without judging legal merit."""

    errors = [
        f"Unresolved marker: {marker}"
        for marker in FORBIDDEN_MARKERS
        if marker in text
    ]

    if final and MANUAL_REVIEW.search(text):
        errors.append("Final report contains unresolved manual-review items")

    headings = _section_headings(text)
    if final and _is_chinese(language):
        if not headings:
            errors.append("Final Chinese report has no reader-facing sections")
        elif headings[0] in MACHINE_OPENING_HEADINGS:
            errors.append(
                f"Final Chinese report opens with machine-state section: {headings[0]}"
            )

    for line_number, line in enumerate(text.splitlines(), start=1):
        if not DECLARED_CLAIM.search(line):
            continue
        if not SOURCE_CITATION.search(line):
            errors.append(
                f"Line {line_number}: declared source-grounded claim lacks source citation"
            )

    return errors


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a reader-facing international-law report."
    )
    parser.add_argument("report", type=Path)
    parser.add_argument("--language", default="zh")
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--claims", type=Path)
    parser.add_argument("--rounds", type=Path)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        text = args.report.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"Unable to read report: {exc}", file=sys.stderr)
        return 2

    errors = validate_report(text, language=args.language, final=args.final)
    bundle_arguments = (args.bundle, args.sources, args.claims, args.rounds)
    if any(bundle_arguments):
        if not all(bundle_arguments):
            errors.append(
                "Bundle-aware validation requires --bundle, --sources, --claims, "
                "and --rounds together"
            )
        else:
            errors.extend(
                validate_bundle_files(
                    args.bundle,
                    source_path=args.sources,
                    claim_path=args.claims,
                    round_path=args.rounds,
                )
            )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1

    print("Reader report is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
