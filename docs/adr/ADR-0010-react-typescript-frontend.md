# ADR-0010: React + TypeScript як frontend-фреймворк

**Статус:** прийнято · **Дата:** 2026-07-27

## Контекст

TPS360 потребує повноцінного SPA із складними рольовими UI (Facilitator Console,
Participant Workspace, Lobby, AAR), реактивним оновленням стану через SSE та
інтеграцією з існуючими TypeScript-модулями (`api_client.ts`, `osm_map_viewer.ts`).
Наявний static HTML/CSS/JS у `src/tps360/web/` є лише demo-дашбордом і не може
бути базою для продуктового frontend.

## Рішення

Обрано **React** (остання стабільна версія) із **TypeScript**:

- Основний роутинг: React Router.
- Стан: React Context / Zustand (обирається при реалізації залежно від складності).
- Збірка: Vite (швидкий dev-сервер, нативний ESM, TypeScript out-of-the-box).
- Існуючі `api_client.ts` та `osm_map_viewer.ts` інтегруються як TypeScript-модулі
  без переписування.
- Frontend розташовується в `src/frontend/` (нова директорія SPA); `src/tps360/web/`
  лишається як legacy demo і не є продуктовою базою.

## Альтернативи

- **Vue 3 + TypeScript:** відхилено — React обрано за більшою екосистемою та
  кращою підтримкою складних рольових інтерфейсів.
- **SvelteKit:** відхилено на цьому етапі — менше спеціалістів, менша спільнота
  для UI-компонентів рольового workspace.
- **Vanilla TypeScript без фреймворку:** відхилено — складність ручного управління
  станом і SSE-підписками для 7+ екранів рольового workspace неприйнятна.

## Наслідки

- Потрібен `package.json`, `vite.config.ts`, `tsconfig.json` у `src/frontend/`.
- FastAPI продовжує обслуговувати API; frontend в dev запускається окремо
  (`vite dev`), у prod збирається в `dist/` та обслуговується FastAPI static.
- Усі frontend-компоненти отримують дані виключно через `api_client.ts`;
  прямі fetch-виклики в компонентах заборонені.
- Жоден компонент не хардкодить назву громади, роль або сценарій.
- Рольові дані отримуються від сервера; відображення визначається server-authorized
  role profile, а не умовами в коді компонента.
