# Журнал змін

Формат спирається на принцип Keep a Changelog. Версії до запуску платформи описують стан документів і концепції, а не готовність продукту.

## [0.2.6] — 2026-07-26

### Додано

- **PR #22 (Facilitator Master Control Dashboard, 5-Variant Future Crisis Vision Engine & Psychological Stress Injection API):**
  - Головна пульт-консоль Фасилітатора (`FacilitatorConsoleService`, `FacilitatorConsoleReadModel`, `CrisisLifecycleProjectionVariant`).
  - Рушій бачення на 1 раунд уперед з 5 проєкціями розвитку кризової події (`BEST_CASE_CONTAINED`, `MODERATE_STABLE`, `ESCALATION_HAZARD`, `INFRASTRUCTURE_COLLAPSE`, `WORST_CASE_CASCADE`).
  - Модерація та затвердження вводних ШІ-Копілота Фасилітатором перед розсилкою гравцям.
  - Рушій психологічного навантаження та фрикцій у Кабінеті гравця (`PsychologicalFrictionInject`): сирени повітряної тривоги (аудіо/візуальний сигнал), термінові телефонні дзвінки, паніка у соцмережах/Telegram-каналах, протести мешканців під міськрадою, побутові форс-мажори (загублені ключі).
  - Обчислення індексу когнітивного стресу (`cognitive_stress_level_pct`) та коригування коефіцієнта спроможності ролі (`capability_score`).
  - Динамічне оцінювання ШІ тривалості гри: залучення ресурсів та правильність рішень гравців визначають момент успішної ліквідації НС та завершення симуляції (`COMPLETED_SUCCESS`).
  - REST API Консолі Фасилітатора (`GET /sessions/{id}/facilitator-console`, `GET /sessions/{id}/future-projections`, `POST /sessions/{id}/injects/approve-ai-proposal`, `POST /sessions/{id}/injects/psychological-friction`, `POST /sessions/{id}/rounds/advance`).

## [0.2.5] — 2026-07-26


### Додано

- **PR #21 (Role Dashboard Workspace, LEGO Decision Card Builder, Resource Exhaustion & Inter-Role OMS Resource Transfer API):**
  - Сервіс рольових кабінетів, відкритих конструкторів карточок LEGO та перерозподілу ресурсів (`RoleDashboardService`, `LegoDecisionCard`, `ResourceTransferDirective`, `RoleWorkspaceReadModel`).
  - Стартовий інвентар ресурсів для ролей (`head_of_emergency`, `chief_medical_officer`, `chief_sanitary_inspector`, `chief_police_officer`, `chief_utility_officer`).
  - Відкритий конструктор каток рішень LEGO: будується гравцем самостійно з кубиків дій (`EVACUATE`, `CONTAIN`, `EXTINGUISH_FIRE`, `REPAIR_LINE`, `DECONTAMINATE`, `DEPLOY_SHELTER`, `DISTRIBUTE_SUPPLIES` тощо), об'єктів OpenStreetMap та залучення ресурсів.
  - Підтримка 100% списання залучених ресурсів за раунд з негайним блокуванням/резервуванням та відкладеним виконанням під час завершення раунду (`PENDING_ROUND_EXECUTION`).
  - Офіційний міжрольовий перерозподіл ресурсів за Розпорядженнями Керівника штабу / Голови ОМС у межах повноважень місцевого самоврядування.
  - REST API Кабінету ролі та Ресурсів (`GET /sessions/{id}/role-workspace`, `POST /sessions/{id}/lego-decisions`, `POST /sessions/{id}/resource-transfers`).

## [0.2.4] — 2026-07-26

### Додано

- **PR #20 (Multi-Participant Lobby Standby Room, Role Assignment & Pre-Start Readiness Guard API):**
  - Сервіс кімнати очікування Лобі та реєстрації гравців (`SessionLobbyService`, `LobbyParticipantStatus`, `LobbyRoomStatus`).
  - Конфігуратор місткості лобі: Демо/Тестовий режим (1-50 осіб) та Продакшн-регламент (5-20 осіб).
  - Процедури реєстрації учасників у кімнаті очікування (Standby Room) та закріплення унікальних оперативних ролей (`head_of_emergency`, `chief_medical_officer` тощо) Фасилітатором.
  - Суворий бар'єр старту сесії (Pre-start Readiness Guard), що блокує запуск гри до моменту отримання ролі кожним підключеним учасником.
  - REST API Кімнати очікування та Ролей (`POST /sessions/{id}/lobby/join`, `POST /sessions/{id}/lobby/assign-role`, `GET /sessions/{id}/lobby-status`).
  - Сервіс об'єктивного заземлення ШІ-Копілота (`AICrisisCopilotService`, `EmpiricalCrisisIncidentFact`) на підтверджені факти реальних воєнних подій, протоколи повторних ударів (Double-tap) та радіуси розльоту БК.

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
