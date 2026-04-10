# Understanding Template

33 questions across 7 phases for systematic codebase discovery. These are generalized starting points. Skills adapt them based on what the structural scan reveals about the target codebase.

---

## Phase A -- Orientation (5 questions)

1. What is this system's primary purpose in one sentence?
2. Who are the primary users or consumers of this system?
3. What team owns this system and who makes architectural decisions?
4. What are the critical runtime dependencies (databases, queues, external services)?
5. What does the deployment topology look like?

---

## Phase B -- Boundaries (5 questions)

6. What data flows into this system and from where?
7. What data flows out and to where?
8. What are the agreed-upon contracts at each boundary?
9. Which boundaries are formal (API specs, schemas) vs informal (conventions, tribal knowledge)?
10. Where do boundary failures cause the most pain?

---

## Phase C -- Data (5 questions)

11. What are the core domain entities and how do they relate?
12. Which entities are owned by this system vs referenced from others?
13. What are the key state machines or lifecycle transitions?
14. Where does data transformation happen (ETL, mapping, enrichment)?
15. What data consistency guarantees exist (or do not)?

---

## Phase D -- Behavior (5 questions)

16. What are the critical user-facing workflows?
17. What are the critical system-to-system workflows?
18. Where does error handling matter most?
19. What retry and recovery mechanisms exist?
20. What are the known performance bottlenecks or scaling limits?

---

## Phase E -- Decisions (4 questions)

21. What were the most significant architectural decisions and why?
22. Which decisions are candidates for reversal or rethinking?
23. What constraints drove the current design (regulatory, legacy, team size)?
24. What technical debt is acknowledged but deferred?

---

## Phase F -- Operations (5 questions)

25. How is this system monitored and what alerts exist?
26. What does the incident response process look like?
27. What are the most common failure modes?
28. How are schema migrations coordinated?
29. What is the disaster recovery plan?

---

## Phase G -- Gaps (4 questions)

30. What do new team members struggle with most?
31. What knowledge exists only in one person's head?
32. What would break if the primary maintainer left?
33. What questions does this system's documentation fail to answer?

---

## Adaptation Rules

These rules modify the question set based on what the structural scan discovers:

- **Multi-source systems:** Add boundary questions for each source pair. Phase B expands to cover every ingestion and emission point.
- **Complex auth:** Add auth-specific questions under Phase D (e.g., "What are the authorization boundaries?", "How are roles and permissions modeled?").
- **Event-driven architectures:** Add event flow questions under Phase D (e.g., "What events does this system publish?", "What are the ordering guarantees?").
- **Simple or single-purpose systems:** Remove Phases E and F. Focus depth on Phases C and D where the real behavior lives.
- **Always:** Skip questions already answered by existing artifacts in the vault. Do not re-ask what is already known.
