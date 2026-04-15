# Per-Service RISK- Template

Use this template for RISK- artifacts that catalog known gaps, technical debt, and risk signals within a single service.

**Naming convention:** `risk-{service}-known-gaps` (e.g., `risk-payments-known-gaps`, `risk-fulfillment-known-gaps`)

**When to use:** One per service. Generated at snorkel depth (thin, TODO/FIXME scan) and deepened at scuba depth (broader code scan).

**Signal sources:** TODO/FIXME/HACK/XXX comments, bare exception handlers, hardcoded URLs/credentials, disabled/skipped tests, missing error handling on HTTP/DB calls, deprecated API usage.

---

```yaml
---
id: "RISK-{SERVICE}-KNOWN-GAPS"
type: "risk"
title: "{Service} Known Risks, Gaps, and Backlog Candidates"
domain: "{DOMAIN}"
status: "draft"
last_verified: {DATE}
freshness_note: "scuba-depth risk scan from code signals"
freshness_triggers:
  - "{path/to/source/root}"
known_unknowns:
  - "Severity assessments are based on signal density, not production impact"
  - "Some TODOs may be resolved but not removed from code"
tags: ["risk-catalog"]
aliases: []
relates_to:
  - { type: "parent", target: "[[SYS-{SERVICE}]]" }
sources:
  - { ref: "{path/to/source/root}", type: "code" }
notes: ""
---
```

## Purpose

{What risks and gaps this catalog covers. One sentence on the service's overall risk posture based on signal density.}

## Key Facts

- {N} risk signals found across {M} files → `{source root}`
- Highest-density theme: {theme} ({N} signals) → `{primary file paths}`
- {Notable specific finding} → `{source}`

## Findings

| # | Location | Signal | Theme | Severity |
|---|----------|--------|-------|----------|
| 1 | `{file:line}` | `{TODO/FIXME/HACK text or description}` | {theme} | {low/medium/high} |
| 2 | `{file:line}` | `{signal}` | {theme} | {severity} |

Severity by density within theme: 10+ signals = high, 5-9 = medium, 1-4 = low.

## Themes

### {Theme Name} ({N} signals, {severity})

{2-3 sentence summary of what this theme covers and why it matters.}

**Signals:**
- `{file:line}` — {description}
- `{file:line}` — {description}

**Impact if unaddressed:** {What could go wrong. Be specific to this service's domain.}

{Repeat for each theme.}

## Recommended Actions

| Priority | Action | Theme | Effort |
|----------|--------|-------|--------|
| 1 | {specific action} | {theme} | {low/medium/high} |
| 2 | {specific action} | {theme} | {effort} |

## Related

- [[SYS-{SERVICE}]] -- parent system
