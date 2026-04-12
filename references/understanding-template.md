# Understanding Template

Discovery questions organized by diving level. Each level maps to a skill and builds on the context from the level above.

| Level | Skill | Human input needed? | What it produces |
|-------|-------|---------------------|------------------|
| Snorkel | `/reef:snorkel` | No — code reading only | Draft artifacts with honest gaps |
| Scuba | `/reef:scuba` | Phase 1: no. Phase 2: yes — guided Q&A | Advanced artifacts (API patterns, schema depth, lifecycles, auth boundaries, dependency maps, entity comparisons) + Socratic exploration |
| Deep | `/reef:deep` | Yes — exhaustive tracing + user framing | Dense, line-cited artifacts for critical areas |

Questions are ordered intentionally — each builds context for the next.

---

## Snorkel — What is here and what does it do?

All answerable from code. No human input required. This is what a newly hired engineer or PM would need to learn in their first week.

### S1. System boundaries

Identify what each repo is and how repos relate to each other.

- What is this repo? What role does it play? (API server, frontend, worker, auth service, gateway, etc.)
- **Within-service**: How do the repos in this service divide responsibilities? (e.g., one is the domain API, one is auth, one is the admin UI, one is the annotator UI)
- **Cross-service**: What external systems, services, or APIs does this service depend on or talk to?
- What does the deployment topology look like? (docker-compose files, Helm charts, Kubernetes configs)

**Artifact output:** SYS- artifact per service.

### S2. Apps and high-level features

Map the applications and extract what they do in user-facing terms.

- What backend and frontend applications exist?
- What are the high-level features each app provides? (e.g., "manages product listings," "processes transactions," "handles image uploads")
- What user roles interact with each app? (if identifiable from route guards, role checks, or UI structure)

**Artifact output:** Update SYS- artifacts with feature inventory.

### S3. Data model

Extract and describe the data layer. Semi-automatic via `/reef:source`.

- What database(s) does each repo use? (PostgreSQL, MongoDB, Redis, etc.)
- What ORM or database client is used? (SQLAlchemy, Beanie, GORM, Prisma, etc.)
- Extract the ERD — tables/collections, fields, types, primary keys, foreign keys, relationships.
- Describe each table/collection: what it represents, what its key fields mean.
- How are migrations managed? What tool is used?

**Artifact output:** SCH- artifact per service. ERD diagram saved to `sources/raw/`.

### S4. API surface

Extract and describe the API layer. Semi-automatic via `/reef:source`.

- What API endpoints does each service expose?
- What are the main resource groups and their CRUD operations?
- How are routes organized? (versioning, grouping, middleware)
- What are the request/response shapes for the key endpoints?

**Artifact output:** API- artifact per service. OpenAPI spec saved to `sources/raw/`.

### S5. Service roles and responsibilities

Synthesize S1-S4 into a clear picture of what each service does and owns.

- What is this service's primary responsibility in one sentence?
- What domain concepts does it own? (i.e., what data and behavior belong to this service and no other)
- What does it explicitly NOT own? (boundaries with adjacent services)

**Artifact output:** Update SYS- artifacts with roles and responsibilities.

### S6. Runtime architecture

Map how the service runs at runtime — topology, storage, events, composition.

- What processes run at runtime? (API server, worker, subscriber, scheduler, etc.)
- What databases does each process connect to? Are they shared or separate?
- What event/async systems exist? (message queues, pub/sub, Celery workers, etc.)
- What are the synchronous vs asynchronous execution paths?
- How is the service composed locally? (docker-compose services, startup scripts)

**Artifact output:** PROC- artifact for runtime architecture per service.

### S7. AuthN/AuthZ model

Define how authentication and authorization work in each service.

- How does authentication work? (JWT, session, OAuth2, API keys, service accounts)
- What identity provider is used? (Keycloak, Auth0, custom, etc.)
- How is authorization enforced? (RBAC, middleware guards, policy engine)
- What roles and permissions exist? Where are they defined?
- How do tokens flow between frontend and backend?

**Artifact output:** PROC- or DEC- artifact for auth per service.

### S8. Glossary and disambiguation

Collect terms, acronyms, and tribal language encountered during S1-S7.

- What acronyms appear in the codebase? What do they stand for?
- What terms have domain-specific meanings that differ from common usage?
- What terms are ambiguous across services? (same word, different meaning)
- What naming conventions are used? (for endpoints, tables, config keys, etc.)

**Artifact output:** GLOSSARY- artifact per service.

---

## Scuba — How does it behave and connect?

Requires domain knowledge from the user via guided Q&A. Code can partially answer these, but the "why" and "what matters" come from the user.

### C1. Entity lifecycle states and transitions

For each core entity identified in S3:

- What are the possible states/statuses?
- What triggers each transition?
- Are transitions enforced in code or by convention?
- What side effects occur on transition? (notifications, events, downstream updates)
- What transitions are irreversible?

**Artifact output:** PROC- artifact per core entity lifecycle.

### C2. Critical workflows end-to-end

Trace the key user-facing and system-to-system workflows.

- What are the critical workflows? (e.g., "user completes checkout," "new order is processed," "file upload finishes")
- For each: what is the step-by-step flow from trigger to completion?
- Where can each workflow fail? What happens when it does?
- What retry or recovery mechanisms exist?

**Artifact output:** PROC- artifact per critical workflow.

### C3. Cross-service data flows and contracts

Requires service groupings from init.

- What data flows between services? In what format and transport? (REST, events, shared DB, file drops)
- What contracts exist at each boundary? Formal (API specs, proto files) or informal (convention)?
- Where do services share entities, schemas, or database tables?
- What happens when a dependency is down?

**Artifact output:** CON- artifact per service pair boundary.

### C4. Error handling and failure modes

