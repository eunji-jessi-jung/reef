# Scuba Phase 1 Sub-Steps (3.1–3.16)

Detailed instructions for each Phase 1 sub-step. Referenced by scuba SKILL.md Step 3. All artifacts produced are `status: "draft"`.

---

## 3.1 — API pattern analysis

For each service with an extracted OpenAPI spec in `sources/apis/{service}/{sub}/openapi.json`:

1. Read the full spec.
2. Analyze and document:
   - **Surface profile**: path count, operation count, method split (GET/POST/PUT/PATCH/DELETE)
   - **Auth posture**: count operations with vs without security requirements. "All N operations auth-gated" or "M of N operations have no auth requirement"
   - **Non-CRUD action patterns**: scan for `:verb` suffix on path segments (e.g., `:finalize`, `:assign`, `:clone`). List them. Note: "these are workflow transitions, not plain resource mutations"
   - **Batch operations**: scan for `batch` or `Batch` in paths or operationIds
   - **Pagination convention**: scan for `page`/`page_size`/`limit`/`offset`/`cursor` on GET list endpoints
   - **Error code patterns**: scan response schemas for common error codes
   - **Contract limits**: what OpenAPI does NOT encode — business invariants, side effects, cross-entity invariants, idempotency semantics
3. **Output:** Write an API- artifact per service/sub as a "delta layer on top of OpenAPI" — not a duplication of endpoint tables, but agent-relevant interpretation. Include a "How Agents Should Use This" section. Set `freshness_note: "scuba-depth API pattern analysis"`.
4. **Worked example (REQUIRED):** Every API- artifact must include a `### Worked Example` subsection with one concrete JSON request/response pair for the most representative or complex endpoint. Show realistic-looking data, not placeholder values.

## 3.2 — Comprehensive schema documentation

For each service with an extracted ERD in `sources/schemas/{service}/{sub}/schema.md`:

1. Read the full schema.
2. Document:
   - **Tech stack**: explicitly state the database and ORM/ODM
   - **For RDB schemas**: full field tables with columns for Field, Type, Nullable, PK/FK, Index, Notes. Mermaid ERD diagram showing tables and FK relationships.
   - **For document stores (MongoDB)**: document nesting structure, embedded vs referenced fields, index strategies. Mermaid diagram showing document relationships.
   - **Entity descriptions**: what each table/collection represents, not just its fields
   - **Relationship cardinalities**: one-to-one, one-to-many, many-to-many with join table names
3. **Output:** Write or update SCH- artifacts per service/sub. Set `freshness_note: "scuba-depth schema documentation"`.

**Quality mandates:**
- Every SCH- **must** include a Mermaid `erDiagram` (RDB) or `classDiagram` (document store). No exceptions. Max 15 entities per diagram; split if larger.
- Every SCH- **must** include a `### Worked Examples` subsection with: (a) at least one representative join query or access pattern using actual table/field names, and (b) an enum value table for every status, type, purpose, or category field. If exact enum values cannot be determined from code, add them to `known_unknowns` rather than guessing.
- For document stores: additionally document embedded vs referenced in a dedicated subsection.

## 3.3 — Entity definition and lifecycle artifacts

Generate a PROC- artifact for every **Tier 1** entity listed in the manifest. **Do not skip Tier 1 entities.**

Only Tier 1 entities (those with status/state fields, complex business logic, or aggregate relationships) get their own PROC- artifact. Tier 2 entities are documented within their parent's artifact under a "Related Entities" subsection. Tier 3 entities (join tables, lookups, views) are skipped entirely.

**Multi-app deduplication:** When a service has parallel sub-apps with near-identical schemas (e.g., regional or product-line variants), write lifecycle artifacts at the SERVICE level (e.g., `PROC-PAYMENTS-ORDER-LIFECYCLE`), not per-app. Note app-specific divergences inline. Separate comparison artifacts handle the detailed diff.

**Naming:** `PROC-{SERVICE}-{ENTITY}-LIFECYCLE` (e.g., `PROC-PAYMENTS-ORDER-LIFECYCLE`).

**Template:** Follow `references/templates/process-entity-lifecycle.md` exactly.

For each Tier 1 entity:

1. **Read the source code** — find the model/schema definition file. Read fields, relationships, validators, business logic.
2. **Write the PROC- artifact** following the template:
   - **Fields table**: focus on business-meaningful fields, not a raw dump
   - **Relationships**: which other entities this connects to, with cardinality. Mention Tier 2 child entities here.
   - **Creation path**: how instances come into existence (API endpoint, background job, migration)
   - **States**: if the entity has a status/state field, include a Mermaid `stateDiagram-v2` showing all states and transitions. If no status field, document the implicit lifecycle (created → used → archived/deleted).
   - **Agent Guidance section (REQUIRED)**: when to consult this artifact, common pitfalls, related artifacts to read together

