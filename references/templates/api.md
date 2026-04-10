---
id: "{ID}"
type: "api"
title: "{TITLE}"
domain: "{DOMAIN}"
status: "draft"
last_verified: {DATE}
freshness_note: "{FRESHNESS_NOTE}"
freshness_triggers: []
known_unknowns: []
tags: []
aliases: []
relates_to: []
sources: []
notes: ""
---

## Overview

{One to two paragraphs interpreting this API surface: what capabilities it exposes, who consumes it, and what design philosophy it follows. Do not restate the raw spec -- explain what the API means for its consumers.}

## Key Facts

- {Verifiable claim about the API} → `{source_ref}`

## Source of Truth

The raw API specification lives at `{path_to_spec_in_sources_raw}`. This artifact interprets that spec; the raw file is the authoritative reference for exact endpoint signatures, request/response schemas, and status codes.

## Resource Map

### {Resource Group}

| Method | Path | Purpose |
|--------|------|---------|
| {GET/POST/...} | {/path} | {What this endpoint does and when you would call it} |

### {Resource Group}

{Repeat for each logical grouping of endpoints.}

## Related

- [[{ARTIFACT_ID}]] -- {relationship description}
