# ADR-0013: Join Code Format (D3)

**Status:** Accepted  
**Date:** 2026-07-27

## Context

Participants need to join a facilitated session. The backend generates two separate
values when creating a session: `session_id` (UUID) and `join_token` (URL-safe random
string). We needed to decide how facilitators share these with participants.

Options considered:

1. **Two separate fields** — facilitator shares `session_id` and `join_token` independently;
   participants fill in two input fields.
2. **One combined code** — both values concatenated with a known separator;
   participants paste one string into one field.
3. **QR code** — one field, rendered as a scannable QR on the facilitator's screen.

## Decision

**Option 2 — one combined field** using `|` as the separator:

```
join_code = "{session_id}|{join_token}"
```

The `|` character never appears in UUID v4 (`[0-9a-f-]`) or `token_urlsafe` output
(`[A-Za-z0-9_-]`), so splitting on `|` is unambiguous.

The frontend `JoinSession.tsx` splits on `|`, validates that exactly two non-empty
parts are present, and calls `POST /sessions/{session_id}/participants/join` with
`{ join_token, display_name }`.

The facilitator's `CreateSession.tsx` constructs the code as
`${session.id}|${session.join_token}` and offers a one-click copy button.

## Consequences

- **Backend unchanged** — no new endpoint; no schema migration.
- **Participant UX** — one copy-paste action, no manual pairing of two fields.
- **QR rendering** (Option 3) is deferred to a later track; the single-field format
  is QR-compatible (short enough to encode efficiently).
- **Reconnect** (D3b) — `participant_token` based reconnect remains a separate open
  decision; the join code is one-time-use only.
