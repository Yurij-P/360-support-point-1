# ADR-0012: PostgreSQL persistence via SQLAlchemy 2 + Alembic

**Статус:** прийнято · **Дата:** 2026-07-27

## Контекст

ADR-0007 зафіксував in-memory репозиторії як тимчасове рішення для MVP. На етапі
Track B1 TPS360 потребує стійкого зберігання сесій, директив, симуляцій,
оцінювань та каталогу громад між перезапусками API, а також керованої еволюції
схеми БД.

## Рішення

Прийнято такі технічні рішення для persistence layer:

- **SQLAlchemy 2 (synchronous ORM)** як базовий persistence API.
- **Alembic** як єдиний механізм міграцій схеми.
- **PostgreSQL** для production і developer environments.
- **SQLite** для automated tests, включно з `:memory:` режимом.
- Конфігурація БД задається через змінну середовища `DATABASE_URL`.
- Значення за замовчуванням: `sqlite:///./tps360_dev.db`.

### Модель зберігання

- Для складних доменних об'єктів Pydantic використовується **JSON-колонка**
  `data`, що зберігає повний serialized snapshot aggregate/root object.
- Для пошуку, фільтрації та індексації зберігаються окремі **scalar-колонки**
  (`community_id`, `status`, `code`, `session_id`, `priority`, тощо).
- Доменні моделі залишаються Pydantic-моделями; SQLAlchemy ORM використовується
  лише на persistence-рівні.

## Альтернативи

- **Залишити in-memory repositories:** відхилено — дані губляться між
  перезапусками, немає міграцій та неможливо перейти до PostgreSQL.
- **Async SQLAlchemy:** відхилено для поточного етапу — не дає необхідної
  цінності для MVP API і ускладнює інтеграцію та тестування.
- **Повна нормалізація всіх вкладених моделей у окремі таблиці:** відхилено на
  Track B1 — надмірна складність для поточного доменного дизайну.

## Наслідки

- FastAPI репозиторії переходять на dependency injection через SQLAlchemy
  `Session`.
- Потрібно підтримувати Alembic-міграції як джерело правди для схеми.
- PostgreSQL драйвер додається як optional dependency.
- JSON snapshot storage спрощує міграцію з Pydantic domain model, але частина
  аналітичних запитів вимагатиме додаткових scalar-колонок або подальшої
  нормалізації.
