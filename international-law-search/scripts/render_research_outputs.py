#!/usr/bin/env python3
"""Render consistent reader outputs from one validated round bundle."""

from dataclasses import dataclass
from pathlib import Path
import argparse
import csv
import html
import io
import json
import os
import re
import shutil
import tempfile

from validate_round_bundle import (
    FILE_URI,
    POSIX_ABSOLUTE_PATH,
    WINDOWS_ABSOLUTE_PATH,
    validate_bundle_files,
)


class BundleValidationError(ValueError):
    """Raised when a round bundle cannot be safely rendered."""


@dataclass(frozen=True)
class RenderedOutputs:
    round_markdown: Path
    round_html: Path
    bibliography_csv: Path
    synthesis_markdown: Path | None
    project_index_html: Path


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _citation(source: dict) -> str:
    identity = source.get("identity_evidence", {})
    return identity.get("raw_citation") or identity.get("normalized_title") or source["source_key"]


def _public_links(source: dict) -> list[str]:
    return [item["url"] for item in source.get("links", []) if item.get("url", "").startswith(("https://", "http://"))]


def _round_markdown(bundle: dict, sources: list[dict], claims: list[dict]) -> str:
    lines = [
        f"# Research Round {bundle['round_id']}", "",
        f"Checkpoint: `{bundle['checkpoint_id']}`  ",
        f"Generated: {bundle['generated_at']}", "", "## Research question", "",
        bundle["research_question"],
    ]
    for section in bundle["narrative_sections"]:
        citations = ", ".join(f"[{key}]" for key in section["source_keys"])
        lines.extend(["", f"## {section['title']}", "", section["body"], "", f"Sources: {citations}"])
    if claims:
        lines.extend(["", "## Current findings", ""])
        for claim in claims:
            qualification = claim.get("reader_qualification")
            suffix = f" — {qualification}" if qualification else ""
            lines.append(f"- [{claim['claim_id']}] **{claim.get('status', 'provisional')}**: {claim.get('claim_text', '')}{suffix}")
    if bundle["gaps"]:
        lines.extend(["", "## Gaps and limits", ""])
        lines.extend(f"- {gap}" for gap in bundle["gaps"])
    lines.extend(["", "## Selected bibliography", ""])
    for source in sources:
        links = _public_links(source)
        link = f" — {links[0]}" if links else ""
        lines.extend([
            f"- [{source['source_key']}] {_citation(source)}{link}",
            f"  - What it covers: {source.get('description', 'No reader description recorded.')}",
            f"  - Why it is here: {source.get('inclusion_reason', 'Included in this checkpoint.')}",
            f"  - Access/review: {source.get('availability', 'not recorded')} / {source.get('review_extent', 'not recorded')}",
        ])
    budget = bundle["budget_summary"]
    lines.extend([
        "", "## Round checkpoint", "",
        f"- Bibliographic discovery: {budget['bibliographic_discovery']}",
        f"- Full-text acquisition: {budget['full_text_acquisition']}",
        f"- Substantive review: {budget['substantive_review']}",
    ])
    return "\n".join(lines) + "\n"


def _source_rows(sources: list[dict]) -> str:
    rows = []
    for source in sources:
        links = _public_links(source)
        citation = html.escape(_citation(source))
        if links:
            citation = f'<a href="{html.escape(links[0], quote=True)}">{citation}</a>'
        rows.append(
            f'<tr data-source-key="{html.escape(source["source_key"], quote=True)}">'
            f'<th scope="row">{html.escape(source["source_key"])}</th><td>{citation}</td>'
            f"<td>{html.escape(source.get('source_type') or 'Not recorded')}</td>"
            f"<td>{html.escape(source.get('availability') or 'Not recorded')}</td>"
            f"<td>{html.escape(source.get('review_extent') or 'Not recorded')}</td></tr>"
        )
    return "".join(rows)


