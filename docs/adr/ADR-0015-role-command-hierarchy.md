# ADR-0015: Role Command Hierarchy (Incident Command over the community role catalog)

**Status:** Accepted
**Date:** 2026-07-27

## Context

`TPS360-ROLE-UX-001` approves a catalog of **7 categories / 23 UX positions** but
explicitly does **not** approve any command hierarchy (§1, §12.5 — "Які взаємодії
між ролями потребують формальної ієрархії" is listed as an open product decision).
`SKILL.md` §11 likewise lists role subordination and the right to assign tasks as
decisions that must not be invented.

The codebase currently carries **two** role vocabularies:

1. The approved UX catalog (`role_catalog_service.py`, e.g. `local-gov-head`,
   `emerg-dsns`, `communal-utility`).
2. Demo operational roles used by the live simulation engine
   (`role_dashboard_service.py` / `MASTER_PROJECT.md` §5, e.g. `head_of_emergency`,
   `chief_police_officer`), marked as fixtures / "ROLE MODEL NOT APPROVED".

The task system (`TaskDirective` with `issuer_role_id` / `assignee_role_id`)
currently issues directives only as `facilitator_moderator`, i.e. a de-facto
"facilitator-only" model with no inter-role command.

## Decision

Adopt an **Incident Command System (ICS)** model, defined over the **approved
KATOTTG role catalog** (not the demo roles). It mirrors the real Ukrainian local
civil-protection command: the head of the community leads the local emergency
response link/HQ (штаб з питань НС).

### Command tiers

- **Tier 0 — Moderation (outside the in-sim chain):**
  - **Facilitator / Модератор гри** — creates the session, injects events, approves
    AI proposals, advances rounds. May direct any role for moderation; is not a
    community role and is not "in command".
  - **System Administrator** — technical configuration only; outside command.

- **Tier 1 — Incident Commander:**
  - `local-gov-head` (**Голова громади**) — commands the response.

- **Tier 2 — Command staff (report to the Commander):**
  - `local-gov-civil-protection` — **Chief of Staff / operational coordinator** of
    the HQ; may relay and assign directives on the Commander's behalf.
  - `local-gov-deputy-head` — deputy commander.
  - `local-gov-executive-rep` — administrative/executive support.

- **Tier 3 — Functional leads (report to the Commander, coordinated via the Chief
  of Staff):**

  | Functional area | Reports to Commander as | Members |
  |---|---|---|
  | Екстрені та безпекові служби | **three peer leads**, each direct: `emerg-dsns`, `emerg-police`, `emerg-ems` | — |
  | Добровільні пожежні команди | `vol-fire-commander` (coordinates functionally with ДСНС) | `vol-fire-member` |
  | Комунальні та соціальні служби | **four independent leads**, each direct: `communal-utility`, `communal-medical`, `communal-social-service`, `communal-child-services` | — |
  | Заклади освіти | `edu-director` | `edu-deputy-director`, `edu-civil-protection`, `edu-shelter-evac` |
  | Старости (територіальні) | `starost-district` | `starost-remote-rep`, `starost-info-coordinator` |
  | Громадський сектор | `civil-humanitarian-hub` | `civil-ngo`, `civil-volunteer-group` |

  Ratified 2026-07-27: emergency-service reps are peers reporting directly to the
  Commander (not subordinate to each other); the volunteer fire team reports to the
  Commander and coordinates with ДСНС; communal/social services are four independent
  functional leads.

### Task-assignment & subordination rules (server-enforced)

1. **Facilitator** may issue directives/injects to any role (moderation only).
2. **Commander** (`local-gov-head`) may issue directives to command staff and to
   functional leads.
3. **Chief of Staff** (`local-gov-civil-protection`) may issue/relay directives to
   functional leads on the Commander's behalf.
4. **Functional lead** may issue directives only to members of **its own** area.
5. **Members** may not issue directives. They may raise **requests / escalations**
   upward and initiate **resource-transfer requests** (existing
   `ResourceTransferDirective`) subject to authorization by their lead or Commander.
6. Authorization is enforced **server-side**; hiding controls in the browser is not
   an access mechanism (per `TPS360-ROLE-UX-001` §3.5).
7. One participant holds at most one role per session (`TPS360-ROLE-UX-001` §5.3).

## Prerequisites for implementation

These are engineering follow-ups, not open hierarchy decisions:

1. **Demo-role → catalog reconciliation.** `MASTER_PROJECT.md` §5 demo roles
   (`head_of_emergency`, `chief_*`) conflate "керівник штабу з НС" with
   `head_of_emergency`. Under this ADR the HQ commander is the **Голова громади**
   (`local-gov-head`). The live engine (`role_dashboard_service`, directives,
   resource transfers) must be migrated onto the catalog role ids (or the demo roles
   explicitly deprecated) before command rules can be enforced.
2. **Directive authorization.** `TaskDirective` issuance must validate the
   issuer→assignee edge against this command chain in the session/directive service.
3. **Member request/escalation contract.** Only resource transfers exist today; an
   upward request/escalation contract is required for Tier-3 members.

## Alternatives (rejected)

- **Flat / facilitator-only.** Matches the current de-facto state; lowest realism —
  no inter-role subordination.
- **Coordination network (peers, no subordination), request-based.** A Commander with
  final approval but no direct orders.

Both rejected in favour of a true ICS command chain.

## Consequences

- Answers `TPS360-ROLE-UX-001` §12.5 for the platform's default command model;
  individual scenarios may still use a subset of the catalog per §5.2.
- Establishes the authority model that directive, escalation and resource-transfer
  contracts must enforce.
- Requires the reconciliation and authorization work listed under Prerequisites
  before any behavioural change ships.

## Owner

Product (community-governance domain) + technical architecture.
