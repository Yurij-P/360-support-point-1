# TPS360 Design System Draft

Status: draft specification. Scope: design guidance only; no CSS, components, dependencies, or implementation.

## Product framing

The visual system must support a community-first crisis-preparedness platform:

Community Catalog -> Community Profile / Passport -> Community Geospatial Overview -> Threat Selection / Threat Profile -> Scenario Selection for Community -> Simulation Context Snapshot -> Session Runtime -> Evaluation -> AAR -> Report -> Archive.

Bereznehuvatska community and the current water incident are test/example content only. The design system must not encode them as defaults.

## Design principles

TPS360 should feel like a professional Ukrainian crisis-preparedness platform:

- Reliable and calm under pressure.
- Modern without decorative overload.
- Operational, but not styled like a military game.
- Community context before scenario action.
- Clear hierarchy over visual drama.
- Fast to scan during facilitated sessions.
- Accessible for desktop control rooms, tablets, and participant phones.

## Palette

The current prototype uses a dark cyan/orange dashboard. The full platform should use a restrained neutral base with clear semantic states.

| Token | Suggested value | Use |
|---|---|---|
| `surface.page` | `#F6F8FA` | Main app background. |
| `surface.panel` | `#FFFFFF` | Panels, forms, cards. |
| `surface.muted` | `#EEF2F5` | Secondary areas. |
| `text.primary` | `#17202A` | Main text. |
| `text.secondary` | `#52616F` | Supporting text. |
| `border.default` | `#D8E0E7` | Dividers and controls. |
| `brand.primary` | `#0B5C7A` | Primary actions and navigation. |
| `brand.accent` | `#2F8F9D` | Highlights and selected states. |

Semantic colors:

| State | Color | Use |
|---|---|---|
| Info | `#2563EB` | Neutral system information. |
| Success | `#15803D` | Completed actions and accepted decisions. |
| Warning | `#B45309` | Readiness blockers, missing context, capacity warnings. |
| Critical | `#B91C1C` | Failed operations, destructive actions, severe injects. |
| Pending | `#64748B` | Waiting states. |
| Active | `#0B5C7A` | Live session state. |

Dark mode can be considered later. MVP should prioritize a light, highly legible operational interface. Dark surfaces can be reserved for map or live status panels if contrast is verified.

## Typography

Current fonts Inter and Outfit can be retained, but operational screens should avoid oversized display text.

| Role | Size | Weight | Notes |
|---|---|---|---|
| Page title | 28-32 px | 700 | One per screen. |
| Section title | 20-24 px | 600 | Major layout blocks. |
| Panel title | 16-18 px | 600 | Cards, forms, side panels. |
| Body | 14-16 px | 400 | Default readable text. |
| Metadata | 12-13 px | 500 | Status, timestamps, labels. |
| Button | 14-16 px | 600 | Clear action labels. |

## Layout system

Desktop:

- 12-column grid.
- Maximum content width around 1440 px for dense operational screens.
- App shell with top bar, optional left navigation, and content region.
- Community profile/geospatial/context screens support two or three panels.

Tablet:

- 8-column grid.
- Secondary panels collapse below or into tabs.
- Critical session state remains visible.
- Map controls must be touch-friendly.

Mobile:

- 4-column grid.
- Participant Join Session, active inject, decision form, and completion are single-column.
- Facilitator mobile is monitoring/emergency action only until product owner approves mobile facilitation.

Spacing follows an 8 px system: 4, 8, 16, 24, 32, and 48 px.

## Component specifications

### Catalog and selection components

Used by Community Catalog, Threat Selection, Scenario Selection, and Archive.

- Search field.
- Filter controls.
- Sort control only when API supports sorting.
- Card/list/table variants.
- Empty and no-results states.
- Clear selected item state.

PRODUCT DECISION REQUIRED: exact filters for community, threat, scenario, and archive screens.

### Community passport components

- Identity header: community name and key metadata.
- Metrics group: population, settlements, assets, preparedness indicators where data exists.
- Data freshness badge.
- Missing data callout.

PRODUCT DECISION REQUIRED: canonical passport fields and source of truth.

### Geospatial components

- Map viewport.
- Layer toggles.
- Selected feature panel.
- Legend.
- Missing/unavailable geodata state.

PRODUCT DECISION REQUIRED: map provider, layers, precision, and data governance.

### Threat/scenario/context components

- Threat card/profile.
- Scenario card/detail panel.
- Compatibility indicator.
- Simulation Context Snapshot summary.
- Context completeness checklist.

PRODUCT DECISION REQUIRED: threat taxonomy, scenario compatibility rules, snapshot immutability.

### Session runtime components

- Session status badge.
- Join code display.
- Participant card/list.
- Readiness checklist.
- Inject card.
- Decision form.
- Decision matrix.
- Session journal.
- Completion confirmation.

No exact role names, round counts, or round transitions are defined in this design system.

## Buttons

Types:

- Primary: one main action per screen or panel.
- Secondary: non-destructive alternatives.
- Tertiary/ghost: navigation and low-emphasis actions.
- Critical: complete session, revoke, destructive actions.
- Icon button: compact toolbar actions with accessible labels and tooltips.

Minimum touch target: 44 x 44 px.

## Fields

Fields must include visible labels, optional helper text, inline validation, disabled/readonly states, and error text. Errors must not rely on color alone.

Join code input should support uppercase normalization and segmented visual grouping only after join code format is approved.

## Statuses and badges

| Status | Code state | Visual treatment |
|---|---|---|
| Lobby | `LOBBY` | Neutral blue/gray. |
| Ready | `READY` | Success green. |
| Active | `ACTIVE` | Strong brand primary with live indicator. |
| Completed | `COMPLETED` | Closed/success neutral. |
| Cancelled | `CANCELLED` | Muted critical. |
| Evaluation | Not implemented | Future post-session status. |
| AAR / Debriefing | Not implemented | Future amber/blue bridge state. |
| Archived | Not implemented | Neutral gray. |

Context badges:

- Community selected.
- Passport incomplete.
- Geodata unavailable.
- Threat selected.
- Scenario compatible/unconfirmed.
- Snapshot ready/stale.

## Accessibility

Minimum requirements:

- WCAG AA contrast for text and controls.
- Keyboard navigation for all controls.
- Visible focus states.
- Accessible names for icon buttons.
- Form errors connected to inputs.
- Live regions for new injects and critical state changes.
- Minimum touch targets of 44 x 44 px.
- Reduced-motion support.
- No information conveyed by color only.
- Map information must have non-map textual alternatives.

## Responsive behavior

- Community Catalog: table/card hybrid on desktop, cards on mobile.
- Community Profile / Passport: metric groups collapse into sections on mobile.
- Community Geospatial Overview: desktop map with side panel; mobile map plus bottom sheet or detail page.
- Threat/Scenario selection: filter drawer on mobile.
- Active facilitator runtime: desktop/tablet primary; mobile monitoring only unless approved.
- Participant runtime: mobile-first.
