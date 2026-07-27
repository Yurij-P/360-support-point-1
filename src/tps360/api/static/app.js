/**
 * TPS360 Single Page Web Application Controller
 * Dynamic REST API client integration, Leaflet GIS mapping, Lego decision building & Facilitator master console.
 */

class TPS360WebApp {
  constructor() {
    this.currentScreen = "catalog";
    this.sessionId = "sess_demo_99";
    this.communityId = "verkhovyna";
    this.roleId = "head_of_emergency";
    this.apiBase = "/api/v1";
    
    this.init();
  }

  init() {
    this.bindEvents();
    this.renderScreen(this.currentScreen);
  }

  bindEvents() {
    // Navigation tabs
    document.querySelectorAll(".nav-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const screen = e.currentTarget.getAttribute("data-screen");
        this.switchScreen(screen);
      });
    });

    // Theme toggle
    const themeBtn = document.getElementById("themeToggleBtn");
    if (themeBtn) {
      themeBtn.addEventListener("click", () => {
        const currentTheme = document.documentElement.getAttribute("data-theme");
        const nextTheme = currentTheme === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", nextTheme);
        themeBtn.querySelector(".theme-icon").textContent = nextTheme === "dark" ? "☀️" : "🌙";
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

    main.innerHTML = `<div class="card"><p>Завантаження даних для екрана ${screen}...</p></div>`;

    switch (screen) {
      case "catalog":
        await this.renderCatalog(main);
        break;
      case "scenarios":
        await this.renderScenarios(main);
        break;
      case "facilitator":
        await this.renderFacilitatorConsole(main);
        break;
      case "workspace":
        await this.renderPlayerWorkspace(main);
        break;
      case "aar":
        await this.renderAARDebriefing(main);
        break;
      default:
        await this.renderCatalog(main);
    }
  }

  async renderCatalog(container) {
    try {
      const res = await fetch(`${this.apiBase}/communities/catalog`);
      const catalog = res.ok ? await res.json() : [];

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <h1 class="card-title">Каталог Територіальних Громад України</h1>
          <p style="color:var(--text-secondary);">Виберіть громаду для перегляду її геопросторового паспорта OpenStreetMap та наявного інвентаря критичної інфраструктури.</p>
        </div>
        <div class="grid-layout">
          ${catalog.map((c) => `
            <div class="card">
              <h3 style="font-size:1.1rem; font-weight:600;">${c.name}</h3>
              <p style="color:var(--text-secondary); font-size:0.9rem;">${c.oblast} · Населення: ${c.population.toLocaleString()}</p>
              <div style="margin:12px 0; font-size:0.85rem;">
                <span class="chip">Повнота даних: ${c.data_completeness_pct}%</span>
                <span class="chip">Населених пунктів: ${c.settlements_count}</span>
              </div>
              <button class="nav-btn active select-comm-btn" data-id="${c.id}" style="width:100%;">Відкрити Паспорт Громади →</button>
            </div>
          `).join("")}
        </div>
      `;

      container.querySelectorAll(".select-comm-btn").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          this.communityId = e.currentTarget.getAttribute("data-id");
          this.renderPassport(container, this.communityId);
        });
      });
    } catch (e) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка завантаження каталогу: ${e.message}</p></div>`;
    }
  }

  async renderPassport(container, communityId) {
    try {
      const res = await fetch(`${this.apiBase}/communities/${communityId}/passport`);
      const passport = res.ok ? await res.json() : {};

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <button class="nav-btn back-btn" style="margin-bottom:10px;">← Назад до каталогу</button>
          <h1 class="card-title">Паспорт Громади: ${passport.name || communityId}</h1>
          <p style="color:var(--text-secondary)">Область: ${passport.oblast || "Миколаївська"} | Населення: ${(passport.population || 16633).toLocaleString()}</p>
        </div>
        
        <div class="card" style="margin-bottom:20px;">
          <h3 class="card-title">Інтерактивна Карта OpenStreetMap (GIS Engine)</h3>
          <div id="gisMap" class="map-container"></div>
        </div>
      `;

      container.querySelector(".back-btn").addEventListener("click", () => this.renderCatalog(container));
      this.initLeafletMap("gisMap", [48.15, 24.83]);
    } catch (e) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка завантаження паспорта: ${e.message}</p></div>`;
    }
  }

  async renderScenarios(container) {
    container.innerHTML = `
      <div class="card">
        <h1 class="card-title">Каталог Кризових Сценаріїв</h1>
        <p style="color:var(--text-secondary)">Оцінка сумісності сценаріїв НС за рельєфом (гірський рельєф/Верховина vs рівнинний степ/Широке, близькості АЕС) та топографією громади.</p>
        <div class="grid-layout" style="margin-top:20px;">
          <div class="card">
            <h3>scen_landslide_v1</h3>
            <p style="color:var(--text-secondary)">Зсув ґрунту внаслідок злив (Сумісність: Гірська зона Верховини)</p>
          </div>
          <div class="card">
            <h3>scen_blackout_dne_v1</h3>
            <p style="color:var(--text-secondary)">Пошкодження енергопідстанції та блекаут (Сумісність: Універсальна)</p>
          </div>
        </div>
      </div>
    `;
  }

  async renderFacilitatorConsole(container) {
    try {
      const res = await fetch(`${this.apiBase}/sessions/${this.sessionId}/facilitator-console`);
      const consoleData = res.ok ? await res.json() : {};

      const projRes = await fetch(`${this.apiBase}/sessions/${this.sessionId}/future-projections`);
      const projections = projRes.ok ? await projRes.json() : [];

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <h1 class="card-title">Головна Пульт-Консоль Фасилітатора</h1>
          <p style="color:var(--text-secondary)">Статус сесії: <strong>${consoleData.session_status || "ACTIVE"}</strong> | Раунд: ${consoleData.current_round || 1} (${consoleData.simulated_hours || 1.5} год)</p>
        </div>

        <div class="card" style="margin-bottom:20px;">
          <h3 class="card-title">🔮 5 Проєкцій Майбутнього (Бачення на 1 Раунд Уперед)</h3>
          <div class="grid-layout">
            ${projections.map((p) => `
              <div class="card" style="border-left:4px solid var(--primary-accent);">
                <h4 style="font-size:1rem; font-weight:600;">${p.variant_type}</h4>
                <p style="font-size:0.85rem; color:var(--text-secondary); margin:6px 0;">${p.description}</p>
                <span class="chip">Імовірність: ${p.probability_pct}%</span>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка завантаження консолі: ${e.message}</p></div>`;
    }
  }

  async renderPlayerWorkspace(container) {
    try {
      const res = await fetch(`${this.apiBase}/sessions/${this.sessionId}/role-workspace?role_id=${this.roleId}`);
      const ws = res.ok ? await res.json() : {};

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <h1 class="card-title">Робочий Кабінет Ролі: ${ws.role_title || "Керівник штабу з НС"}</h1>
          <p style="color:var(--text-secondary)">Індекс когнітивного стресу: <strong>${ws.cognitive_stress_level_pct || 0}%</strong> | Рівень спроможності: <strong>${ws.capability_score || 100}%</strong></p>
        </div>

        <div class="grid-layout">
          <div class="card">
            <h3 class="card-title">📦 Інвентар Зарезервованих Ресурсів</h3>
            <p style="font-size:0.9rem; color:var(--text-secondary);">Доступно 100% залучення ресурсів за 1 раунд під блокування PENDING_ROUND_EXECUTION.</p>
          </div>

          <div class="card">
            <h3 class="card-title">🧩 Відкритий Конструктор Рішень LEGO</h3>
            <p style="font-size:0.9rem; color:var(--text-secondary);">Збирання картки з кубиків дій, об'єктів OSM та виділення сил.</p>
          </div>
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка завантаження кабінету: ${e.message}</p></div>`;
    }
  }

  async renderAARDebriefing(container) {
    try {
      const res = await fetch(`${this.apiBase}/sessions/${this.sessionId}/aar-report`);
      const report = res.ok ? await res.json() : {};

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <h1 class="card-title">After-Action Review (AAR) & Звіт Дебрифінгу</h1>
          <p style="color:var(--text-secondary)">Сесія: ${report.session_id || this.sessionId} | Статус: <strong>${report.final_status || "COMPLETED_SUCCESS"}</strong></p>
        </div>

        <div class="grid-layout">
          <div class="card">
            <h3 class="card-title">📊 Індекс Готовності Громади</h3>
            <p style="font-size:1.2rem; font-weight:700; color:var(--success-text);">Початковий: ${report.initial_preparedness_score || 68.5}% → Фінальний: ${report.final_preparedness_score || 92.0}%</p>
          </div>

          <div class="card">
            <h3 class="card-title">🧠 Двостороннє Навчання ШІ</h3>
            <p style="font-size:0.85rem; color:var(--text-secondary);">ШІ засвоїв стиль рішень гравця і не повторюватиме цей сценарій у наступних іграх.</p>
          </div>
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка завантаження AAR: ${e.message}</p></div>`;
    }
  }

  initLeafletMap(containerId, centerCoords) {
    if (typeof L === "undefined") return;

    setTimeout(() => {
      const map = L.map(containerId).setView(centerCoords, 13);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);

      L.marker(centerCoords).addTo(map).bindPopup("<b>Центр громади (Верховина)</b><br>Штаб з НС").openPopup();
    }, 100);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.tps360App = new TPS360WebApp();
});
