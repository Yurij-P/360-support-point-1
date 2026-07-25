# TPS360 Participant Workspace Wireframes

## Status

APPROVED UX LOGIC prototype. Low-fidelity UX artifact, not production frontend code.

## Seven-screen lifecycle

1. Join Session.
2. Lobby / Readiness.
3. Role and Participant Briefing.
4. Active Simulation Workspace.
5. Inject Detail.
6. Decision Preparation and Submission.
7. Completion and Individual Reflection.

The facilitator assigns the role between Lobby and Briefing. Participants cannot self-select, change, automatically receive, or randomly receive a role.

## Role model

The runtime uses a universal scenario/session role profile contract with: `role_id`, `role_version`, `title`, `category_id`, `category_title`, `briefing`, `responsibilities`, `permissions`, `available_data`, `resources`, `allowed_actions`, `restrictions`, `interactions`, `visibility_rules`, and `tasks`.

The three original profiles and the emergency medical representative are demo fixtures. The fourth profile validates that the same shell works for an arbitrary category; it is not a production role definition.

The 7-category / 23-position catalog is a UX coverage reference only. It is not the roster of this session.

## Data and API markers

- `MOCK DATA` identifies illustrative local values.
- `API REQUIRED - PROPOSED CONTRACT, NOT IMPLEMENTED` identifies backend work not implemented here.
- `ROLE MODEL NOT APPROVED` identifies demo role content.
- `PRODUCT DECISION REQUIRED` identifies unresolved product behavior.

Participant identity, facilitator assignment, role profile, lifecycle state, and reconnect are persisted in localStorage as MOCK DATA. A reload restores the same participant_id, session_id, assigned role_id and role_version without participant self-selection. Future server persistence and role assignment are API REQUIRED. Decisions are persisted locally with decision_id, participant_id, session_id, inject_id, entered data, Submitted status, submitted_at, and locked=true; editing and resubmission remain disabled after submission.

## Local preview

```powershell
python -m http.server 3001 --bind 127.0.0.1 --directory docs/ux-ui/prototypes/participant-workspace-v1.1
```

Open `http://localhost:3001/TPS360%20Participant%20Wireframes.html`. No dependencies, CDN, network calls, `eval`, `new Function`, or `postMessage` are used.
