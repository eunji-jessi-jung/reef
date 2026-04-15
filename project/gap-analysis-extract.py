#!/usr/bin/env python3
"""
Extract quantitative metrics from a reef artifacts directory.
Outputs a JSON report that can be compared against a baseline.

Usage:
    python scripts/gap-analysis-extract.py /path/to/reef/artifacts
    python scripts/gap-analysis-extract.py /path/to/reef/artifacts --output report.json
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import yaml


def parse_frontmatter(filepath: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    text = filepath.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def count_content_features(filepath: Path) -> dict:
    """Count lines, mermaid blocks, code blocks, Key Facts, etc."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")
    line_count = len(lines)

    # Count mermaid diagrams
    mermaid_count = len(re.findall(r"```mermaid", text))

    # Count non-mermaid code blocks
    all_code_blocks = len(re.findall(r"```\w*", text))
    code_blocks = all_code_blocks - mermaid_count

    # Count Key Facts (reef-style: lines starting with "- " under "## Key Facts")
    key_facts = 0
    in_key_facts = False
    for line in lines:
        if re.match(r"^##\s+Key Facts", line):
            in_key_facts = True
            continue
        if in_key_facts:
            if re.match(r"^##\s+", line):  # next section
                in_key_facts = False
            elif re.match(r"^- .+", line):
                key_facts += 1

    # Check for ## Related section
    has_related = bool(re.search(r"^##\s+Related", text, re.MULTILINE))

    # Count verifiable claims with source arrows (reef pattern: "claim → source")
    source_cited_claims = len(re.findall(r"^- .+→.+$", text, re.MULTILINE))

    return {
        "lines": line_count,
        "mermaid_diagrams": mermaid_count,
        "code_blocks": code_blocks,
        "key_facts": key_facts,
        "source_cited_claims": source_cited_claims,
        "has_related_section": has_related,
        "size_bytes": filepath.stat().st_size,
    }


def extract_artifact(filepath: Path) -> dict:
    """Extract all metrics for a single artifact file."""
    fm = parse_frontmatter(filepath)
    content = count_content_features(filepath)

    relates_to = fm.get("relates_to", []) or []
    sources = fm.get("sources", []) or []
    known_unknowns = fm.get("known_unknowns", []) or []

    return {
        "filename": filepath.name,
        "id": fm.get("id", ""),
        "type": fm.get("type", ""),
        "title": fm.get("title", ""),
        "domain": fm.get("domain", ""),
        "status": fm.get("status", ""),
        "last_verified": str(fm.get("last_verified", "")),
        "has_freshness_note": bool(fm.get("freshness_note")),
        "has_freshness_triggers": bool(fm.get("freshness_triggers")),
        "relates_to_count": len(relates_to),
        "sources_count": len(sources),
        "known_unknowns_count": len(known_unknowns),
        **content,
    }


