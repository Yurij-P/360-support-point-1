# ADR-0016: Platform-wide Community Identity Unification (UUID → KATOTTG)

**Status:** Proposed — pending ratification
**Date:** 2026-07-28

## Context

The platform currently carries **two parallel community identity systems**:

1. **Legacy UUID identity** — `core/domain/models.py` (`Community.id: UUID`, and
   `community_id: UUID` on `Simulation`, `Decision`, `Inject`, …), plus
   `assessment`, `risks`, `preparedness`, `geospatial`, `simulation/context`,
   `simulation/domain/session` (`FacilitatedSession.community_id: UUID`), and the
   API routers. ORM stores it as `String(36)`.
2. **KATOTTG identity** — the `community` catalog/passport module
   (`CommunityCatalogService`, `CommunityPassportReadModel.community_id`), where a
   community is the official **KATOTTG code** (e.g. `ua48060030000037887`), per
   `ADR-0014`. 42 communities from the official dataset.

These are **not linked**. `ADR-0014` moved the authoritative community model to
KATOTTG, but the simulation/session core still uses opaque UUIDs. `#41` bridged
sessions to passports additively (`katottg_community_code`) without touching the
UUID model — a stopgap, not a resolution. The split blocks direct passport-driven
behaviour everywhere and invites the exact hardcoding ADR-0014 removed.

## Decision

**Adopt the KATOTTG code as the single canonical community identifier
platform-wide.** `community_id` becomes a KATOTTG string everywhere; the legacy
UUID community identity is retired. Aligns the whole platform with `ADR-0014`.

Rationale: one authoritative, government-backed, verifiable identifier; direct
passport binding in every domain; removes the dual-identity confusion and the
additive bridge.

## Migration strategy (phased — each stage a separate green PR)

Big-bang is rejected (~18 declarations, core models, ORM, ~27 test files). Stage it:

1. **Type foundation.** Introduce a `CommunityId = str` alias and helpers
   (validate/normalize KATOTTG). No behaviour change.
2. **Leaf domains.** Migrate `assessment`, `risks`, `preparedness`, `geospatial`
   `community_id: UUID → CommunityId`; update their repos, routers and tests.
3. **Core + ORM.** Migrate `core/domain/models.py` (`Community`, `Simulation`,
   `Decision`, `Inject`) and the ORM columns/repositories; ensure `String` width
   holds a KATOTTG code (≤ 19 chars; current `String(36)` suffices).
4. **Session.** Migrate `FacilitatedSession.community_id → CommunityId`; make the
   `#41` `katottg_community_code` the primary community field and remove the bridge.
5. **Cleanup.** Remove the legacy UUID `Community` model/paths; passport binding
   becomes automatic from `community_id` everywhere.

After each stage: `pytest`, `ruff`, `mypy` green before merge.

## Consequences

- Substantial but staged test churn (~27 files touched across stages).
- API contract change: `community_id` request/response fields become KATOTTG
  strings (breaking for any external UUID caller — acceptable pre-pilot).
- Removes dual-identity confusion; passport/estimator/crisis-plan bind directly.
- ORM column semantics change from UUID-string to KATOTTG-string (no width change).
- `ADR-0014` invariant holds everywhere; the `#41` bridge is retired.

## Alternatives (rejected)

1. **Keep dual identity + bridge (status quo, `#41`).** Perpetuates confusion and
   the risk of hardcoded communities; only masks the split.
2. **UUID↔KATOTTG mapping table.** Reintroduces indirection/aliases that
   `ADR-0014` deliberately removed.
3. **Big-bang single-PR migration.** Too risky; breaks the green baseline.

## Open questions for ratification

1. Are external/legacy UUID community callers in play, or is a clean break fine
   pre-pilot?
2. Do we need a data migration for any persisted UUID community rows, or is the
   store effectively empty/dev-only so far?
3. Stage order acceptable, or migrate session (stage 4) earlier to unblock live
   passport binding sooner?

## Owner

Technical architecture + product.
