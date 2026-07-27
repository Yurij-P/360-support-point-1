# ADR-0011: JWT для автентифікації фасилітатора та учасників

**Статус:** прийнято · **Дата:** 2026-07-27

## Контекст

TPS360 має два типи акторів із різними повноваженнями: **Фасилітатор** (керує
сесією, надсилає вводні, затверджує рішення ШІ) та **Учасник** (гравець із
рольовим workspace). Зараз `X-Facilitator-Token` та `X-Participant-Token`
генеруються при створенні сесії, але механізму входу/реєстрації не існує.
ADR-0009 залишив спосіб входу як відкладене рішення.

## Рішення

Обрано **JWT (JSON Web Tokens)** із парою Access + Refresh token:

### Токени

| Токен | TTL | Зберігання | Призначення |
|---|---|---|---|
| Access token | 15–30 хв | `memory` (JavaScript variable) | Авторизація запитів до API |
| Refresh token | 7–30 днів | `httpOnly cookie` | Оновлення access token |

### Ролі (claims у JWT)

- `role: facilitator` — видається після логіну фасилітатора.
- `role: participant` — видається після join за invite-посиланням/кодом.
- `session_id` — прив'язка токена до конкретної сесії.
- `participant_role_id` — присвоєна роль (після призначення фасилітатором).

### Ендпоінти авторизації (нові)

```
POST /auth/login              # логін фасилітатора → access + refresh
POST /auth/refresh            # оновити access token
POST /auth/logout             # інвалідувати refresh token
POST /auth/join               # учасник входить за кодом/посиланням → access + refresh
```

### Інтеграція з існуючою моделлю токенів

Існуючі `X-Facilitator-Token` та `X-Participant-Token` замінюються стандартним
`Authorization: Bearer <access_token>`. Роль та session_id витягуються FastAPI
dependency з JWT payload. Серверна авторизація (`FacilitatorToken`, `ParticipantToken`)
рефакторингується на JWT-validation middleware.

## Альтернативи

- **Розширення поточних session-токенів:** відхилено — не підтримує механізм
  логіну/реєстрації та lifecycle refresh; потребує зберігання на сервері.
- **Server-side sessions (cookie-based):** відхилено — ускладнює stateless
  масштабування; вимагає серверного session store.
- **Anonymous join без облікового запису:** відхилено для фасилітатора — фасилітатор
  має мати ідентичність для аудиту; для учасника anonymous join лишається
  можливим варіантом для demo-режиму (Демо 1-50 осіб).

## Наслідки

- Потрібна бібліотека `python-jose` або `PyJWT` + `passlib[bcrypt]` у
  `pyproject.toml`.
- FastAPI dependency `get_current_facilitator` / `get_current_participant`
  замінює ручну перевірку заголовків.
- Refresh token зберігається на сервері (таблиця `refresh_tokens` в PostgreSQL)
  для можливості інвалідації.
- Frontend зберігає access token у пам'яті (не localStorage) для захисту від XSS.
- Учасник у Демо-режимі може входити без повного облікового запису через
  invite-код; у Production-режимі — потрібна ідентифікація.
- Ця ADR залежить від реалізації PostgreSQL (ADR-0012 / Трек B1).

## Відкладено

- MFA / 2FA — поза межами поточного прототипу.
- SSO / OAuth2 (Google, Diia) — окремий ADR після пілотного відбору організацій.
- Гранулярний RBAC на рівні ресурсів — визначається разом із каталогом ролей
  (Трек B3 / D4).
