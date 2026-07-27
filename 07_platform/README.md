# Цифрова платформа

**Статус: технічний прототип v0.2.8.** Основні доменні модулі, FastAPI-сервер і TypeScript-клієнт реалізовані; повноцінний frontend та PostgreSQL persistence відсутні.

## Реалізовані модулі (код у `src/tps360/`)

| Модуль | Статус | Опис |
|---|---|---|
| `core/` | ✅ реалізовано | Базові типи, виключення, спільні утиліти |
| `community/` | ✅ реалізовано | Паспорт громади, ресурси, профіль готовності, OSM-каталог |
| `geospatial/` | ✅ реалізовано | Геопросторова модель, межі OSM, критична інфраструктура (40+ категорій) |
| `threat/` | ✅ реалізовано | Онтологія загроз, класифікація криз, ланцюжки впливу |
| `simulation/` | ✅ реалізовано | Рушій симуляції, раунди, дилатація часу, LEGO-рішення, SSE, AI Crisis Copilot |
| `api/` | ✅ реалізовано | FastAPI-сервер, 30+ ендпоінтів, SSE-транспорт |
| `ai/` | ✅ реалізовано | AICrisisCopilotService, EmpiricalCrisisIncidentFact, OSM-геообмеження |
| `frontend/` | ✅ реалізовано | TypeScript API Client (`api_client.ts`), OSM Map Viewer (`osm_map_viewer.ts`) |
| `web/` | ⚠️ частково | Static HTML/CSS/JS демо-дашборд; повноцінний frontend не розпочато |
| `analytics/` | ⚠️ частково | AAR Telemetry Service реалізовано; аналітичний дашборд відсутній |
| `assessment/` | 🔲 заплановано | Модуль оцінювання готовності (CPI/CPP) — окремий етап |
| `mobile/` | 🔲 заплановано | Мобільний досвід — окремий етап |

## Що відсутнє до Pilot Readiness

- PostgreSQL/SQLAlchemy (зараз in-memory, ADR-0007)
- Auth/RBAC
- Повноцінний frontend (React/Vue/Svelte — рішення не прийнято)
- Role catalog API
- Crisis Constructor
- Session Archive, Report export, Evaluation workflow