**Worked examples mandate:** Every entity lifecycle PROC- **must** include a `### Worked Examples` subsection with: (a) at least one representative query showing how to access this entity in context (joining to parent/child, filtering by status), and (b) an enum value table for every status, type, purpose, or category field. Use actual field names from the Fields table. If exact enum values cannot be determined from code, add them to `known_unknowns`.

**Entity completeness check:** After generating all entity PROC- for a service, compare against the manifest's Tier 1 list. If any Tier 1 entity was skipped, go back and generate it.

## 3.4 — Authentication and authorization patterns

For each service with auth-related code (JWT validation, RBAC decorators, OAuth config, API keys, middleware):

1. Trace the auth flow: where credentials are validated, what claims are extracted, how permissions are checked.
2. Document: auth mechanism, identity provider, enforcement points, permission model.
3. **Output:** PROC- artifact per service's auth pattern. Set `freshness_note: "scuba-depth auth analysis"`.

## 3.5 — Frontend-backend contracts (if applicable)

If any source repo contains frontend code (React, Vue, Angular, etc.) alongside or connected to backend services:

1. Trace API calls from frontend to backend.
2. Document: which endpoints the frontend uses, data shapes expected, auth token handling.
3. **Output:** CON- artifact for the frontend-backend boundary.

Skip if no frontend code exists in the reef sources.

## 3.6 — Error handling patterns

For each service:

1. Scan for: global exception handlers, error middleware, retry decorators, circuit breakers, dead-letter queues.
2. Document: what errors are caught vs propagated, retry semantics, alerting hooks.
3. **Output:** PROC- artifact per service's error handling approach. Set `freshness_note: "scuba-depth error handling analysis"`.

## 3.7 — Service pair contracts

Generate a CON- artifact for every pair of services. N services = N×(N-1)/2 contracts.

**Template:** Follow `references/templates/contract-service-pair.md` exactly.

For each pair:

1. Scan both services' code for references to the other (HTTP client calls, shared schemas, event publishing/consuming, database sharing).
2. If integration detected: document endpoints called, auth model, data shapes, failure behavior. Include a **Mermaid `sequenceDiagram`** for the primary call flow. Add an `## Impact Analysis` subsection documenting what breaks if either service changes its API.
3. If no integration detected: use the "No Integration Detected" template section. This confirms architectural separation.

**Completeness check:** After all contracts are written, count them. Must have exactly N×(N-1)/2 CON- artifacts.

After all pairs, add a summary heat map table to the briefing showing coupling ratings.

## 3.8 — Cross-service entity comparison

Check GLOSSARY- artifacts for terms used in multiple services:

1. For each term that appears in SCH- artifacts from different services, pull field lists from both and generate a side-by-side comparison table.
2. Flag semantic mismatches: same-name fields with different types, different storage, different lifecycle semantics.
3. **Output:** CON- artifact per entity comparison with field-level comparison table, high-risk ambiguities, and canonical writing rules.

Skip for single-service reefs.

## 3.9 — Pattern and mechanism deepening

For each named pattern or domain-specific mechanism found in snorkel artifacts' Key Facts or Core Concepts:

1. Read the source code to understand the pattern at a conceptual level.
2. Document: what the pattern is, which entities/services use it, why it exists, what it enables, how it differs from the standard approach.
3. **Output:** PROC- or DEC- artifact per pattern/mechanism. Set `freshness_note: "scuba-depth pattern analysis"`.
   - **Note:** If you notice the same design choice appearing across multiple entities or services — two different approaches to the same problem, a shared concept with divergent implementations, a recurring architectural convention — flag it as a **PAT- candidate** in the manifest. Do NOT create PAT- artifacts in Phase 1. PAT- artifacts require understanding *why* the pattern exists, not just *that* it exists. They are created in Phase 2 or deep-dive, where the user can confirm the design intent.
4. **Do not go deep.** If investigating requires tracing more than 2-3 source files, stop and flag for `/reef:deep`. Scuba = "what and why" (1-3 files). Deep = "show me every line" (5+ files).

## 3.10 — Per-service RISK- artifacts

For each service in the manifest's RISK- plan:

1. Scan the source code for risk signals:
   - TODO/FIXME/HACK/XXX comments
   - Bare exception handlers (`except:` or `except Exception:` with no specific handling)
   - Hardcoded URLs/credentials
   - Missing error handling on HTTP/DB calls
   - Disabled/skipped tests
   - Deprecated API usage
2. Group findings by theme: data integrity, auth gaps, error handling, tech debt, missing validation, operational risk.
3. Severity by density: 10+ signals = high, 5-9 = medium, 1-4 = low.
4. **Output:** RISK- artifact per service. Template: `references/templates/risk-service.md`.

If snorkel already created a RISK- with 5+ findings, update instead of creating new.

## 3.11 — DEC- from observable patterns

For each planned DEC- in the manifest:

1. Read the relevant source code.
2. Document using ADR format:
   - **Context:** What problem prompted this choice. Cite code evidence.
   - **Decision:** What was chosen. Be specific.
   - **Consequences:** Observable in code — positive and negative.
   - **Rationale:** If determinable from code comments/commits/README. Otherwise: `known_unknowns: ["Rationale not available from code alone"]`.
