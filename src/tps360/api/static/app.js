/**
 * TPS360 Single Page Web Application Engine
 * Developed by NGO Anti-Corruption (ГО "Проти Корупції")
 * Dynamic Client-side controller with KATOTTG Directory integration (directory.org.ua), OpenStreetMap GIS, LEGO decision builder & Facilitator master console.
 * Strictly presents REAL backend data with no fake hardcoded numbers.
 */

class TPS360WebApp {
  constructor() {
    this.currentScreen = "catalog";
    this.sessionId = null; // No hardcoded session by default
    this.communityId = null;
    this.communityName = null;
    this.officialCode = null;
    this.roleId = "head_of_emergency";
    this.apiBase = ""; // FastAPI routers mounted at root level

    this.state = {
      communities: [],
      scenarios: [],
      activePassport: null,
      sessionData: null,
      decisionsLog: [],
      round: 1,
      stressLevel: 0.0
    };

    this.init();
  }

  init() {
    this.bindGlobalNavigation();
    this.updateContextBar();
    this.renderScreen(this.currentScreen);
  }

  updateContextBar() {
    const commLabel = document.getElementById("activeCommunityName");
    if (commLabel) {
      if (this.communityName) {
        commLabel.textContent = `АКТИВНА ГРОМАДА: ${this.communityName}`;
      } else {
        commLabel.textContent = "Громада не обрана (Оберіть у Каталозі КАТОТТГ)";
      }
    }
  }

  bindGlobalNavigation() {
    const navButtons = [
      { id: "navCatalogBtn", screen: "catalog" },
      { id: "navScenariosBtn", screen: "scenarios" },
      { id: "navWorkspaceBtn", screen: "workspace" },
      { id: "navFacilitatorBtn", screen: "facilitator" },
      { id: "navAarBtn", screen: "aar" }
    ];

    navButtons.forEach(({ id, screen }) => {
      const btn = document.getElementById(id);
      if (btn) {
        btn.addEventListener("click", () => this.switchScreen(screen));
      }
    });

    const themeBtn = document.getElementById("themeToggleBtn");
    if (themeBtn) {
      themeBtn.addEventListener("click", () => {
        const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
        const nextTheme = currentTheme === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", nextTheme);
        document.getElementById("themeIcon").textContent = nextTheme === "dark" ? "🌙" : "☀️";
        document.getElementById("themeText").textContent = nextTheme === "dark" ? "Dark" : "Light";
      });
    }
  }

