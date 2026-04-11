# Final QA Plan — Pre-Launch

Goal: Validate that reef works end-to-end for a complete stranger on a fresh device with unfamiliar codebases from unrelated domains.

---

## Setup

- **Device:** Different machine from development (no cached state, no muscle memory)
- **Install:** Fresh plugin install from marketplace (`/plugin marketplace add eunji-jessi-jung/reef`)
- **No prior context:** Do not read skill files or reference docs beforehand. Experience the tool as a new user.

---

## Round 1 — Single Service (Saleor)

**Repo:** [saleor/saleor](https://github.com/saleor/saleor) — headless ecommerce, Django + GraphQL + PostgreSQL
**Purpose:** Validate basics work on a simple, single-service codebase.

```bash
git clone https://github.com/saleor/saleor.git
```

### Checklist

- [ ] `/reef:init` completes without errors
  - [ ] Welcome block displays correctly (ASCII art, cost estimate, scope line)
  - [ ] 3 questions are asked and feel natural
  - [ ] Service grouping makes sense for a single-repo project
  - [ ] Discovery plan is shown with accurate time/token estimate
  - [ ] Snorkel + source run in parallel without conflicts
- [ ] Snorkel produces 5-10 artifacts
  - [ ] SYS- artifact captures what Saleor does
  - [ ] SCH- artifact has Mermaid ERD (products, orders, payments, etc.)
  - [ ] GLOSSARY- has ecommerce terms, not medical terms
  - [ ] No empty or stub-only artifacts
- [ ] Source extraction works
  - [ ] GraphQL schema detected (not just REST — Saleor uses Graphene)
  - [ ] ERD extraction finds Django ORM models
  - [ ] Report distinguishes live-truth vs fallback tiers
- [ ] Health report renders correctly (Unicode box-drawing)
- [ ] `/reef:obsidian` opens the reef (or gives clear instructions)
- [ ] Artifacts are domain-correct — no hallucinated services, no wrong entity names

### What could go wrong

- GraphQL (Graphene) is not in the API framework detection table — source may fall back to code reading
- Saleor has plugins, webhooks, and payment gateways — snorkel may miss these as architectural patterns
- Single-service means CON- artifacts are skipped — verify this is handled gracefully

---

## Round 2 — Multi-Service (Plane)

**Repo:** [makeplane/plane](https://github.com/makeplane/plane) — project management, Django + Next.js + PostgreSQL + Celery + RabbitMQ, 13 docker-compose services
**Purpose:** Validate multi-service detection, mixed-language handling, and service contract generation.

```bash
git clone https://github.com/makeplane/plane.git
```

### Checklist

- [ ] `/reef:init` detects the monorepo structure correctly
  - [ ] Sub-apps (api, web, admin, space, live, proxy) are grouped under one service or logically split
  - [ ] Docker-compose services are recognized for runtime architecture
  - [ ] Service grouping confirmation table makes sense
- [ ] Snorkel produces artifacts for multiple components
  - [ ] SYS- covers the overall system and/or individual services
  - [ ] SCH- captures the Django data model
  - [ ] PROC- runtime architecture mentions workers, beat, queues
  - [ ] CON- artifacts exist for detected service pairs (or correctly notes single-service)
- [ ] Source extraction handles mixed stacks
  - [ ] Django REST API detected and extracted
  - [ ] TypeScript frontend packages are at least acknowledged
  - [ ] ERD from Django models works
- [ ] `/reef:scuba` Phase 1 runs
  - [ ] Manifest is built with reasonable artifact count
  - [ ] Cost estimate is shown before execution
  - [ ] Sub-steps produce real content (not stubs)
  - [ ] Phase 1 briefing shows completion status
  - [ ] Phase 2 questions are relevant to project management domain
- [ ] Health report after scuba shows meaningful coverage increase

### What could go wrong

- Monorepo with both Python and TypeScript — init may struggle with service grouping
- 13 docker-compose services may overwhelm the "3-15 repos" sweet spot messaging
- Celery workers + RabbitMQ may not be detected as "pipeline/orchestration" for PROC- flow catalogs
- Shared TypeScript `packages/` (ui, editor, types) may be miscounted as services

---

## Round 3 — Different Stack (Twenty)

**Repo:** [twentyhq/twenty](https://github.com/twentyhq/twenty) — CRM, NestJS + TypeORM + GraphQL + PostgreSQL, 19 packages
**Purpose:** Validate reef works with a completely different tech stack (not Django, not SQLAlchemy).

```bash
git clone https://github.com/twentyhq/twenty.git
```

### Checklist

- [ ] `/reef:init` detects NestJS and TypeORM
  - [ ] Tech stack table shows correct framework and ORM
  - [ ] Package manager (yarn/pnpm) is detected
- [ ] Source extraction finds TypeORM entities
  - [ ] ERD extraction path works for `@Entity()` decorators
  - [ ] GraphQL schema is detected (auto-generated from NestJS decorators)
- [ ] Snorkel artifacts are domain-correct
  - [ ] Terms like "contact," "company," "deal," "pipeline" appear — not "patient" or "case"
  - [ ] Entity relationships make sense for a CRM
- [ ] Scuba Phase 1 produces useful artifacts
  - [ ] API- artifacts document GraphQL operations (not REST endpoints)
  - [ ] SCH- has Mermaid ERD with CRM entities
  - [ ] DEC- captures observable decisions (why NestJS? why TypeORM?)

### What could go wrong

- NestJS is in the detection table but TypeORM extraction via runtime may fail in sandbox
- GraphQL schema generation from NestJS decorators is different from Graphene — tier 2 extraction may need different import path
- 19 packages may be grouped incorrectly

---

## Cross-Cutting Checks (All Rounds)

- [ ] **No hardcoded paths** — no `/Users/jessi/...` appears anywhere in output
- [ ] **No CSG/medical terms** — no CDM, CTL, RDP, DAIP, Lunit, breast, chest, DICOM in any artifact
- [ ] **`${CLAUDE_PLUGIN_ROOT}`** resolves correctly on the fresh device
- [ ] **reef.py commands work** — `lint`, `rebuild-index`, `rebuild-map`, `diff` all run without errors
- [ ] **Artifact contract** — every artifact has valid YAML frontmatter, matching ID/filename, non-empty freshness_note
- [ ] **Wikilinks** — relates_to targets exist as files, graph is connected
- [ ] **Resume detection** — if a skill is interrupted and re-run, it detects existing state correctly
- [ ] **`/reef:help`** — shows correct skill list and recommends a sensible next action
- [ ] **`/reef:health`** — produces a valid report with no crashes
- [ ] **`/reef:test`** — if questions were seeded, test pass runs and produces meaningful evaluation

---

## Exit Criteria

Reef is ready to launch when:

1. All three rounds complete without blocking errors
2. Artifacts are domain-correct and structurally valid for all three codebases
3. No CSG-specific content appears anywhere in output
4. A person unfamiliar with reef could follow the init flow without confusion
5. The reef produced for Plane (Round 2) would genuinely help a new engineer understand the system

---

## Notes

- Log all issues found during QA to `dogfood.md` with `[qa-round-N]` tag
- If a blocking issue is found, fix it and re-run that round from scratch
- Time each round (wall-clock) and record token usage for cost estimate validation