3. Common auto-detectable: database choice, auth provider, API framework, monorepo structure, sync vs async, soft vs hard delete, versioning strategy.
4. **Output:** DEC- artifact. Set `freshness_note: "scuba-depth decision record from code observation"`.

## 3.12 — Per-service GLOSSARY- artifacts

For each service missing a per-service GLOSSARY-{SERVICE}:

1. Extract domain terms from all existing artifacts for that service (SYS-, SCH-, API-, PROC-).
2. Focus on: entity names, status/state values, acronyms (do NOT guess expansions — flag unknown), domain-specific field names.
3. Cross-reference with unified GLOSSARY-. Add disambiguation rows for multi-service terms.
4. **Output:** GLOSSARY-{SERVICE} artifact. Template: `references/templates/glossary-service.md`.
5. If all per-service glossaries are generated, also generate **GLOSSARY-SOURCE-INDEX** mapping each term to its defining code location across all services.

## 3.13 — PROC- flow catalogs

For each service with pipeline/orchestration/job systems in the manifest:

1. Enumerate all flows: Prefect `@flow`/`@task`, Celery `@app.task`, Airflow DAGs, background job classes, status progressions.
2. For each flow: trigger, processing steps, terminal states, error/retry behavior.
3. **If `sources/infra/{service}/storage.md` exists:** Cross-reference flows with storage path patterns. Document which flows read from / write to which cloud storage paths. This is often the primary data contract for pipeline services — the path convention defines the data model more than any database schema.
4. **If `sources/infra/{service}/queues.md` exists:** Cross-reference flows with queue/task definitions. Document which flows publish to / consume from which queues.
5. Include a **Mermaid `graph` diagram** showing flow dependencies, annotated with storage I/O where applicable.
6. **Output:** PROC-{SERVICE}-FLOW-CATALOG artifact. Template: `references/templates/process-flow-catalog.md`.

Skip for services with no pipeline/orchestration patterns.

## 3.13b — Infrastructure-driven PROC- and SCH- artifacts

For services where `sources/infra/{service}/storage.md` exists and the service has **fewer than 5 Tier 1 entities** (i.e., the traditional schema extraction was thin):

1. **Storage path conventions as data schema:** If the storage.md reveals structured path patterns with meaningful segments (e.g., `{project_id}/{dataset_id}/{split}/{filename}`), these path segments ARE the data model for this service. Write a SCH- artifact documenting the storage schema: path segments, their types/enums, naming conventions, and the implicit entity hierarchy.

2. **Data flow PROC- artifacts:** If storage patterns show data moving between buckets or path prefixes (input → processing → output), write PROC- artifacts for each major data flow. Cross-reference with flow catalog entries.

3. **Configuration surface as operational knowledge:** If `sources/infra/{service}/runtime.md` reveals a complex env var surface (10+ variables), write a PROC- operational artifact documenting the configuration model — what each group of variables controls, which are required for different environments, common misconfiguration patterns visible in the code.

This sub-step exists because pipeline/orchestration services are systematically under-documented by the traditional API+ERD extraction path. Their complexity lives in storage conventions, flow composition, and configuration — not in database tables and REST endpoints.

## 3.14 — PROC- multi-app comparison pairs

For services where the same domain concept has parallel implementations across sub-apps:

1. Detect: mirrored directory structures, shared base classes with overrides, same entity names with different fields.
2. Document: what is shared, what differs, why it differs (if determinable).
3. **Output:** PROC-{SERVICE}-{CONCEPT}-{APP-A}-VS-{APP-B} artifact with side-by-side field comparison tables.

Skip for services with only one app.

## 3.15 — SCH- per-collection (document stores)

For MongoDB/document-store services with 3+ collections:

1. For each collection, read the model/document class definition.
2. Document: fields table (name, type, required, indexed, meaning), embedded vs referenced, indexes (compound, unique, TTL, text), Mermaid diagram of nesting structure.
3. **Output:** SCH-{SERVICE}-COLLECTION-{COLLECTION} artifact.

Complements unified SCH- with per-collection depth.

## 3.16 — SCH- field lineage

For core entities with complex data origins (ingestion, ETL, computed fields, cross-service sync):

1. Trace each non-trivial field's origin:
   - **API input:** from request payload
   - **External system:** from third-party API, imported files, webhooks
   - **Computed:** calculated from other fields (document logic)
   - **Copied:** from another entity (document source and mapping)
   - **System-generated:** timestamps, auto-increment, hashes
2. Document as a lineage table: Field | Origin | Transform | Code Path
3. Include a **Mermaid `flowchart`** showing data flow from origin to entity fields.
4. **Output:** SCH-{SERVICE}-FIELD-LINEAGE-{ENTITY-GROUP} artifact.

Skip for simple CRUD entities where fields map 1:1 to API inputs.