def compute_aggregates(artifacts: list[dict]) -> dict:
    """Compute aggregate statistics from artifact list."""
    total = len(artifacts)
    if total == 0:
        return {"error": "No artifacts found"}

    by_type = Counter(a["type"] for a in artifacts)
    by_domain = Counter(a["domain"] for a in artifacts)
    by_status = Counter(a["status"] for a in artifacts)

    # Type x Domain matrix
    type_domain = defaultdict(lambda: Counter())
    for a in artifacts:
        type_domain[a["type"]][a["domain"]] += 1

    # Averages by type
    type_metrics = defaultdict(lambda: {"count": 0, "lines": 0, "relates_to": 0,
                                         "sources": 0, "mermaid": 0, "code_blocks": 0,
                                         "key_facts": 0, "source_cited_claims": 0})
    for a in artifacts:
        t = type_metrics[a["type"]]
        t["count"] += 1
        t["lines"] += a["lines"]
        t["relates_to"] += a["relates_to_count"]
        t["sources"] += a["sources_count"]
        t["mermaid"] += a["mermaid_diagrams"]
        t["code_blocks"] += a["code_blocks"]
        t["key_facts"] += a["key_facts"]
        t["source_cited_claims"] += a["source_cited_claims"]

    type_averages = {}
    for typ, m in type_metrics.items():
        c = m["count"]
        type_averages[typ] = {
            "count": c,
            "avg_lines": round(m["lines"] / c, 1),
            "avg_relates_to": round(m["relates_to"] / c, 1),
            "avg_sources": round(m["sources"] / c, 1),
            "total_mermaid": m["mermaid"],
            "total_code_blocks": m["code_blocks"],
            "total_key_facts": m["key_facts"],
            "total_source_cited_claims": m["source_cited_claims"],
        }

    # Structural checks
    valid_frontmatter = sum(1 for a in artifacts if a["id"])
    with_known_unknowns = sum(1 for a in artifacts if a["known_unknowns_count"] > 0)
    with_sources = sum(1 for a in artifacts if a["sources_count"] > 0)
    with_freshness_note = sum(1 for a in artifacts if a["has_freshness_note"])
    with_freshness_triggers = sum(1 for a in artifacts if a["has_freshness_triggers"])
    orphans = sum(1 for a in artifacts if a["relates_to_count"] == 0)

    # ID/filename consistency
    id_filename_match = 0
    id_filename_mismatch = []
    for a in artifacts:
        if a["id"]:
            expected_filename = a["id"].lower().replace("_", "-") + ".md"
            if a["filename"] == expected_filename:
                id_filename_match += 1
            else:
                id_filename_mismatch.append({"id": a["id"], "filename": a["filename"],
                                              "expected": expected_filename})

    return {
        "total_artifacts": total,
        "total_lines": sum(a["lines"] for a in artifacts),
        "total_size_kb": round(sum(a["size_bytes"] for a in artifacts) / 1024, 1),
        "total_mermaid_diagrams": sum(a["mermaid_diagrams"] for a in artifacts),
        "total_code_blocks": sum(a["code_blocks"] for a in artifacts),
        "total_key_facts": sum(a["key_facts"] for a in artifacts),
        "total_source_cited_claims": sum(a["source_cited_claims"] for a in artifacts),
        "total_relates_to_edges": sum(a["relates_to_count"] for a in artifacts),
        "avg_relates_to": round(sum(a["relates_to_count"] for a in artifacts) / total, 2),
        "by_type": dict(by_type),
        "by_domain": dict(by_domain),
        "by_status": dict(by_status),
        "type_averages": type_averages,
        "structural": {
            "valid_frontmatter": valid_frontmatter,
            "valid_frontmatter_pct": round(valid_frontmatter / total * 100, 1),
            "with_known_unknowns": with_known_unknowns,
            "with_known_unknowns_pct": round(with_known_unknowns / total * 100, 1),
            "with_sources": with_sources,
            "with_sources_pct": round(with_sources / total * 100, 1),
            "with_freshness_note": with_freshness_note,
            "with_freshness_note_pct": round(with_freshness_note / total * 100, 1),
            "with_freshness_triggers": with_freshness_triggers,
            "with_freshness_triggers_pct": round(with_freshness_triggers / total * 100, 1),
            "orphans_no_relates_to": orphans,
            "id_filename_match": id_filename_match,
            "id_filename_mismatches": id_filename_mismatch[:10],  # cap at 10
        },
        "topic_index": [{"id": a["id"], "title": a["title"], "type": a["type"],
                         "domain": a["domain"]} for a in artifacts],
    }


def main():
    parser = argparse.ArgumentParser(description="Extract gap analysis metrics from artifacts directory")
    parser.add_argument("artifacts_dir", help="Path to artifacts/ directory")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    parser.add_argument("--stage", "-s", default="unknown",
                        help="Current Reef pipeline stage (e.g., snorkel, scuba, deep)")
    args = parser.parse_args()

    artifacts_path = Path(args.artifacts_dir)
    if not artifacts_path.is_dir():
        print(f"Error: {artifacts_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Find all .md files recursively, skip non-artifact files
    md_files = sorted(artifacts_path.rglob("*.md"))
    if not md_files:
        print(f"Error: No .md files found in {artifacts_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {len(md_files)} files in {artifacts_path}...", file=sys.stderr)

    artifacts = []
    for f in md_files:
        artifacts.append(extract_artifact(f))

    aggregates = compute_aggregates(artifacts)

    report = {
        "meta": {
            "extracted_at": datetime.now().isoformat(timespec="minutes"),
            "source_dir": str(artifacts_path),
            "reef_stage": args.stage,
            "file_count": len(md_files),
        },
        "aggregates": aggregates,
        "artifacts": artifacts,
    }

    output_json = json.dumps(report, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(output_json)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