def _presentation_html(bundle: dict, sources: list[dict], claims: list[dict]) -> str:
    sections = []
    for section in bundle["narrative_sections"]:
        keys = ", ".join(html.escape(key) for key in section["source_keys"])
        sections.append(f"<section><h2>{html.escape(section['title'])}</h2><p>{html.escape(section['body'])}</p><p class=\"source-note\">Sources: {keys}</p></section>")
    claim_items = "".join(
        f'<li data-claim-id="{html.escape(claim["claim_id"], quote=True)}"><strong>{html.escape(claim.get("status", "provisional").title())}:</strong> {html.escape(claim.get("claim_text", ""))}<span class="qualification">{html.escape(claim.get("reader_qualification") or "")}</span></li>'
        for claim in claims
    )
    gap_items = "".join(f"<li>{html.escape(gap)}</li>" for gap in bundle["gaps"])
    budget = bundle["budget_summary"]
    return f"""<!doctype html>
<html lang="{html.escape(bundle['reader_language'], quote=True)}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>International Law Research — {html.escape(bundle['round_id'])}</title>
<style>
:root{{--ink:#17221d;--muted:#59665f;--paper:#f5f1e7;--panel:#fffdf7;--line:#c9c2b3;--accent:#8c3b2f}}
*{{box-sizing:border-box}}body{{margin:0;color:var(--ink);background:var(--paper);font:18px Georgia,'Times New Roman',serif;line-height:1.65}}main{{max-width:76rem;margin:auto;padding:4rem 5vw}}header{{border-top:.5rem solid var(--accent);padding-top:2rem;margin-bottom:4rem}}h1{{font-size:clamp(2.4rem,6vw,5.5rem);line-height:.98;max-width:14ch;margin:.4rem 0 2rem}}h2{{font-size:1.65rem;margin-top:3.5rem}}.eyebrow,.source-note{{color:var(--muted);font-size:.88rem;letter-spacing:.04em}}.qualification{{display:block;color:var(--muted);font-size:.92em}}table{{width:100%;border-collapse:collapse;background:var(--panel);font-size:.92rem}}caption{{text-align:left;font-weight:bold;font-size:1.2rem;margin-bottom:.8rem}}th,td{{border-bottom:1px solid var(--line);padding:.8rem;text-align:left;vertical-align:top}}a{{color:var(--accent);text-underline-offset:.16em}}.checkpoint{{margin-top:4rem;padding:1.4rem;border:1px solid var(--line);background:var(--panel)}}
@media(max-width:700px){{main{{padding:2rem 1rem}}table{{display:block;overflow-x:auto}}}}@media print{{body{{background:white;font-size:11pt}}main{{max-width:none;padding:0}}a{{color:inherit;text-decoration:none}}header{{border-color:black}}}}
</style></head><body><main>
<header><p class="eyebrow">Checkpoint {html.escape(bundle['checkpoint_id'])} · {html.escape(bundle['generated_at'])}</p><h1>{html.escape(bundle['research_question'])}</h1><p>Research round {html.escape(bundle['round_id'])}</p></header>
{''.join(sections)}
<section><h2>Current findings</h2><ul>{claim_items}</ul></section>
<section><h2>Gaps and limits</h2><ul>{gap_items}</ul></section>
<section><h2>Selected bibliography</h2><table><caption>Sources included at this checkpoint</caption><thead><tr><th scope="col">ID</th><th scope="col">Citation</th><th scope="col">Type</th><th scope="col">Availability</th><th scope="col">Review</th></tr></thead><tbody>{_source_rows(sources)}</tbody></table></section>
<aside class="checkpoint"><h2>Round checkpoint</h2><p>Bibliographic discovery: {budget['bibliographic_discovery']} · Full-text acquisition: {budget['full_text_acquisition']} · Substantive review: {budget['substantive_review']}</p></aside>
</main></body></html>
"""


def _bibliography_csv(sources: list[dict]) -> str:
    columns = ["source_key", "citation", "source_type", "language", "scholarly_importance", "acquisition_priority", "availability", "review_extent", "reading_priority", "stable_links", "round_membership"]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    for source in sources:
        writer.writerow({
            "source_key": source["source_key"], "citation": _citation(source),
            "source_type": source.get("source_type") or "", "language": source.get("language") or "",
            "scholarly_importance": source.get("scholarly_importance", {}).get("level", ""),
            "acquisition_priority": source.get("acquisition_priority", ""), "availability": source.get("availability", ""),
            "review_extent": source.get("review_extent", ""), "reading_priority": source.get("reading_priority", ""),
            "stable_links": " | ".join(_public_links(source)),
            "round_membership": " | ".join(item.get("round_id", "") for item in source.get("round_membership", [])),
        })
    return buffer.getvalue()


def _contains_private_path(value: str) -> bool:
    return bool(FILE_URI.search(value) or POSIX_ABSOLUTE_PATH.search(value) or WINDOWS_ABSOLUTE_PATH.search(value))


