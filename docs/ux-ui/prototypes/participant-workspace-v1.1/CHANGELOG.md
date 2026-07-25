## 2.3 - Participant API integration

- Fixed the raw-template rendering cause by executing the component script as JavaScript and starting runtime reconnect after the first render.
- Added real join and participant polling calls with separate join and participant credentials.
- Added local participant session persistence and reconnect state handling without exposing the participant token.
- Removed participant-facing role controls; role profiles come only from facilitator assignment returned by the API.
- Added local API client tests and documented the local API/frontend launch commands.
- Added restricted local CORS for the participant preview origins.
# TPS360 Wireframes — changelog

## v2.1 · категорії учасників і рольова адаптація (25.07.2026)

- Додано каталог **7 категорій учасників** з усіма підролями (ОМС, старости, ДПК, заклади освіти, екстрені служби, комунальні та соціальні служби, громадський сектор) у розділі Participant flow, з тегом `PRODUCT DECISION REQUIRED — role permissions and information access`.
- У прототипі з’явився перемикач **«Демонстрація ролі»**: староста округу · керівник ДПК · директор ліцею. Від ролі залежать briefing, контекст громади, підсвічені об’єкти карти, ресурси, завдання, акцент у робочому вікні, запитання події та підказка «Відповідальні» у формі рішення.
- Структура інтерфейсу єдина для всіх ролей — шапка, зони, головна дія, стани й форма рішення не змінюються. Це зафіксовано текстом і таблицею «Адаптація Active Simulation Workspace під ролі» в документації.
- Демонстраційну роль «представник КП Водоканал» замінено на три конкретні ролі; загальні назви «представник установи» не використовуються.

## v2.0 · робоче середовище учасника (25.07.2026)

Новий файл `TPS360 Participant Wireframes.dc.html`. Погоджені шість community-first екранів у `TPS360 Wireframes.dc.html` **не змінювались**.

**Що додано**
- Клікабельний прототип семи low-fidelity екранів учасника: вхід за кодом → роль і briefing → lobby/readiness → active simulation workspace → подія (inject detail) → підготовка й подання рішення → завершення та індивідуальна рефлексія з debriefing preview.
- Participant flow (4 дорожки, включно з погодженим контекстом фасилітатора) і sitemap середовища учасника, окремо позначено «поза цим етапом» і «не проєктується» (чат, команди, рейтинги, таймери, AI).
- Робочі стани: підтвердження ознайомлення з briefing, підтвердження готовності, вкладки контексту (громада / карта / ресурси), подання рішення, надсилання рефлексії.
- Три альтернативні варіанти призначення ролі (A призначає фасилітатор / B вибір зі списку / C автоматично) — жоден не затверджений.
- Системні стани: 6 візуальних карток (loading, offline, reconnecting, new event, autosave/unsaved draft, submission accepted/failed) + таблиця з 19 станів із позначенням «текст + глиф + дія».
- Документація: таблиця з 20 компонентів, перелік mock-даних, запропоновані API, PRODUCT DECISION REQUIRED, 9 UX-ризиків.
- Специфікація під кожним екраном: мета, головна й другорядні дії, вхідні дані, що передається далі, стани, відкриті питання.
- Desktop 1280 і Tablet 834 для всіх екранів (робоче вікно, подія та форма рішення перебудовуються в один стовпець), пояснення mobile-поведінки.

**Обмеження, зафіксовані в макетах**
- REAL DATA не використовується; усе наповнення — MOCK DATA.
- Роли, етапи, раунди, час, структура рішення, методика оцінювання та AAR — PRODUCT DECISION REQUIRED.
- API — `API REQUIRED — PROPOSED CONTRACT, NOT IMPLEMENTED`.
- Адреси лише демонстраційні (`prototype.local`).
- High-fidelity дизайн, кабінет фасилітатора, адмінпанель і frontend не розроблялися.

## v1.1 · контрольні виправлення (25.07.2026)

1. Базові дані демонстраційної громади: населення **16 633**, населених пунктів **41**; щільність перерахована й позначена як розрахунок MOCK.
2. Позначку REAL DATA видалено з системи тегів — усі непідтверджені дані мають MOCK DATA.
3. API подаються як `API REQUIRED — PROPOSED CONTRACT, NOT IMPLEMENTED`.
4. `tps360.gov.ua` → `prototype.local`.
5. Lobby — лише демонстрація success-переходу, бейдж `PREVIEW — STAGE 2, NOT APPROVED WIREFRAME`.
6. Ролі, учасники, тривалість, складність і готовність сценаріїв — MOCK або PDR.
7. Таблицю mock-даних доповнено.

## v2.3 - persistent participant runtime (2026-07-25)

- Reordered the seven screens to Join -> Lobby / Readiness -> Role and Participant Briefing -> Active Simulation Workspace -> Inject Detail -> Decision Preparation and Submission -> Completion and Individual Reflection.
- Removed self-select, automatic, and random role assignment from the participant flow; role assignment is facilitator-only.
- Added explicit waiting-for-role-assignment state and stable participant identity/reconnect MOCK DATA.
- Replaced the three-role runtime switch with a universal role profile contract and added an emergency medical representative fixture.
- Kept the 7-category / 23-position catalog as UX reference data, not a session roster.
- Decision submission is local MOCK DATA with immutable Submitted state; backend integration remains API REQUIRED.


- Added guarded localStorage MOCK DATA persistence for participant identity, session_id, assigned role_id, role_version, roleAssigned, lifecycle state, reconnect, and submitted decisions.
- Removed participant-facing role switching. Role assignment is represented only by the facilitator-only MOCK DATA hook; the participant remains in a waiting state until assignment.
- The emergency medical representative fixture is loaded through the same universal role profile renderer without role-specific UI conditions.
- Submitted decisions now persist their full local contract and remain locked after reload; backend persistence remains API REQUIRED.
