# ADR-0014: Community Identity via KATOTTG Codes

**Status:** Accepted
**Date:** 2026-07-27

## Context

Early prototype code identified communities by opaque UUIDs and, in several
places, hardcoded a single demo community (`a29d6fbd-…` / "Березнегуватська
громада") as an implicit default. This violated the core TPS360 invariant that
the platform must stay **universal** for all territorial communities and that
every simulation must bind to a **selected** community rather than a baked-in
constant.

Ukraine already has an official, stable, government-maintained identifier for
territorial communities: the **KATOTTG** code (Кодифікатор адміністративно-
територіального устрою та територій територіальних громад), e.g.
`UA48060030000037887`. The catalog was migrated to the official KATOTTG dataset
(`OFFICIAL_KATOTTG_DATASET`), covering communities across all oblasts.

## Decision

**Community identity is the official KATOTTG code.**

- The canonical `community_id` is the KATOTTG code in lower case (e.g.
  `ua48060030000037887`); `official_code` holds the upper-case form.
- The community catalog (`GET /communities/catalog`) is the single source of
  truth. Clients (and tests) select a community from the catalog; they never
  assume a specific community exists.
- `get_passport()` resolves by canonical id or `official_code` only. Unknown
  ids return `404`. The former legacy UUID/name alias map ("verkhovyna",
  "shiroke", the demo UUID) has been removed.
- Endpoints that operate on a community take the community explicitly. In
  particular `GET /simulations/{session_id}/context-snapshot` now requires
  `community_id` and `scenario_id` query parameters instead of hardcoding them.
- A typed KATOTTG code not yet in the dataset is registered dynamically on
  search, so the catalog is open-ended rather than a fixed enumeration.
- No community name, code, or UUID may be a frontend constant; the served SPA
  (`api/static`) forces selection from the catalog.

## Alternatives

1. **Keep opaque UUIDs.** Rejected — not tied to any official registry, invites
   hardcoded defaults, and gives no meaning to operators.
2. **Free-text community names as keys.** Rejected — ambiguous, unstable, not
   machine-verifiable against an authoritative source.
3. **Internal sequential ids mapped to KATOTTG.** Rejected — an extra indirection
   layer with no benefit over using the KATOTTG code directly.

## Consequences

- Identity is aligned with an authoritative national registry; codes are stable
  and verifiable.
- The demo community and its aliases are gone; the dead `src/tps360/web/`
  frontend that hardcoded it was deleted.
- Tests are catalog-driven and therefore community-agnostic.
- Callers must supply a community explicitly; there is no implicit default.
- Human-readable community names remain data on the passport, never identifiers.

## Owner

Technical architecture (repository maintainer).
