# TPS360 Wireframes — changelog

## v1.1 · контрольні виправлення (25.07.2026)

Структура community-first і low-fidelity стиль не змінювались.

1. **Базові дані демонстраційної громади виправлено:** Березнегуватська громада — населення **16 633**, населених пунктів **41**. Оновлено в каталозі громад, паспорті, шарі «Населені пункти», Simulation Context Snapshot і контексті сесії. Щільність перерахована (14,7 осіб/км²) і позначена як розрахунок MOCK.
2. **Позначку REAL DATA видалено з системи тегів.** Усі непідтверджені числові, геопросторові, інфраструктурні та демографічні дані мають тег **MOCK DATA** (населення блоками, укриття, підстанції, вразливі групи, навчальні цілі, показники снепшота). Формулювання «11 із 14 НП» замінено на «більшість НП (MOCK)».
3. **API більше не подаються як чинні.** Тег змінено на `API REQUIRED · PROPOSED`; у таблиці документації — заголовок і колонка `API REQUIRED — PROPOSED CONTRACT, NOT IMPLEMENTED`, з приміткою, що назви, параметри та структура відповіді — PRODUCT DECISION REQUIRED. Ті самі підписи в екранах 1, 3, 7 і в специфікаціях.
4. **Адресу `previous public-domain placeholder` замінено на нейтральну `prototype.local`** (адресний рядок фрейму та посилання приєднання в lobby).
5. **Lobby залишено лише як демонстрацію success-переходу** після створення сесії; позначено бейджем **PREVIEW — STAGE 2, NOT APPROVED WIREFRAME**, текст уточнено.
6. **Ролі, кількість учасників, тривалість, складність, раунди та статус готовності сценаріїв** позначено як MOCK або PDR: підписи полів картки сценарію (`ТРИВАЛІСТЬ · MOCK`, `СКЛАДНІСТЬ · MOCK`, `УЧАСНИКИ · PDR`, `РОЛІ · PDR`), бейдж готовності `… · MOCK`.
7. **Таблицю mock-даних доповнено** рядками: базові дані громади (надані замовником проти вигаданих), ролі/учасники/тривалість/раунди, lobby-прев’ю.

Наступний крок — погодження логіки й переходів. High-fidelity дизайн і дизайн-система не розпочаті.

## Review hardening update

- Repaired prototype HTML and changelog text as valid UTF-8 Ukrainian content.
- Replaced the generated runtime with a local vanilla JavaScript renderer that does not use `new Function`, `eval`, remote module loading, Babel, React, or ReactDOM.
- Removed Google Fonts and all third-party CDN requests; the prototype now uses system font fallbacks.
- Removed cross-window messaging from the docs prototype runtime instead of allowing wildcard `postMessage` traffic.
- Verified the local click-through path in Chrome from Community Catalog through Simulation Context Snapshot and Lobby preview.
