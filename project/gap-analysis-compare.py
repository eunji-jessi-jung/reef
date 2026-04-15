#!/usr/bin/env python3
"""
Compare a candidate extraction against a baseline.
Produces a markdown gap analysis report with the scoring template filled in.

Usage:
    python scripts/gap-analysis-compare.py candidate.json --baseline baseline.json --output gap-analysis-results.md

Both candidate.json and baseline.json are produced by gap-analysis-extract.py.
"""

import argparse
import json
import sys
from pathlib import Path


def pct(candidate_val, baseline_val):
    """Calculate candidate as % of baseline."""
    if baseline_val == 0:
        return 100.0 if candidate_val == 0 else float("inf")
    return round(candidate_val / baseline_val * 100, 1)


def score_label(pct_val):
    """Return a label for the coverage percentage."""
    if pct_val >= 90:
        return "Excellent"
    elif pct_val >= 80:
        return "Target Met"
    elif pct_val >= 60:
        return "Partial"
    elif pct_val >= 40:
        return "Weak"
    else:
        return "Gap"


def generate_report(candidate: dict, baseline: dict) -> str:
    meta = candidate["meta"]
    agg = candidate["aggregates"]
    struct = agg["structural"]

    b_agg = baseline["aggregates"]
    b_struct = b_agg["structural"]

    timestamp = meta["extracted_at"]
    stage = meta["reef_stage"]
    baseline_source = baseline["meta"]["source_dir"]
    baseline_total = b_agg["total_artifacts"]

    lines = []
    lines.append(f"# Gap Analysis Results — {timestamp}")
    lines.append("")
    lines.append(f"- **Reef stage**: {stage}")
    lines.append(f"- **Source**: `{meta['source_dir']}`")
    lines.append(f"- **Baseline**: `{baseline_source}` ({baseline_total} artifacts, extracted {baseline['meta']['extracted_at']})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === Dimension 1: Quantitative Coverage ===
    lines.append("## Dimension 1: Quantitative Coverage")
    lines.append("")
    total_pct = pct(agg["total_artifacts"], baseline_total)
    lines.append(f"**Overall: {agg['total_artifacts']} / {baseline_total} ({total_pct}%) — {score_label(total_pct)}**")
    lines.append("")
    lines.append("### By Type")
    lines.append("")
    lines.append("| Type | Baseline | Candidate | % | Status |")
    lines.append("|------|----------|-----------|---|--------|")
    all_types = sorted(set(list(b_agg["by_type"].keys()) + list(agg["by_type"].keys())))
    for typ in all_types:
        b = b_agg["by_type"].get(typ, 0)
        c = agg["by_type"].get(typ, 0)
        p = pct(c, b)
        lines.append(f"| {typ} | {b} | {c} | {p}% | {score_label(p)} |")
    lines.append("")

    lines.append("### By Domain")
    lines.append("")
    lines.append("| Domain | Baseline | Candidate | % | Status |")
    lines.append("|--------|----------|-----------|---|--------|")
    all_domains = sorted(set(list(b_agg["by_domain"].keys()) + list(agg["by_domain"].keys())))
    for dom in all_domains:
        b = b_agg["by_domain"].get(dom, 0)
        c = agg["by_domain"].get(dom, 0)
        p = pct(c, b)
        lines.append(f"| {dom} | {b} | {c} | {p}% | {score_label(p)} |")
    lines.append("")

    # === Dimension 2: Qualitative Depth (automated portion) ===
    lines.append("## Dimension 2: Qualitative Depth (Automated Metrics)")
    lines.append("")
    lines.append("| Metric | Baseline | Candidate | % | Status |")
    lines.append("|--------|----------|-----------|---|--------|")

    lines_pct = pct(agg["total_lines"], b_agg["total_lines"])
    lines.append(f"| Total content (lines) | {b_agg['total_lines']} | {agg['total_lines']} | {lines_pct}% | {score_label(lines_pct)} |")

    mermaid_pct = pct(agg["total_mermaid_diagrams"], b_agg["total_mermaid_diagrams"])
    lines.append(f"| Mermaid diagrams | {b_agg['total_mermaid_diagrams']} | {agg['total_mermaid_diagrams']} | {mermaid_pct}% | {score_label(mermaid_pct)} |")

    code_pct = pct(agg["total_code_blocks"], b_agg["total_code_blocks"])
    lines.append(f"| Code blocks | {b_agg['total_code_blocks']} | {agg['total_code_blocks']} | {code_pct}% | {score_label(code_pct)} |")

    lines.append(f"| Key Facts (candidate) | {b_agg.get('total_key_facts', 'N/A')} | {agg['total_key_facts']} | — | — |")
    lines.append(f"| Source-cited claims (→) | {b_agg.get('total_source_cited_claims', 'N/A')} | {agg['total_source_cited_claims']} | — | — |")
    lines.append("")

    # === Dimension 3: Structural Integrity ===
    lines.append("## Dimension 3: Structural Integrity")
    lines.append("")
    lines.append("| Metric | Baseline | Candidate | Status |")
    lines.append("|--------|----------|-----------|--------|")

    lines.append(f"| Valid frontmatter | {b_struct['valid_frontmatter_pct']}% | {struct['valid_frontmatter_pct']}% | {'Pass' if struct['valid_frontmatter_pct'] >= 99 else 'Fail'} |")

    edge_pct = pct(agg["avg_relates_to"], b_agg["avg_relates_to"])
    lines.append(f"| Avg relates_to edges | {b_agg['avg_relates_to']} | {agg['avg_relates_to']} | {score_label(edge_pct)} ({edge_pct}%) |")

    lines.append(f"| Orphans (no relates_to) | {b_struct.get('orphans_no_relates_to', '—')} | {struct['orphans_no_relates_to']} | — |")
    lines.append(f"| With known_unknowns | {b_struct['with_known_unknowns_pct']}% | {struct['with_known_unknowns_pct']}% | {'Better' if struct['with_known_unknowns_pct'] >= b_struct['with_known_unknowns_pct'] else 'Worse'} |")
    lines.append(f"| With sources | {b_struct['with_sources_pct']}% | {struct['with_sources_pct']}% | {'Pass' if struct['with_sources_pct'] >= 95 else 'Fail'} |")
    lines.append(f"| With freshness_note | {b_struct.get('with_freshness_note_pct', '—')}% | {struct['with_freshness_note_pct']}% | {'Pass' if struct['with_freshness_note_pct'] >= 95 else 'Needs work'} |")
    lines.append(f"| With freshness_triggers | {b_struct.get('with_freshness_triggers_pct', '—')}% | {struct['with_freshness_triggers_pct']}% | {'Pass' if struct['with_freshness_triggers_pct'] >= 95 else 'Needs work'} |")
    lines.append(f"| ID/filename match | {b_struct.get('id_filename_match', '—')}/{baseline_total} | {struct['id_filename_match']}/{agg['total_artifacts']} | {'Pass' if struct['id_filename_match'] == agg['total_artifacts'] else 'Fail'} |")

    if struct["id_filename_mismatches"]:
        lines.append("")
        lines.append("**ID/filename mismatches:**")
        for m in struct["id_filename_mismatches"]:
            lines.append(f"- `{m['id']}` -> `{m['filename']}` (expected `{m['expected']}`)")
    lines.append("")

    # === Type-level detail ===
    lines.append("## Type-Level Metrics")
    lines.append("")
    lines.append("| Type | Count | Avg Lines | Avg relates_to | Avg sources | Mermaid | Code Blocks | Key Facts |")
    lines.append("|------|-------|-----------|----------------|-------------|---------|-------------|-----------|")
    for typ in all_types:
        ta = agg["type_averages"].get(typ, {})
        if ta:
            lines.append(f"| {typ} | {ta['count']} | {ta['avg_lines']} | {ta['avg_relates_to']} | {ta['avg_sources']} | {ta['total_mermaid']} | {ta['total_code_blocks']} | {ta['total_key_facts']} |")
    lines.append("")

    # === Dimensions 4-7: Manual sections (templates) ===
    lines.append("## Dimension 4: Accuracy & Truthfulness")
    lines.append("")
    lines.append("_To be filled manually via spot-checking._")
    lines.append("")
    lines.append("| Metric | Result | Notes |")
    lines.append("|--------|--------|-------|")
    lines.append("| Spot-check accuracy (30 claims) | —/30 | |")
    lines.append("| Hallucination rate | —% | |")
    lines.append("| Baseline hallucination rate (control) | —% | |")
    lines.append("")

    lines.append("## Dimension 5: Practical Utility")
    lines.append("")
    lines.append("_To be filled manually per use case._")
    lines.append("")
    for uc, name in [("A", "Team/Org Documentation"), ("B", "Developer Agent"),
                     ("C", "PM Assistant"), ("D", "Operations/Agent Builder")]:
        lines.append(f"### Use Case {uc}: {name}")
        lines.append("")
        lines.append(f"| Metric | Baseline (1-5) | Candidate (1-5) | Notes |")
        lines.append(f"|--------|----------------|-----------------|-------|")
        for i in range(1, 6):
            lines.append(f"| 5{uc}.{i} | — | — | |")
        lines.append("")

    lines.append("## Dimension 6: Efficiency & ROI")
    lines.append("")
    lines.append("| Metric | Baseline | Candidate |")
    lines.append("|--------|----------|-----------|")
    lines.append(f"| Creation time | — | {stage} stage |")
    lines.append("| Human effort | — | — |")
    lines.append("| Domain expertise required | — | — |")
    lines.append("| Reproducibility | — | — |")
    lines.append("")

    lines.append("## Dimension 7: Unique Strengths & Gaps")
    lines.append("")
    lines.append("### Candidate-only artifacts (not in baseline)")
    lines.append("")
    lines.append("_To be filled after semantic matching._")
    lines.append("")
    lines.append("### Baseline-only artifacts (missing from candidate)")
    lines.append("")
    lines.append("_To be filled after semantic matching._")
    lines.append("")

    # === Summary Scorecard ===
    lines.append("---")
    lines.append("")
    lines.append("## Summary Scorecard")
    lines.append("")
    lines.append("| Dimension | Weight | Score | Status |")
    lines.append("|-----------|--------|-------|--------|")
    lines.append(f"| 1. Quantitative Coverage | 20% | {total_pct}% | {score_label(total_pct)} |")
    lines.append(f"| 2. Qualitative Depth | 25% | {lines_pct}% (content volume) | {score_label(lines_pct)} |")
    lines.append(f"| 3. Structural Integrity | 10% | {struct['valid_frontmatter_pct']}% (frontmatter) | {'Pass' if struct['valid_frontmatter_pct'] >= 99 else 'Fail'} |")
    lines.append("| 4. Accuracy & Truthfulness | 15% | — | _manual_ |")
    lines.append("| 5. Practical Utility | 20% | — | _manual_ |")
    lines.append("| 6. Efficiency & ROI | 5% | — | — |")
    lines.append("| 7. Unique Strengths | 5% | — | _manual_ |")
    lines.append(f"| **Automated estimate** | **55%** | **~{round((total_pct * 0.2 + lines_pct * 0.25 + min(struct['valid_frontmatter_pct'], 100) * 0.1) / 0.55, 1)}%** | — |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Next Actions")
    lines.append("")
    lines.append("_Based on the gaps identified above, recommend specific reef:deep targets or pipeline improvements._")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compare candidate extraction against baseline")
    parser.add_argument("candidate_json", help="Path to candidate extraction JSON")
    parser.add_argument("--baseline", "-b", required=True, help="Path to baseline extraction JSON (produced by gap-analysis-extract.py)")
    parser.add_argument("--output", "-o", help="Output markdown file")
    args = parser.parse_args()

    candidate = json.loads(Path(args.candidate_json).read_text())
    baseline = json.loads(Path(args.baseline).read_text())
    report = generate_report(candidate, baseline)

    if args.output:
        Path(args.output).write_text(report)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
