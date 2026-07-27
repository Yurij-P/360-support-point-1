---
name: tps360-project
description: Work on the TPS360 / «Точка підтримки 360» repository, architecture, documentation, backend, simulation engine, community profiles, geospatial data, threats, multiplayer sessions, roles, facilitator and player interfaces, tests, or web UI. Use whenever analyzing, planning, implementing, reviewing, debugging, or continuing TPS360 work so prior approved requirements are read before changes and unsupported product behavior is not invented.
---

# TPS360 project workflow

## Start every TPS360 task

1. Resolve the repository, branch, HEAD, remote and working-tree status.
2. Read `MASTER_PROJECT.md` completely.
3. Read every relevant standard, ADR and domain rule before interpreting code.
4. Inspect the actual backend, frontend and tests affected by the request.
5. Preserve uncommitted user changes and never overwrite unrelated work.

If `MASTER_PROJECT.md` is missing, stop implementation and report the missing
source of truth. Do not reconstruct it silently from memory.

## Establish evidence before proposing changes

Create or maintain this mapping:

`document → approved requirement → backend → frontend → gap → required change`

Classify every intended change as one of:

- approved requirement;
- necessary technical consequence of an approved requirement;
- new product or methodological proposal requiring user approval.

Do not implement the third category before approval.

## Apply the source hierarchy

Use the precedence defined in `MASTER_PROJECT.md`.

Treat code and tests as evidence of the current implementation, not as proof that
the product behavior is approved. Treat screenshots and demo content as evidence
of UI state only.

When documents conflict:

1. Quote or precisely identify both requirements.
2. Explain the concrete architectural consequence of each interpretation.
3. Ask one focused question.
4. Do not edit the disputed behavior until resolved.

## Protect TPS360 invariants

- Keep TPS360 universal for territorial communities.
- Treat any named community as data or a test fixture, never a frontend constant.
- Bind every simulation to a selected community and versioned context.
- Separate real community/profile/map data from scenario and simulation state.
- Separate facilitator capabilities from player capabilities.
- Give each player a role-specific server-authorized view.
- Keep the shared community/crisis state consistent for all participants.
- Let the facilitator create the crisis and additional conditions.
- Do not invent roles, hierarchy, tasks, resource ownership or permissions.
- Do not call an unvalidated scenario or methodology validated.

## Work in small vertical slices

For each slice:

1. Update or add the governing standard/ADR when an approved decision is not yet
   documented.
2. Implement the domain model and invariants.
3. Implement the repository/service/API boundary.
4. Add focused domain and API tests.
5. Change frontend only after the data and authorization contract exists.
6. Update `MASTER_PROJECT.md` only when approved architecture or implementation
   status changes.

Do not begin with a visually complete screen backed by hard-coded domain data.

## Verify before handoff

Run:

```bash
pytest
ruff check .
mypy src/tps360
git diff --check
git status --short --branch
```

### Full-Stack Web UI Verification Protocol
When implementing or modifying frontend Web UI components (`app.js`, `api_client.ts`, HTML templates), you MUST execute the following 4-step alignment protocol before declaring completion:
1. **API Route Contract Alignment:** Verify all `fetch()` / API client URL paths against FastAPI router paths in `main.py` and routers (ensure root prefix alignment e.g. `/communities/catalog` instead of `/api/v1/...`).
2. **Response Payload Shape Alignment:** Verify backend return type shapes (e.g. object wrapper `{ items: [...] }` vs array `[...]`). In frontend code, always parse defensively: `Array.isArray(data) ? data : (data.items || [])`.
3. **Automated Endpoint & Asset Test:** Add unit/integration tests in `test_web_app_serving.py` and `test_frontend_api_integration.py` ensuring static files and REST endpoints return 200 OK with correct JSON contracts.
4. **Local Runtime Smoke Verification:** Launch the application locally and verify that frontend components render live backend data without silent client-side JavaScript console errors.

Report exact results. If a command cannot run, report why; never substitute an
assumed result.

Before commit or publication, review the full diff against the mapping and verify
that no hard-coded community, crisis, role or resource has been introduced.

## Stop conditions

Stop and ask the user when:

- a product decision is absent from the approved documents;
- two approved sources conflict;
- role names, hierarchy, permissions or resource ownership must be chosen;
- a destructive operation or unrelated user change would be affected;
- the correct repository or branch cannot be established.

Ask a concrete question grounded in files already inspected. Do not fill gaps with
plausible domain language.
