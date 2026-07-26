# Журнал змін

Формат спирається на принцип Keep a Changelog. Версії до запуску платформи описують стан документів і концепції, а не готовність продукту.

## [0.2.0] — 2026-07-26

### Додано

- **PR #16 (Task Contract & Directive System & Round Infrastructure):**
  - Доменна модель доручень та рольових завдань (`TaskDirective`, `DirectiveStatus`, `DirectivePriority`).
  - Сервіс управління та синхронізації раундів (`RoundExecutionService`).
  - REST API рольових доручень (`/directives`, `/directives/{id}`, `/directives/{id}/transition`, `/directives/session/{session_id}`).
- **PR #15 (Task Round Execution Engine):**
  - Детермінований доменний рушій раундів (`TaskRoundExecutionEngine`, `TaskExecution`, `ExecutionResourceState`, `ResourceReservation`).
  - Гарантія незмінності, атомарності та ідемпотентності раундових команд.
- **PR #14 (Participant Capability Compatibility Model):**
  - Модель відповідності та перевірки сумісності спроможностей ролей гравців із ресурсними потребами.
- **PR #13 (LEGO Participant Decision Schema):**
  - Модуль та валідатор структурованих рішень учасників симуляції (`validate_decision_payload`).
- **PR #12 (Universal Participant Transport & Security):**
  - Автентифікація токенів гравців (`participant_token`, `join_token`), захист рольових даних та ізоляція рольових інтерфейсів.

## [0.1.0] — 2026-07-24

### Додано

- стартову структуру TPS360 та модульний технічний контур;
- базові документи Foundation: статут, архітектуру, дорожню карту, кодекс поведінки й глосарій;
- стандарти методології, врядування, симуляцій, AAR, індексу готовності, CPMM і CPP;
- ADR для цільової архітектури, симуляційного рушія, індексу готовності та AI-підтримки;
- Sprint 2A.1: базову геопросторову модель карти громади.