- Where does error handling matter most?
- What are the known failure modes? (timeout, data inconsistency, partial writes)
- What monitoring or alerting exists?
- What are the operational runbooks or incident patterns?

**Artifact output:** RISK- artifact per service or shared risk.

### C5. Decisions and constraints

- What were the significant architectural decisions? What drove them?
- What constraints shaped the design? (regulatory, legacy, team size, timeline)
- What trade-offs were made? What was explicitly deferred?

**Artifact output:** DEC- artifact per significant decision.

### C6. Cross-service entity comparison

For entities that share names across services (identified by glossary disambiguation flags):

- What does `{entity}` mean in service A vs service B?
- Are the field definitions compatible? (same types, same semantics)
- Is there a canonical definition, or do both services own their own meaning?
- Where do these definitions need to align? (API boundaries, shared databases, event payloads)
- What happens when they drift apart?

Phase 1 auto-detects these from glossary disambiguation entries and generates draft comparison tables. Phase 2 confirms with the user.

**Artifact output:** CON- artifact per entity comparison.

### C7. Authorization model depth

For services with RBAC or complex authorization (identified by S7 findings):

- What are the permission primitives? (resource types, actions, roles, permissions)
- How are roles composed from permissions?
- Where is authorization enforced? (API layer, service layer, database layer)
- What is the token lifecycle? (issuance, refresh, revocation)
- Are there multiple auth paths coexisting? (legacy vs new, local vs external)

Phase 1 auto-detects auth middleware, RBAC decorators, and token validation from code. Phase 2 explores the "why" — design choices, migration plans, edge cases.

**Artifact output:** PROC- artifact deepening the auth boundary, or DEC- artifact for auth design choices.

### C8. Repeated concept taxonomy

For terms or concepts that appear frequently across a service's codebase:

- What are the different kinds of `{concept}`? (e.g., types of flows in a pipeline service)
- Is there a formal taxonomy, or is the naming ad hoc?
- What are the lifecycle stages of a `{concept}`?
- How do instances relate to each other? (composition, dependency, ordering)

Phase 1 identifies high-frequency terms by scanning directory structures and code patterns. Phase 2 asks the user to confirm and refine the taxonomy.

**Artifact output:** PROC- artifact documenting the taxonomy, or GLOSSARY- extension.

### C9. Business logic and domain terms

For terms that appear to carry business semantics beyond their technical implementation:

- What does `{term}` mean to the business? (not just what the code does)
- Where did this term originate? (domain expert, regulatory requirement, legacy system)
- Is the code implementation faithful to the business meaning?
- Are there business rules that the code does not enforce? (convention, manual process, future work)

Phase 1 surfaces candidate terms by finding names that don't match standard technical vocabulary. Phase 2 confirms with the user — only they know what's business-meaningful vs incidental naming.

**Artifact output:** GLOSSARY- extension or PROC- for business rules.

### C10. Version boundaries and migration

For services with multiple API versions or service layers detected:

- What prompted each version boundary? (breaking change, new feature, team split)
- What is the migration plan? (deprecation timeline, client migration)
- Are old versions deprecated or still actively used?
- What clients are on which version?
- What would break if an old version were removed?

Phase 1 detects version boundaries from directory structure (v1/, v2/, v3/) and route definitions. Phase 2 asks the user for the migration story.

**Artifact output:** DEC- artifact per version boundary decision.

---

## Deep — Why is it this way?

Exhaustive, line-by-line investigation of critical areas. The user directs where to go deep. 5+ Key Facts per artifact with precise source citations.

### D1. Critical path tracing

- Trace the complete execution path for a critical operation, function by function.
- Map every module that materially affects runtime behavior.
- Identify implicit dependencies, side effects, and edge cases.
- Document exact line citations for every claim.

### D2. Technical debt and risk

- What technical debt is acknowledged? Where is it documented vs. only known verbally?
- What would break if the primary maintainer left?
- What knowledge exists only in someone's head?
- What parts of the system are fragile, under-tested, or poorly understood?

### D3. Pattern analysis

- What design patterns recur across the codebase? Are they consistent?
- Where do patterns break or diverge? Why?
- What anti-patterns exist? Are they intentional trade-offs or accidents?

---

## Adaptation Rules

These rules modify the question set based on what the structural scan discovers:

- **No API endpoints found:** Skip S4. The repo may be a library, CLI tool, or worker.
- **No database found:** Skip S3. The service may be stateless or use external storage via another service.
- **Single-source reef:** Skip C3 (cross-service contracts). Within-service questions in S1 simplify to just external dependencies.
- **No event/async system detected:** Simplify S6 — skip async execution paths.
- **Simple or single-purpose service:** Compress S1-S4. Fewer questions needed when there are only a few files.
- **No status/state fields found on entities:** Skip C1 lifecycle detection in scuba Phase 1. Note in briefing.
- **Single-service reef:** Skip C6 (entity comparison) and dependency heat map. Simplify to within-service patterns only.
- **No frontend repos in sources:** Skip FE/BE contract detection in scuba Phase 1.
- **No RBAC primitives found:** Skip C7 depth exploration. Note auth as a gap in briefing.
- **No version boundaries detected:** Skip C10. The service has a single API version.
- **Always:** Skip questions already answered by existing artifacts. Do not re-ask what is already known.

---

## Triggerable Actions

Some questions should trigger automated extraction rather than manual investigation:

- **S3 (Data model) and S4 (API surface):** Trigger `/reef:source` to extract OpenAPI specs and ERD diagrams using the tiered protocol. During init, this runs in parallel with snorkel.
- **S6 (Runtime architecture):** Read docker-compose files, Helm charts, and startup configs directly.
- **S1 (System boundaries):** Read CLAUDE.md and README.md first — richest signal for service identity and boundaries.