def _safe_checkpoint_id(checkpoint_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", checkpoint_id):
        raise BundleValidationError("checkpoint_id is unsafe for an artifact filename")
    return checkpoint_id


def _write_staged(staging: Path, relative: Path, content: str) -> Path:
    path = staging / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _preflight_immutable(targets: dict[Path, str]) -> None:
    for path, content in targets.items():
        if path.exists() and path.read_text(encoding="utf-8") != content:
            raise FileExistsError(f"Refusing to replace immutable artifact: {path}")


def _publish_file(staged: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    shutil.copyfile(staged, temporary)
    os.replace(temporary, target)


def render_outputs(*, bundle_path: Path, source_path: Path, claim_path: Path, round_path: Path, output_root: Path) -> RenderedOutputs:
    """Validate one checkpoint and failure-atomically publish reader outputs."""
    errors = validate_bundle_files(Path(bundle_path), source_path=Path(source_path), claim_path=Path(claim_path), round_path=Path(round_path))
    if errors:
        raise BundleValidationError("; ".join(errors))
    bundle = _load_json(Path(bundle_path))
    checkpoint_id = _safe_checkpoint_id(bundle["checkpoint_id"])
    rounds_by_id = {item["round_id"]: item for item in _load_jsonl(Path(round_path))}
    if rounds_by_id[bundle["round_id"]].get("status") != "completed":
        raise BundleValidationError("Reader outputs require a completed round checkpoint")
    sources_by_key = {item["source_key"]: item for item in _load_jsonl(Path(source_path))}
    claims_by_id = {item["claim_id"]: item for item in _load_jsonl(Path(claim_path))}
    sources = [sources_by_key[key] for key in bundle["bibliography_selection"]]
    claims = [claims_by_id[key] for key in bundle["claim_ids"]]
    markdown = _round_markdown(bundle, sources, claims)
    synthesis = markdown.replace(f"Research Round {bundle['round_id']}", "Living Research Synthesis", 1)
    rendered_html = _presentation_html(bundle, sources, claims)
    csv_content = _bibliography_csv(sources)
    for label, content in (("round Markdown", markdown), ("synthesis Markdown", synthesis), ("bibliography CSV", csv_content)):
        if _contains_private_path(content):
            raise BundleValidationError(f"{label} contains a private local path")

    root = Path(output_root)
    round_markdown = root / "reports" / f"{bundle['round_id']}.md"
    round_html = root / "presentations" / "rounds" / f"{bundle['round_id']}.html"
    bibliography_csv = root / "exports" / "bibliography.csv"
    versioned_synthesis = root / "synthesis" / f"synthesis-{checkpoint_id}.md"
    current_synthesis = root / "synthesis" / "current-synthesis.md"
    versioned_html = root / "presentations" / "versions" / f"{checkpoint_id}.html"
    project_index_html = root / "presentations" / "index.html"
    _preflight_immutable({round_markdown: markdown, round_html: rendered_html, versioned_synthesis: synthesis, versioned_html: rendered_html})

    root.parent.mkdir(parents=True, exist_ok=True)
    content_by_relative = {
        Path("reports") / f"{bundle['round_id']}.md": markdown,
        Path("presentations/rounds") / f"{bundle['round_id']}.html": rendered_html,
        Path("exports/bibliography.csv"): csv_content,
        Path("synthesis") / f"synthesis-{checkpoint_id}.md": synthesis,
        Path("synthesis/current-synthesis.md"): synthesis,
        Path("presentations/versions") / f"{checkpoint_id}.html": rendered_html,
        Path("presentations/index.html"): rendered_html,
    }
    with tempfile.TemporaryDirectory(prefix=f".{root.name}.render-", dir=root.parent) as temp_dir:
        staging = Path(temp_dir)
        staged = {relative: _write_staged(staging, relative, content) for relative, content in content_by_relative.items()}
        publish_order = [
            Path("reports") / f"{bundle['round_id']}.md", Path("presentations/rounds") / f"{bundle['round_id']}.html",
            Path("synthesis") / f"synthesis-{checkpoint_id}.md", Path("presentations/versions") / f"{checkpoint_id}.html",
            Path("exports/bibliography.csv"), Path("synthesis/current-synthesis.md"), Path("presentations/index.html"),
        ]
        for relative in publish_order:
            _publish_file(staged[relative], root / relative)
    return RenderedOutputs(round_markdown, round_html, bibliography_csv, versioned_synthesis, project_index_html)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render research outputs from one validated round bundle.")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--claims", type=Path, required=True)
    parser.add_argument("--rounds", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    render_outputs(bundle_path=args.bundle, source_path=args.sources, claim_path=args.claims, round_path=args.rounds, output_root=args.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
