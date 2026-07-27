# API

**Статус: реалізовано (v0.2.8).** FastAPI-сервер з повним набором REST API та SSE-транспортом реального часу.

## Реалізовані ендпоінти (v0.2.8)

- **Громади:** `GET /communities/catalog`, `GET /communities/{id}/passport`
- **Сценарії:** `GET /scenarios/catalog`, `POST /scenarios/compatibility-check`, `GET /simulations/{id}/context-snapshot`
- **Сесії та лобі:** `POST /sessions`, `POST /sessions/{id}/lobby/join`, `POST /sessions/{id}/lobby/assign-role`, `GET /sessions/{id}/lobby-status`
- **Симуляція:** `POST /sessions/{id}/rounds/advance`, `GET /sessions/{id}/role-workspace`, `POST /sessions/{id}/lego-decisions`, `POST /sessions/{id}/resource-transfers`
- **Консоль фасилітатора:** `GET /sessions/{id}/facilitator-console`, `GET /sessions/{id}/future-projections`, `POST /sessions/{id}/injects/approve-ai-proposal`, `POST /sessions/{id}/injects/psychological-friction`
- **Доручення:** `/directives`, `/directives/{id}`, `/directives/{id}/transition`
- **SSE:** `GET /events/session/{id}/stream`, `GET /events/session/{id}/history`
- **AAR та аналітика:** `GET /sessions/{id}/aar-report`, `GET /sessions/{id}/telemetry`, `GET /sessions/participants/{id}/experience-record`
- **ШІ:** `POST /sessions/{id}/ai-resource-estimate`
- **Профілі готовності та учасники**

## Авторизація

Фасилітатор: `X-Facilitator-Token`. Учасник: `X-Participant-Token`. Сервер не повертає токени після створення сесії.

## Не реалізовано

- Auth/RBAC (логін, видача токенів) — відкрите рішення MASTER_PROJECT §11
- Role catalog API — заплановано в Треку B3
- Crisis Constructor — заплановано в Треку B4
- PostgreSQL persistence — зараз in-memory (ADR-0007)
