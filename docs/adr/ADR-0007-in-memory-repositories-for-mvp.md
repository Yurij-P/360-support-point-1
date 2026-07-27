# ADR-0007: In-memory репозиторії для MVP

**Статус:** замінено [ADR-0012](ADR-0012-postgresql-persistence.md) · **Дата:** 2026-07-24

> **Оновлення (2026-07-27):** рішення замінено ADR-0012, який приймає persistence
> на SQLAlchemy 2 + Alembic (PostgreSQL для production, SQLite для тестів). Міграцію
> персистентних репозиторіїв здебільшого виконано: `community`, `session`,
> `simulation`, `assessment` та `directive` віддаються через SQLAlchemy
> (`tps360.api.dependencies` → `Depends(get_*_repo)`). Лишається один in-memory
> репозиторій — `preparedness_profiles`. Окремо існує in-memory рантайм-стан у
> сервісах (шина подій, рольові кабінети, читацька модель каталогу громад) — це не
> persistence-репозиторії й ADR-0012 їх не стосується.

Для Sprint 1 використовуються in-memory репозиторії, щоб перевірити доменні контракти без створення схеми БД. PostgreSQL залишається цільовою базою; перехід на SQLAlchemy/Alembic вимагатиме окремого ADR і міграцій. Дані MVP не є довготривалими.
