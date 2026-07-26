# Журнал змін

Формат спирається на принцип Keep a Changelog. Версії до запуску платформи описують стан документів і концепції, а не готовність продукту.

## [0.2.3] — 2026-07-26

### Додано

- **PR #19 (Threat-Scenario Compatibility & Simulation Context Snapshot API):**
  - Сервіс каталогу та моделювання сценаріїв криз (`ScenarioCatalogService`, `ScenarioTemplateCatalogItem`).
  - Картографічна та топографічна модель евалуації сумісності за рельєфом (`SpatialTopographyFeature`, `ScenarioCompatibilityEvaluator`), що перевіряє можливість виникнення загрози за картою громади (гірський рельєф для зсувів ґрунту/Верховина vs рівнинний степ/Широке, близькість АЕС для радіації) з універсальною сумісністю ракетно-дронових загроз.
  - Immutable Read Model передстартового контекстного зрізу симуляції (`SimulationContextSnapshotReadModel`).
  - REST API Сценаріїв та Контексту (`GET /scenarios/catalog`, `POST /scenarios/compatibility-check`, `GET /simulations/{session_id}/context-snapshot`).

## [0.2.2] — 2026-07-26


### Додано

- **PR #18 (Community Catalog & OpenStreetMap Critical Infrastructure Passport Read Model API):**
  - Вичерпна доменна онтологія 40+ категорій об'єктів критичної інфраструктури, АПК, видобутку, військово-оборонного компонента та небезпек (`CriticalInfrastructureCategory`, `OSMTagMapping`), прикріплена до тегів OpenStreetMap (`openstreetmap.org`).
  - Агрегована Read Model Паспорта громади (`CommunityPassportReadModel`, `InfrastructureItemReadModel`) з картографічними межами OpenStreetMap, демографією, уразливими групами та балом готовності.
  - Сервіс каталогу громад (`CommunityCatalogService`, `CommunityCatalogItem`).
  - REST API Каталогу та Паспорта громад (`GET /communities/catalog`, `GET /communities/{community_id}/passport`).

## [0.2.1] — 2026-07-26


### Додано

- **PR #17 (Real-Time SSE Event Transport, Time Dilation Clock & Open AI Crisis Copilot):**
  - Математична та доменна модель дилатації часу (`SimulationRoundClock`, `CrisisVelocity`, розрахунок 1:30, 1:60, 1:90 для пожеж, епідемій холери, падіжу худоби, ізоляції, блек-аутів).
  - In-Memory PubSub шина подій реального часу (`SessionEventBroadcaster`, `SessionEvent`, `SessionEventType`) з рольовою фільтрацією.
  - Server-Sent Events (SSE) REST API (`GET /events/session/{session_id}/stream`, `GET /events/session/{session_id}/history`).
  - Відкрита онтологія криз та сервіс **AI Crisis Copilot** (`AICrisisCopilotService`), що моделює розвиток подій на основі джерел та ЗМІ під модерацією фасилітатора.
  - Суворе геопросторове обмеження подій ШІ у межах кордонів **OpenStreetMap (OSM BoundingBox / Relation)** громади.

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
