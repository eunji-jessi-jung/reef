## From snorkel + source to Scuba

What we have at this point:
- Fundamental artifacts: system, schema, glossary, contracts, apis
- Source-of-truth apis and erds

What's missing:
- Advanced artifacts: process, risks, decisions

What we want:
1. Automatically generate common advanced artifacts from what we have. This can include:
- Comprehensive schema and api docs (delta layer on top of OpenAPI, not duplication)
- For schema, it could be the data model + description of each entity. Make sure to differentiate RDB and MongoDB. Make sure to document the tech stack (e.g., Postgres)
- For api, it could be the api contract. Record anything out of ordinary or noteworthy.
- After creating these, maybe we can identify core entities and create definition and lifecycle docs for each core entity.
- I see we identified important basic questions like authn and authz. Maybe we can create advanced authorization boundary artifacts at this stage.
- FE/BE contract for each service. This can happen across systems and are worth exploring.
- Failure/error handling behavior for each service

2. Do Q&A with user to generate exploration-worthy questions based on common question patterns. This can include:
- If there are entities or concepts that overlap across services/systems, it's worth making comparison doc between them. It's almost always an issue when there is a same concept/entity with the same name across different systems/services.
- If there are any detailed AuthZ settings like RBAC, it's worth noting that.
- If there is a concept repeatedly used across a service (like "flow" in a pipeline service), it might be worth exploring. Ask user if they want to log everything that happens inside a flow.
- There might be services that have heavy dependencies on each other. Scan through repo, and find if some of the services are heavily dependent. If there is, it might be worth deep exploration. Ask user if they want to deep-dive into interface and contract between systems.
- If reef can find any business-related terms or logics, surface them. We can't be sure without user's confirmation.