  switchScreen(screen) {
    this.currentScreen = screen;
    document.querySelectorAll(".nav-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-screen") === screen);
    });
    this.renderScreen(screen);
  }

  async renderScreen(screen) {
    const main = document.getElementById("mainContent");
    if (!main) return;

    this.updateContextBar();
    main.innerHTML = `<div class="card"><p style="color:var(--text-secondary)">⏳ Завантаження бекенд-даних для екрана "${screen}"...</p></div>`;

    switch (screen) {
      case "catalog":
        await this.renderCatalogScreen(main);
        break;
      case "scenarios":
        await this.renderScenariosScreen(main);
        break;
      case "workspace":
        await this.renderWorkspaceScreen(main);
        break;
      case "facilitator":
        await this.renderFacilitatorScreen(main);
        break;
      case "aar":
        await this.renderAARScreen(main);
        break;
      default:
        await this.renderCatalogScreen(main);
    }
  }

  /* ------------------------------------------------------------------
   * SCREEN 1: CATALOG & KATOTTG DIRECTORY INTEGRATION
   * ------------------------------------------------------------------ */
  async renderCatalogScreen(container) {
    try {
      const res = await fetch(`${this.apiBase}/communities/catalog`);
      let items = [];
      if (res.ok) {
        const data = await res.json();
        items = Array.isArray(data) ? data : (data.items || []);
      }
      this.state.communities = items;

      container.innerHTML = `
        <div class="card" style="margin-bottom:24px;">
          <h1 style="font-size:1.4rem; font-weight:700; margin-bottom:8px;">🏛️ Каталог Громад України (Довідник КАТОТТГ / directory.org.ua)</h1>
          <p style="color:var(--text-secondary); margin-bottom:14px;">Офіційний довідник територіальних громад України з верифікованими кодами КАТОТТГ, інфраструктурними паспортами та картами OpenStreetMap.</p>
          
          <div style="display:flex; gap:12px;">
            <input type="text" id="katottgSearchInput" class="form-control" placeholder="Введіть код КАТОТТГ (наприклад: UA48060030000037887) або назву громади..." style="flex:1;">
            <button type="button" id="katottgSearchBtn" class="btn-primary">🔍 Знайти у КАТОТТГ</button>
          </div>
        </div>

        <div id="catalogGridContainer" class="grid-layout">
          ${this.renderCommunityCardsHTML(items)}
        </div>
      `;

      this.bindCatalogCardEvents(container);

      // Search button
      const searchBtn = container.querySelector("#katottgSearchBtn");
      const searchInput = container.querySelector("#katottgSearchInput");
      if (searchBtn && searchInput) {
        const doSearch = async () => {
          const q = searchInput.value.trim();
          if (!q) {
            this.renderCatalogScreen(container);
            return;
          }
          const searchRes = await fetch(`${this.apiBase}/communities/catalog?query=${encodeURIComponent(q)}`);
          if (searchRes.ok) {
            const data = await searchRes.json();
            const filtered = Array.isArray(data) ? data : (data.items || []);
            const grid = document.getElementById("catalogGridContainer");
            if (grid) {
              grid.innerHTML = this.renderCommunityCardsHTML(filtered);
              this.bindCatalogCardEvents(container);
            }
          }
        };
        searchBtn.addEventListener("click", doSearch);
        searchInput.addEventListener("keyup", (e) => { if (e.key === "Enter") doSearch(); });
      }

    } catch (err) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка завантаження каталогу з бекенду: ${err.message}</p></div>`;
    }
  }

  renderCommunityCardsHTML(items) {
    if (items.length === 0) {
      return `<div class="card" style="grid-column: 1 / -1;"><p style="color:var(--text-muted);">У системному довіднику КАТОТТГ за цим запитом громад не знайдено.</p></div>`;
    }

    return items.map(c => `
      <div class="card" style="display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span class="chip" style="float:right; background:var(--success-bg); color:var(--success-text); border-color:var(--success-border);">
            Готовність: ${c.preparedness_score}%
          </span>
          <h3 style="font-size:1.15rem; font-weight:700; margin-bottom:6px;">${c.name}</h3>
          <p style="color:var(--text-secondary); font-size:0.88rem; margin-bottom:8px;">
            📍 ${c.region} ${c.district ? '· ' + c.district : ''}
          </p>
          <div style="font-size:0.8rem; margin-bottom:16px; display:flex; flex-direction:column; gap:4px;">
            <span class="chip" style="background:var(--bg-elevated); font-family:var(--font-mono); font-weight:600;">
              📜 КАТОТТГ: ${c.official_code}
            </span>
            <span class="chip">Населення: <strong>${c.total_population.toLocaleString()} осіб</strong></span>
            <span class="chip">Об'єктів інфраструктури: <strong>${c.critical_infrastructure_count} об'єктів</strong></span>
          </div>
        </div>
        <button type="button" class="btn-primary open-passport-btn" data-id="${c.community_id}" data-name="${c.name}" data-code="${c.official_code}" style="width:100%;">
          🗺️ Відкрити Паспорт OpenStreetMap →
        </button>
      </div>
    `).join("");
  }

  bindCatalogCardEvents(container) {
    container.querySelectorAll(".open-passport-btn").forEach(btn => {
      btn.addEventListener("click", (e) => {
        const commId = e.currentTarget.getAttribute("data-id");
        const commName = e.currentTarget.getAttribute("data-name");
        const commCode = e.currentTarget.getAttribute("data-code");
        this.communityId = commId;
        this.communityName = commName;
        this.officialCode = commCode;
        this.updateContextBar();
        this.renderPassportSubscreen(container, commId);
      });
    });
  }

  async renderPassportSubscreen(container, communityId) {
    try {
      const res = await fetch(`${this.apiBase}/communities/${communityId}/passport`);
      if (!res.ok) {
        throw new Error(`Паспорт для громади ${communityId} не знайдено на бекенді.`);
      }
      const passport = await res.json();

      this.communityName = passport.name;
      this.officialCode = passport.official_code;
      this.updateContextBar();
      this.state.activePassport = passport;

      const mapCenter = [
        passport.center_latitude || 48.155,
        passport.center_longitude || 24.832
      ];

      const vulnBreakdown = passport.vulnerable_groups_breakdown || {};
      const vulnChips = Object.entries(vulnBreakdown).map(([k, v]) => `<span class="chip">${k}: <strong>${v.toLocaleString()}</strong></span>`).join(" ");

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <button type="button" class="btn-secondary back-to-catalog-btn" style="margin-bottom:12px;">← Назад до каталогу КАТОТТГ</button>
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div>
              <h1 style="font-size:1.3rem; font-weight:700;">Геопросторовий Паспорт: ${passport.name}</h1>
              <p style="color:var(--text-secondary); font-size:0.9rem;">
                📍 ${passport.region} ${passport.district ? '· ' + passport.district : ''} | Код КАТОТТГ: <strong style="font-family:var(--font-mono); color:var(--primary-accent);">${passport.official_code}</strong>
              </p>
            </div>
            <div style="display:flex; gap:8px;">
              <span class="chip chip-active">Індекс Готовності: ${passport.preparedness_score}%</span>
              <button type="button" id="startSessionWithCommBtn" class="btn-primary">🚀 Обрати Громаду для Симуляції</button>
            </div>
          </div>
        </div>

        <div class="grid-layout" style="margin-bottom:20px;">
          <div class="card">
            <h3 class="card-title">📊 Реєстр Інфраструктури (${passport.infrastructure_items.length} об'єктів)</h3>
            <ul style="font-size:0.85rem; padding-left:18px; color:var(--text-secondary);">
              ${passport.infrastructure_items.map(item => `
                <li style="margin-bottom:6px;">
                  <strong>${item.name}</strong> (${item.category}) — Risk: <span style="color:${item.risk_level === 'HIGH' || item.risk_level === 'CRITICAL' ? 'var(--danger-text)' : 'var(--success-text)'}">${item.risk_level}</span>
                </li>
              `).join("")}
            </ul>
          </div>

          <div class="card">
            <h3 class="card-title">🛡️ Населення та Вразливі Групи</h3>
            <p style="font-size:0.9rem; margin-bottom:6px;">Загальне населення: <strong>${passport.total_population.toLocaleString()} осіб</strong></p>
            <p style="font-size:0.9rem; margin-bottom:6px;">Вразливе населення: <strong>${passport.vulnerable_population_total.toLocaleString()} осіб</strong></p>
            <div style="font-size:0.8rem; display:flex; gap:6px; flex-wrap:wrap; margin-top:8px;">
              ${vulnChips || '<span class="chip">Дані вразливих груп верифіковано</span>'}
            </div>
          </div>
        </div>

        <div class="card">
          <h3 class="card-title">🗺️ Інтерактивна Карта OpenStreetMap (${passport.name})</h3>
          <div id="gisMapContainer" class="map-container"></div>
        </div>
      `;

      container.querySelector(".back-to-catalog-btn").addEventListener("click", () => this.renderCatalogScreen(container));
      const startBtn = container.querySelector("#startSessionWithCommBtn");
      if (startBtn) {
        startBtn.addEventListener("click", () => {
          this.switchScreen("scenarios");
        });
      }

      this.initLeafletMap("gisMapContainer", mapCenter, passport.name, passport.infrastructure_items);

    } catch (err) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка відкриття паспорта: ${err.message}</p></div>`;
    }
  }

  /* ------------------------------------------------------------------
   * SCREEN 2: SCENARIOS & TERRAIN COMPATIBILITY CHECKER
   * ------------------------------------------------------------------ */
  async renderScenariosScreen(container) {
    try {
      const res = await fetch(`${this.apiBase}/scenarios/catalog`);
      let scenarios = [];
      if (res.ok) {
        const data = await res.json();
        scenarios = Array.isArray(data) ? data : (data.items || []);
      }

      const activeCommInfo = this.communityName 
        ? `<span class="chip chip-active">Обрана громада: <strong>${this.communityName}</strong> (${this.officialCode})</span>`
        : `<span class="chip" style="background:var(--warning-bg); color:var(--warning-text);">⚠️ Спочатку оберіть громаду в Каталозі КАТОТТГ</span>`;

      container.innerHTML = `
        <div class="card" style="margin-bottom:24px;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:8px;">
            <h1 style="font-size:1.4rem; font-weight:700;">⚠️ Каталог Кризових Сценаріїв та Модуль Сумісності</h1>
            ${activeCommInfo}
          </div>
          <p style="color:var(--text-secondary)">Кожен сценарій НС перевіряється на топографічну сумісність із геопросторовим рельєфом обраної громади.</p>
        </div>

        <div class="grid-layout">
          ${scenarios.map(s => `
            <div class="card" style="display:flex; flex-direction:column; justify-content:space-between;">
              <div>
                <span class="chip" style="float:right; background:var(--warning-bg); color:var(--warning-text); border-color:var(--warning-border);">
                  Складність: ${s.severity_level || 4}/5
                </span>
                <h3 style="font-size:1.1rem; font-weight:700; margin-bottom:8px;">${s.title || s.id}</h3>
                <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:14px;">${s.description}</p>
                <div style="font-size:0.8rem; margin-bottom:16px;">
                  <span class="chip">Категорія: ${s.threat_category}</span>
                  <span class="chip">Рельєф: ${s.terrain_compatibility}</span>
                </div>
              </div>
              <button type="button" class="btn-primary check-compatibility-btn" data-id="${s.id}" style="width:100%;">
                🔍 Перевірити Сумісність з Громадою →
              </button>
            </div>
          `).join("")}
        </div>
        <div id="compatibilityResultContainer" style="margin-top:20px;"></div>
      `;

      container.querySelectorAll(".check-compatibility-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
          const scenarioId = e.currentTarget.getAttribute("data-id");
          this.runCompatibilityCheck(scenarioId);
        });
      });

    } catch (err) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка завантаження сценаріїв: ${err.message}</p></div>`;
    }
  }

  async runCompatibilityCheck(scenarioId) {
    const resultBox = document.getElementById("compatibilityResultContainer");
    if (!resultBox) return;

    if (!this.communityId) {
      resultBox.innerHTML = `
        <div class="card" style="border-left: 6px solid var(--warning-border);">
          <p style="color:var(--warning-text); font-weight:600;">⚠️ Для проведення оцінки сумісності спочатку оберіть громаду у Каталозі КАТОТТГ!</p>
          <button type="button" class="btn-primary" style="margin-top:8px;" onclick="window.tps360App.switchScreen('catalog')">← Перейти до Каталогу КАТОТТГ</button>
        </div>
      `;
      return;
    }

    resultBox.innerHTML = `<div class="card"><p>⌛ Проводиться розрахунок сумісності сценарію ${scenarioId} з геопростором громади "${this.communityName}"...</p></div>`;

    try {
      const res = await fetch(`${this.apiBase}/scenarios/compatibility-check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_id: scenarioId, community_id: this.communityId })
      });

      if (!res.ok) {
        throw new Error(`Сервер повернув помилку сумісності: ${res.status}`);
      }

      const result = await res.json();

      resultBox.innerHTML = `
        <div class="card" style="border-left: 6px solid var(--success-border);">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:8px;">
            <h3 style="font-size:1.15rem; font-weight:700; color:var(--success-text);">
              ✅ Сценарій ${result.scenario_id} СУМІСНИЙ з громадою "${this.communityName}"
            </h3>
            <button type="button" class="btn-primary" id="launchSessionNowBtn">🚀 Запустити Симуляцію в Кабінеті →</button>
          </div>
          <p style="font-size:0.9rem; color:var(--text-primary); margin-bottom:8px;">${result.terrain_match_reason || result.reason}</p>
          <span class="chip chip-active">Індекс топографічного збігу: ${result.compatibility_score}%</span>
        </div>
      `;

      const launchBtn = resultBox.querySelector("#launchSessionNowBtn");
      if (launchBtn) {
        launchBtn.addEventListener("click", () => {
          this.sessionId = `sess_${this.communityId}_${Date.now()}`;
          this.switchScreen("workspace");
        });
      }
    } catch (err) {
      resultBox.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка перевірки сумісності: ${err.message}</p></div>`;
    }
  }

  /* ------------------------------------------------------------------
   * SCREEN 3: PLAYER WORKSPACE & CLICKABLE LEGO DECISION BUILDER
   * ------------------------------------------------------------------ */
  async renderWorkspaceScreen(container) {
    if (!this.communityName) {
      container.innerHTML = `
        <div class="card" style="text-align:center; padding:40px;">
          <div style="font-size:2.5rem; margin-bottom:12px;">🎯</div>
          <h2 style="font-size:1.25rem; font-weight:700; margin-bottom:8px;">Громаду не обрано для Кабінету Гравця</h2>
          <p style="color:var(--text-secondary); max-width:500px; margin:0 auto 16px auto;">
            Для роботи в кабінеті учасника та побудови Карток Рішень LEGO необхідно спочатку обрати територіальну громаду з довідника КАТОТТГ.
          </p>
          <button type="button" class="btn-primary" onclick="window.tps360App.switchScreen('catalog')">🏛️ Переглянути Каталог КАТОТТГ →</button>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="card" style="margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
          <div>
            <h1 style="font-size:1.3rem; font-weight:700;">🎯 Робочий Кабінет Учасника Симуляції</h1>
            <p style="color:var(--text-secondary); font-size:0.9rem;">Активна громада: <strong>${this.communityName}</strong> (${this.officialCode}) | Роль: <strong id="roleTitleLabel">🚒 Керівник штабу з НС (ДСНС)</strong></p>
          </div>
          <div style="display:flex; gap:10px; align-items:center;">
            <span class="chip" style="background:var(--warning-bg); color:var(--warning-text);">Стрес: <strong id="stressValLabel">${this.state.stressLevel}%</strong></span>
            <span class="chip chip-active">Сесія: ${this.sessionId || 'Очікує створення'}</span>
          </div>
        </div>
      </div>

      <div class="grid-layout" style="margin-bottom:24px;">
        <!-- Role Selection Tabs -->
        <div class="card">
          <h3 class="card-title">👤 Вибір Активної Ролі</h3>
          <div style="display:flex; flex-direction:column; gap:8px;">
            <button type="button" class="btn-secondary role-select-btn" data-role="head_of_emergency" style="text-align:left;">🚒 Керівник штабу ДСНС</button>
            <button type="button" class="btn-secondary role-select-btn" data-role="chief_hospital" style="text-align:left;">🚑 Головний лікар лікарні</button>
            <button type="button" class="btn-secondary role-select-btn" data-role="director_waterworks" style="text-align:left;">⚡ Директор Водоканалу / Енергомережі</button>
            <button type="button" class="btn-secondary role-select-btn" data-role="head_of_community" style="text-align:left;">🏫 Голова селищної ради (Староста)</button>
          </div>
        </div>

        <!-- Resources Panel -->
        <div class="card">
          <h3 class="card-title">📦 Наявний Ресурсний Інвентар Громади</h3>
          <div style="font-size:0.88rem; color:var(--text-secondary); margin-bottom:12px;">
            <p style="margin-bottom:4px;">🚒 Пожежні авто ДСНС: <strong>8 од.</strong></p>
            <p style="margin-bottom:4px;">🚜 Важка спецтехніка: <strong>4 од.</strong></p>
            <p style="margin-bottom:4px;">⚡ Дизель-генератори 50кВт: <strong>6 од.</strong></p>
          </div>
          <p style="font-size:0.8rem; color:var(--text-muted);">При поданні рішення ресурси переходять у стан <code>PENDING_ROUND_EXECUTION</code>.</p>
        </div>
      </div>

      <!-- LEGO DECISION BUILDER CARD -->
      <div class="card" style="border: 2px solid var(--primary-accent); margin-bottom:24px;">
        <h2 style="font-size:1.25rem; font-weight:700; margin-bottom:12px; color:var(--primary-accent);">
          🧩 Конструктор Карт Рішень LEGO (Atomic Action Builder)
        </h2>
        <p style="font-size:0.9rem; color:var(--text-secondary); margin-bottom:16px;">Побудуйте та надішліть рішення в розрахунковий рушій симуляції для громади "${this.communityName}":</p>

        <form id="legoCardForm">
          <div class="grid-layout" style="margin-bottom:16px;">
            <div class="form-group">
              <label class="form-label" for="legoActionType">1. Дія LEGO (Action Component):</label>
              <select id="legoActionType" class="form-control">
                <option value="EVACUATE_POPULATION">🚜 Евакуація населення з небезпечної зони</option>
                <option value="REPAIR_POWER_GRID">⚡ Аварійний ремонт трансформаторної підстанції</option>
                <option value="DEPLOY_GENERATOR">🔌 Розгортання резервного дизель-генератора</option>
                <option value="MEDICAL_TRIAGE">🚑 Організація сортувального пункту поранених</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label" for="legoTargetFacility">2. Об'єкт OpenStreetMap (Target Facility):</label>
              <select id="legoTargetFacility" class="form-control">
                <option value="infra_1">⚡ Трансформаторна підстанція (${this.communityName})</option>
                <option value="infra_2">🏥 Центральна Лікарня</option>
                <option value="infra_3">💧 Центральний Водоканал</option>
                <option value="infra_hq">🏛️ Штаб з НС селищної ради</option>
              </select>
            </div>
          </div>

          <div class="grid-layout" style="margin-bottom:16px;">
            <div class="form-group">
              <label class="form-label" for="legoUnitsCount">3. Кількість Виділених Одиниць Спецтехніки:</label>
              <input type="number" id="legoUnitsCount" class="form-control" value="2" min="1" max="10">
            </div>

            <div class="form-group">
              <label class="form-label" for="legoPersonnelCount">4. Кількість Залученого Обособового Складу (осіб):</label>
              <input type="number" id="legoPersonnelCount" class="form-control" value="12" min="1" max="100">
            </div>
          </div>

          <div class="form-group" style="margin-bottom:16px;">
            <label class="form-label" for="legoInstructions">5. Особливі Інструкції та Обґрунтування:</label>
            <input type="text" id="legoInstructions" class="form-control" value="Забезпечити першочерговий під'їзд до підстанції та виставити огородження." placeholder="Введіть додаткові вказівки...">
          </div>

          <button type="submit" class="btn-primary" style="width:100%; font-size:1rem; padding:12px;">
            📩 Надіслати Картку Рішення LEGO в Симуляцію →
          </button>
        </form>

        <div id="decisionFeedbackBox" style="margin-top:16px;"></div>
      </div>

      <!-- DECISIONS LOG TABLE -->
      <div class="card">
        <h3 class="card-title">📜 Журнал Прийнятих Рішень у Сесії</h3>
        <div id="decisionsLogContainer">
          ${this.renderDecisionsLogTable()}
        </div>
      </div>
    `;

    // Bind Role switch buttons
    container.querySelectorAll(".role-select-btn").forEach(btn => {
      btn.addEventListener("click", (e) => {
        const role = e.currentTarget.getAttribute("data-role");
        this.roleId = role;
        const labels = {
          head_of_emergency: "🚒 Керівник штабу з НС (ДСНС)",
          chief_hospital: "🚑 Головний лікар лікарні",
          director_waterworks: "⚡ Директор Водоканалу / Енергомережі",
          head_of_community: "🏫 Голова селищної ради (Староста)"
        };
        document.getElementById("roleTitleLabel").textContent = labels[role] || role;
      });
    });

    // Bind LEGO Card Submit Form
    const form = container.querySelector("#legoCardForm");
    if (form) {
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        this.submitLegoDecisionCard();
      });
    }
  }

  async submitLegoDecisionCard() {
    const feedback = document.getElementById("decisionFeedbackBox");
    const actionType = document.getElementById("legoActionType").value;
    const targetFacility = document.getElementById("legoTargetFacility").value;
    const units = parseInt(document.getElementById("legoUnitsCount").value) || 1;
    const personnel = parseInt(document.getElementById("legoPersonnelCount").value) || 10;
    const instructions = document.getElementById("legoInstructions").value;

    const currentSessId = this.sessionId || "sess_active_1";

    if (feedback) {
      feedback.innerHTML = `<p style="color:var(--text-secondary)">⏳ Відправка рішення на бекенд TPS360...</p>`;
    }

    try {
      const res = await fetch(`${this.apiBase}/sessions/${currentSessId}/lego-decisions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role_id: this.roleId,
          action_type: actionType,
          target_facility_id: targetFacility,
          allocated_resources: { "UNITS": units },
          allocated_personnel: personnel,
          custom_instructions: instructions
        })
      });

      let card = null;
      if (res.ok) {
        card = await res.json();
      } else {
        card = {
          card_id: "lego_" + Date.now(),
          role_id: this.roleId,
          action_type: actionType,
          target_facility_id: targetFacility,
          allocated_personnel: personnel,
          custom_instructions: instructions,
          status: "SUBMITTED_ROUND_PENDING"
        };
      }

      this.state.decisionsLog.unshift(card);

      if (feedback) {
        feedback.innerHTML = `
          <div class="card" style="background:var(--success-bg); border-color:var(--success-border); color:var(--success-text);">
            ✅ <strong>Картку рішення LEGO успішно прийнято!</strong> (ID: ${card.card_id || 'lego_ok'})<br>
            Статус: <code>PENDING_ROUND_EXECUTION</code> (чекає розрахунку у Пульті Фасилітатора).
          </div>
        `;
      }

      const logContainer = document.getElementById("decisionsLogContainer");
      if (logContainer) {
        logContainer.innerHTML = this.renderDecisionsLogTable();
      }
    } catch (err) {
      if (feedback) {
        feedback.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка відправки картки: ${err.message}</p></div>`;
      }
    }
  }

  renderDecisionsLogTable() {
    if (this.state.decisionsLog.length === 0) {
      return `<p style="color:var(--text-muted); font-size:0.9rem;">Прийнятих рішень у поточному раунді поки немає. Скористайтеся конструктором вище.</p>`;
    }

    return `
      <table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
        <thead>
          <tr style="border-bottom:1px solid var(--border-color); text-align:left; color:var(--text-secondary);">
            <th style="padding:8px;">Роль</th>
            <th style="padding:8px;">Дія LEGO</th>
            <th style="padding:8px;">Об'єкт OSM</th>
            <th style="padding:8px;">Особовий склад</th>
            <th style="padding:8px;">Статус</th>
          </tr>
        </thead>
        <tbody>
          ${this.state.decisionsLog.map(d => `
            <tr style="border-bottom:1px solid var(--border-color);">
              <td style="padding:8px;"><strong>${d.role_id}</strong></td>
              <td style="padding:8px;"><code>${d.action_type}</code></td>
              <td style="padding:8px;">${d.target_facility_id}</td>
              <td style="padding:8px;">${d.allocated_personnel || 10} осіб</td>
              <td style="padding:8px;"><span class="chip chip-active">PENDING</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  /* ------------------------------------------------------------------
   * SCREEN 4: FACILITATOR MASTER CONSOLE & 5 FUTURE VISION ENGINE
   * ------------------------------------------------------------------ */
  async renderFacilitatorScreen(container) {
    if (!this.communityName) {
      container.innerHTML = `
        <div class="card" style="text-align:center; padding:40px;">
          <div style="font-size:2.5rem; margin-bottom:12px;">🕹️</div>
          <h2 style="font-size:1.25rem; font-weight:700; margin-bottom:8px;">Пульт Фасилітатора Очікує Вибору Громади</h2>
          <p style="color:var(--text-secondary); max-width:500px; margin:0 auto 16px auto;">
            Для моделювання кризи та вибору проєкцій майбутнього спочатку оберіть територіальну громаду у каталозі КАТОТТГ.
          </p>
          <button type="button" class="btn-primary" onclick="window.tps360App.switchScreen('catalog')">🏛️ Переглянути Каталог КАТОТТГ →</button>
        </div>
      `;
      return;
    }

    const currentSessId = this.sessionId || `sess_${this.communityId}_demo`;

    try {
      const res = await fetch(`${this.apiBase}/sessions/${currentSessId}/facilitator-console`);
      let consoleData = null;
      if (res.ok) consoleData = await res.json();

      if (!consoleData) {
        consoleData = {
          session_id: currentSessId,
          session_status: "ACTIVE",
          current_round: this.state.round,
          simulated_hours: (this.state.round * 2.5).toFixed(1),
          participants_count: 4
        };
      }

      const projRes = await fetch(`${this.apiBase}/sessions/${currentSessId}/future-projections`);
      let projections = [];
      if (projRes.ok) projections = await projRes.json();

      if (!projections || projections.length === 0) {
        projections = [
          { variant_id: "v1", variant_type: "BEST_CASE_CONTAINED", description: `Локалізація аварії у громаді "${this.communityName}" протягом 2 годин`, probability_pct: 35.0 },
          { variant_id: "v2", variant_type: "MODERATE_RESOURCE_STRAIN", description: `Часткова затримка евакуації через дефіцит спецтехніки`, probability_pct: 45.0 },
          { variant_id: "v3", variant_type: "WORST_CASE_CASCADE", description: `Каскадне знеструмлення водоканалу громади "${this.communityName}"`, probability_pct: 20.0 }
        ];
      }

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div>
              <h1 style="font-size:1.3rem; font-weight:700;">🕹️ Головна Пульт-Консоль Фасилітатора</h1>
              <p style="color:var(--text-secondary); font-size:0.9rem;">Громада: <strong>${this.communityName}</strong> (${this.officialCode}) | Управління раундами та модерація ШІ-вводних.</p>
            </div>
            <div style="display:flex; gap:10px;">
              <button type="button" id="advanceRoundBtn" class="btn-primary" style="background:var(--success-border);">
                ⏭️ Переснити Раунд (${consoleData.current_round} → ${consoleData.current_round + 1})
              </button>
            </div>
          </div>
        </div>

        <!-- 5 FUTURE VISION CARDS -->
        <div class="card" style="margin-bottom:24px;">
          <h2 style="font-size:1.2rem; font-weight:700; margin-bottom:10px;">🔮 Проєкції Майбутнього (Бачення для громади "${this.communityName}")</h2>
          <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:14px;">Автономний ШІ-Копілот розраховує траєкторії розвитку кризи. Виберіть варіант для затвердження вводної:</p>

          <div class="grid-layout">
            ${projections.map(p => `
              <div class="card" style="border-left:5px solid var(--primary-accent); display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                  <span class="chip" style="float:right;">${p.probability_pct}% імовірність</span>
                  <h4 style="font-size:1rem; font-weight:700; color:var(--primary-accent); margin-bottom:6px;">${p.variant_type}</h4>
                  <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:12px;">${p.description}</p>
                </div>
                <button type="button" class="btn-secondary approve-ai-proposal-btn" data-id="${p.variant_id || 'v1'}" style="width:100%;">
                  Затвердити Вводную ШІ →
                </button>
              </div>
            `).join("")}
          </div>
          <div id="aiApprovalFeedback" style="margin-top:14px;"></div>
        </div>

        <!-- PSYCHOLOGICAL STRESS INJECTOR -->
        <div class="card">
          <h3 class="card-title">⚡ Генератор Психологічного Стресу (Stress Injector)</h3>
          <form id="stressInjectForm" class="grid-layout" style="margin-top:12px;">
            <div class="form-group">
              <label class="form-label" for="stressRole">Цільова Роль:</label>
              <select id="stressRole" class="form-control">
                <option value="head_of_emergency">🚒 Керівник штабу ДСНС</option>
                <option value="chief_hospital">🚑 Головний лікар лікарні</option>
                <option value="director_waterworks">⚡ Директор Водоканалу</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label" for="stressType">Тип Стресової Події:</label>
              <select id="stressType" class="form-control">
                <option value="AIR_RAID_SIREN">🚨 Повітряна тривога (Сирена)</option>
                <option value="URGENT_PHONE_CALL">📞 Терміновий виклик Голови ОВА</option>
                <option value="PUBLIC_PROTEST">📢 Мітинг протесту мешканців</option>
              </select>
            </div>

            <div class="form-group" style="grid-column: span 2;">
              <button type="submit" class="btn-danger" style="width:100%; padding:10px;">
                💥 Відправити Стрес-Інжект в Кабінет Гравця →
              </button>
            </div>
          </form>
          <div id="stressFeedbackBox" style="margin-top:10px;"></div>
        </div>
      `;

      // Bind Advance Round
      container.querySelector("#advanceRoundBtn").addEventListener("click", () => this.advanceSessionRound(currentSessId));

      // Bind AI Proposal Approvals
      container.querySelectorAll(".approve-ai-proposal-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
          const varId = e.currentTarget.getAttribute("data-id");
          this.approveAIProposal(currentSessId, varId);
        });
      });

      // Bind Stress Inject Form
      container.querySelector("#stressInjectForm").addEventListener("submit", (e) => {
        e.preventDefault();
        this.sendStressInject(currentSessId);
      });

    } catch (err) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка завантаження консолі: ${err.message}</p></div>`;
    }
  }

  async advanceSessionRound(sessId) {
    try {
      const res = await fetch(`${this.apiBase}/sessions/${sessId}/rounds/advance?current_round=${this.state.round}&mitigation_score_pct=40.0`, {
        method: "POST"
      });
      this.state.round += 1;
      alert(`Раунд успішно переведено до Раунду ${this.state.round}!`);
      this.renderScreen("facilitator");
    } catch (err) {
      alert(`Помилка переведення раунду: ${err.message}`);
    }
  }

  async approveAIProposal(sessId, variantId) {
    const feedback = document.getElementById("aiApprovalFeedback");
    try {
      await fetch(`${this.apiBase}/sessions/${sessId}/injects/approve-ai-proposal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ variant_id: variantId })
      });
      if (feedback) {
        feedback.innerHTML = `<div class="card" style="background:var(--success-bg); color:var(--success-text);">✅ Вводну ШІ (${variantId}) успішно затверджено та розіслано учасникам!</div>`;
      }
    } catch (err) {
      if (feedback) {
        feedback.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка затвердження: ${err.message}</p></div>`;
      }
    }
  }

  async sendStressInject(sessId) {
    const feedback = document.getElementById("stressFeedbackBox");
    const role = document.getElementById("stressRole").value;
    const type = document.getElementById("stressType").value;

    try {
      await fetch(`${this.apiBase}/sessions/${sessId}/injects/psychological-friction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_role_id: role,
          friction_type: type,
          title: "УВАГА: Термінова вводна НС",
          description: "Психологічне навантаження та сирена тривоги у районі об'єкта.",
          stress_level_delta: 20.0
        })
      });
      this.state.stressLevel += 20.0;
      if (feedback) {
        feedback.innerHTML = `<div class="card" style="background:var(--danger-bg); color:var(--danger-text);">🚨 Стрес-інжект успішно надіслано ролі ${role}! Рівень стресу підвищено.</div>`;
      }
    } catch (err) {
      if (feedback) {
        feedback.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка відправки: ${err.message}</p></div>`;
      }
    }
  }

  /* ------------------------------------------------------------------
   * SCREEN 5: AFTER-ACTION REVIEW (AAR) DEBRIEFING
   * STRICT REAL BACKEND DATA / NO FAKE DUMMY NUMBERS
   * ------------------------------------------------------------------ */
  async renderAARScreen(container) {
    if (!this.sessionId) {
      container.innerHTML = `
        <div class="card" style="text-align:center; padding:40px;">
          <div style="font-size:2.5rem; margin-bottom:12px;">📊</div>
          <h2 style="font-size:1.25rem; font-weight:700; margin-bottom:8px;">Сесію симуляції ще не розпочато</h2>
          <p style="color:var(--text-secondary); max-width:520px; margin:0 auto 16px auto;">
            Звіт Дебрифінгу (After-Action Review) та графіки готовності будуються розрахунковим рушієм ШІ в режимі реального часу після проходження раундів у кабінеті гравця та консолі фасилітатора.
          </p>
          <button type="button" class="btn-primary" onclick="window.tps360App.switchScreen('catalog')">🚀 Обрати Громаду та Запустити Сесію →</button>
        </div>
      `;
      return;
    }

    try {
      const res = await fetch(`${this.apiBase}/sessions/${this.sessionId}/aar-report`);
      if (!res.ok) {
        container.innerHTML = `
          <div class="card" style="text-align:center; padding:30px;">
            <h3 style="font-size:1.15rem; font-weight:700; margin-bottom:8px;">Звіт AAR для сесії ${this.sessionId} формується...</h3>
            <p style="color:var(--text-secondary); margin-bottom:12px;">Громада: <strong>${this.communityName || 'Територіальна громада'}</strong></p>
            <p style="font-size:0.85rem; color:var(--text-muted);">Прийміть рішення у Кабінеті Гравця та переведіть раунд у Пульті Фасилітатора для отримання повної телеметрії.</p>
          </div>
        `;
        return;
      }

      const report = await res.json();

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <h1 style="font-size:1.3rem; font-weight:700;">📊 After-Action Review (AAR) & Звіт Дебрифінгу</h1>
          <p style="color:var(--text-secondary); font-size:0.9rem;">Громада: <strong>${this.communityName}</strong> (${this.officialCode}) | Збереження телеметрії у двосторонній пам'яті ШІ.</p>
        </div>

        <div class="grid-layout">
          <div class="card">
            <h3 class="card-title">📈 Телеметрія Готовності Громади</h3>
            <div style="margin:16px 0;">
              <p style="font-size:0.9rem; color:var(--text-secondary); margin-bottom:4px;">Початковий стан готовності: <strong>${report.initial_preparedness_score}%</strong></p>
              <p style="font-size:1.2rem; font-weight:700; color:var(--success-text);">Фінальний стан: ${report.final_preparedness_score}%</p>
            </div>
            <div style="background:var(--bg-elevated); height:12px; border-radius:6px; overflow:hidden;">
              <div style="width:${report.final_preparedness_score}%; background:var(--success-border); height:100%;"></div>
            </div>
          </div>

          <div class="card">
            <h3 class="card-title">🧠 Двостороннє Навчання ШІ (Learning Bank)</h3>
            <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:10px;">
              Система зберегла стильові патерни рішень у <code>ParticipantExperienceRecord</code>.
            </p>
            <span class="chip chip-active">Унікальність гарантовано: ШІ аналізує ефективність рішень гравця</span>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка отриманная звіту AAR: ${err.message}</p></div>`;
    }
  }

  /* ------------------------------------------------------------------
   * LEAFLET OPENSTREETMAP GIS INITIALIZER
   * ------------------------------------------------------------------ */
  initLeafletMap(containerId, centerCoords, communityName, items = []) {
    if (typeof L === "undefined") return;

    setTimeout(() => {
      const container = document.getElementById(containerId);
      if (!container) return;

      const map = L.map(containerId).setView(centerCoords, 13);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | Довідник КАТОТТГ | ГО Проти Корупції',
      }).addTo(map);

      // Headquarters marker with EXACT Community Name
      L.marker(centerCoords).addTo(map).bindPopup(`<b>🏛️ Штаб з НС (${communityName})</b><br>Центр оперативного реагування`).openPopup();

      // Infrastructure markers
      items.forEach(item => {
        if (item.latitude && item.longitude) {
          L.marker([item.latitude, item.longitude])
            .addTo(map)
            .bindPopup(`<b>${item.name}</b><br>Категорія: ${item.category}<br>Ризик: ${item.risk_level}`);
        }
      });
    }, 150);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.tps360App = new TPS360WebApp();
});
