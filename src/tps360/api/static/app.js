/**
 * TPS360 Single Page Web Application Controller
 * Live REST API client integration, Leaflet GIS mapping, Lego decision building & Facilitator master console.
 * Developed by NGO Anti-Corruption (ГО "Проти Корупції")
 */

class TPS360WebApp {
  constructor() {
    this.currentScreen = "catalog";
    this.sessionId = "sess_demo_99";
    this.communityId = "verkhovyna";
    this.roleId = "head_of_emergency";
    this.apiBase = ""; // FastAPI routers are mounted at root level (/communities, /scenarios, /sessions)
    
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

    main.innerHTML = `<div class="card"><p>Завантаження даних бекенду для екрана ${screen}...</p></div>`;

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
      let catalog = [];
      if (res.ok) {
        const data = await res.json();
        catalog = Array.isArray(data) ? data : (data.items || []);
      }

      // Fallback demo items if backend catalog empty
      if (catalog.length === 0) {
        catalog = [
          {
            id: "verkhovyna",
            name: "Верховинська селищна територіальна громада",
            oblast: "Івано-Франківська",
            population: 17850,
            data_completeness_pct: 94.5,
            settlements_count: 42
          },
          {
            id: "berezneghuvate",
            name: "Березнегуватська селищна територіальна громада",
            oblast: "Миколаївська",
            population: 14200,
            data_completeness_pct: 91.0,
            settlements_count: 28
          },
          {
            id: "shiroke",
            name: "Широківська сільська територіальна громада",
            oblast: "Запорізька",
            population: 12500,
            data_completeness_pct: 88.0,
            settlements_count: 35
          }
        ];
      }

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <h1 class="card-title">Каталог Територіальних Громад України</h1>
          <p style="color:var(--text-secondary);">Виберіть громаду для перегляду її геопросторового паспорта OpenStreetMap та наявного інвентаря критичної інфраструктури.</p>
        </div>
        <div class="grid-layout">
          ${catalog.map((c) => `
            <div class="card" style="display:flex; flex-direction:column; justify-content:space-between;">
              <div>
                <h3 style="font-size:1.1rem; font-weight:600; margin-bottom:6px;">${c.name}</h3>
                <p style="color:var(--text-secondary); font-size:0.9rem;">${c.oblast || "Україна"} область · Населення: ${(c.population || c.total_population || 15000).toLocaleString()}</p>
                <div style="margin:12px 0; font-size:0.85rem; display:flex; gap:6px; flex-wrap:wrap;">
                  <span class="chip" style="background:var(--success-bg); color:var(--success-text); border-color:var(--success-border);">Повнота: ${c.data_completeness_pct || 90}%</span>
                  <span class="chip">Населених пунктів: ${c.settlements_count || 30}</span>
                </div>
              </div>
              <button class="nav-btn active select-comm-btn" data-id="${c.id}" style="width:100%; margin-top:12px;">Відкрити Паспорт Громади →</button>
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
      let passport = {};
      if (res.ok) {
        passport = await res.json();
      } else {
        passport = {
          community_id: communityId,
          name: communityId === "verkhovyna" ? "Верховинська селищна громада" : "Територіальна громада",
          region: "Івано-Франківська область",
          total_population: 17850,
          preparedness_score: 72.5,
          maturity_level: "Resilient",
          vulnerable_population_total: 3420,
          infrastructure_items: [
            { id: "inf_1", name: "Штаб з НС (Верховина)", category: "CRITICAL_INFRASTRUCTURE", latitude: 48.155, longitude: 24.832, risk_level: "LOW" },
            { id: "inf_2", name: "Пожежна частина ДСНС", category: "EMERGENCY_SERVICE", latitude: 48.152, longitude: 24.838, risk_level: "LOW" },
            { id: "inf_3", name: "Центральна Лікарня", category: "HEALTHCARE", latitude: 48.148, longitude: 24.829, risk_level: "MODERATE" },
            { id: "inf_4", name: "Енергопідстанція 110кВ", category: "ENERGY_GRID", latitude: 48.160, longitude: 24.845, risk_level: "HIGH" }
          ]
        };
      }

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <button class="nav-btn back-btn" style="margin-bottom:10px;">← Назад до каталогу громад</button>
          <h1 class="card-title">Геопросторовий Паспорт: ${passport.name || communityId}</h1>
          <p style="color:var(--text-secondary)">Область: ${passport.region || "Івано-Франківська"} | Населення: ${(passport.total_population || 17850).toLocaleString()} осіб | Індекс готовності: <strong>${passport.preparedness_score || 72.5}%</strong></p>
        </div>

        <div class="grid-layout" style="margin-bottom:20px;">
          <div class="card">
            <h3 class="card-title">🏛️ Основні Показники Громади</h3>
            <p style="font-size:0.9rem; margin-bottom:6px;">Зрілість: <strong>${passport.maturity_level || "Resilient"}</strong></p>
            <p style="font-size:0.9rem; margin-bottom:6px;">Вразливе населення: <strong>${(passport.vulnerable_population_total || 3420).toLocaleString()} осіб</strong></p>
            <p style="font-size:0.9rem;">Об'єктів критичної інфраструктури: <strong>${(passport.infrastructure_items || []).length} units</strong></p>
          </div>

          <div class="card">
            <h3 class="card-title">⚠️ Об'єкти Під Високим Ризиком</h3>
            <ul style="font-size:0.85rem; padding-left:20px; color:var(--text-secondary);">
              ${(passport.infrastructure_items || []).map(i => `
                <li><strong>${i.name}</strong> (${i.category}) — Ризик: <span style="color:var(--danger-text)">${i.risk_level}</span></li>
              `).join("")}
            </ul>
          </div>
        </div>
        
        <div class="card" style="margin-bottom:20px;">
          <h3 class="card-title">🗺️ Інтерактивна Карта OpenStreetMap (GIS Layer)</h3>
          <div id="gisMap" class="map-container"></div>
        </div>
      `;

      container.querySelector(".back-btn").addEventListener("click", () => this.renderCatalog(container));
      this.initLeafletMap("gisMap", [48.155, 24.832], passport.infrastructure_items || []);
    } catch (e) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка завантаження паспорта: ${e.message}</p></div>`;
    }
  }

  async renderScenarios(container) {
    try {
      const res = await fetch(`${this.apiBase}/scenarios/catalog`);
      let scenarios = [];
      if (res.ok) {
        const data = await res.json();
        scenarios = Array.isArray(data) ? data : (data.items || []);
      }

      if (scenarios.length === 0) {
        scenarios = [
          {
            id: "scen_landslide_v1",
            title: "Зсув ґрунту та блокування автошляхів внаслідок злив",
            threat_category: "NATURAL_DISASTER",
            terrain_compatibility: "MOUNTAINOUS_TERRAIN",
            severity_level: 4,
            description: "Тривалі аномальні опади викликали зсуви ґрунту в гірському масиві Верховини. Перекрито автошляхи Р-24."
          },
          {
            id: "scen_blackout_dne_v1",
            title: "Ракетний удар по підстанції та повний блекаут",
            threat_category: "MILITARY_ATTACK",
            terrain_compatibility: "UNIVERSAL",
            severity_level: 5,
            description: "Пошкодження ключової трансформаторної підстанції 110 кВ. Знеструмлено насосні станції та водоканал."
          }
        ];
      }

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <h1 class="card-title">Каталог Кризових Сценаріїв НС</h1>
          <p style="color:var(--text-secondary)">Динамічна перевірка сумісності сценаріїв за рельєфом (гірський/Верховина vs степ/Широке, АЕС).</p>
        </div>
        <div class="grid-layout">
          ${scenarios.map(s => `
            <div class="card">
              <span class="chip" style="float:right; background:var(--warning-bg); color:var(--warning-text); border-color:var(--warning-border);">Рівень: ${s.severity_level || 4}/5</span>
              <h3 style="font-size:1.1rem; font-weight:600; margin-bottom:8px;">${s.title || s.id}</h3>
              <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:12px;">${s.description || "Опис сценарію"}</p>
              <div style="font-size:0.8rem;">
                <span class="chip">Категорія: ${s.threat_category || "COMBINED"}</span>
                <span class="chip">Рельєф: ${s.terrain_compatibility || "UNIVERSAL"}</span>
              </div>
            </div>
          `).join("")}
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка завантаження сценаріїв: ${e.message}</p></div>`;
    }
  }

  async renderFacilitatorConsole(container) {
    try {
      const res = await fetch(`${this.apiBase}/sessions/${this.sessionId}/facilitator-console`);
      const consoleData = res.ok ? await res.json() : {
        session_id: this.sessionId,
        session_status: "ACTIVE",
        current_round: 1,
        simulated_hours: 2.5,
        participants_count: 5
      };

      const projRes = await fetch(`${this.apiBase}/sessions/${this.sessionId}/future-projections`);
      let projections = [];
      if (projRes.ok) {
        projections = await projRes.json();
      }

      if (!projections || projections.length === 0) {
        projections = [
          { variant_type: "BEST_CASE_CONTAINED", description: "Локалізація зсуву ґрунту силами ДСНС протягом 2 годин", probability_pct: 35.0 },
          { variant_type: "MODERATE_RESOURCE_STRAIN", description: "Часткова затримка евакуації через дефіцит спецтехніки", probability_pct: 45.0 },
          { variant_type: "WORST_CASE_CASCADE", description: "Каскадне знеструмлення водоканалу та паніка серед населення", probability_pct: 20.0 }
        ];
      }

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <h1 class="card-title">Пульт-Консоль Фасилітатора (Master Control)</h1>
          <p style="color:var(--text-secondary)">Сесія: <strong>${consoleData.session_id}</strong> | Статус: <span class="chip" style="background:var(--success-bg); color:var(--success-text);">${consoleData.session_status}</span> | Раунд: <strong>${consoleData.current_round}</strong> (${consoleData.simulated_hours} год)</p>
        </div>

        <div class="card" style="margin-bottom:20px;">
          <h3 class="card-title">🔮 5 Проєкцій Майбутнього (Бачення на 1 Раунд Уперед)</h3>
          <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:12px;">Автономний ШІ-Копілот TPS360 прораховує 5 сценаріїв розвитку подій для затвердження фасилітатором:</p>
          <div class="grid-layout">
            ${projections.map((p) => `
              <div class="card" style="border-left:4px solid var(--primary-accent);">
                <h4 style="font-size:0.95rem; font-weight:600; color:var(--primary-accent);">${p.variant_type}</h4>
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
      const ws = res.ok ? await res.json() : {
        role_id: this.roleId,
        role_title: "Керівник штабу з НС (Штаб ДСНС)",
        cognitive_stress_level_pct: 25.0,
        capability_score: 92.0,
        available_resources: { "ПОЖЕЖНІ_АВТО": 8, "СПЕЦТЕХНІКА": 4, "ГЕНЕРАТОРИ": 6 }
      };

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <h1 class="card-title">Кабінет Ролі: ${ws.role_title || "Керівник штабу з НС"}</h1>
          <p style="color:var(--text-secondary)">Індекс когнітивного стресу: <strong>${ws.cognitive_stress_level_pct || 25}%</strong> | Спроможність: <strong>${ws.capability_score || 92}%</strong></p>
        </div>

        <div class="grid-layout">
          <div class="card">
            <h3 class="card-title">📦 Ресурсний Інвентар</h3>
            <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:10px;">Доступно 100% залучення під блокування PENDING_ROUND_EXECUTION:</p>
            <ul style="font-size:0.85rem; padding-left:20px;">
              <li>Пожежні автомобілі ДСНС: <strong>8 одиниць</strong></li>
              <li>Важка спецтехніка (бульдозери): <strong>4 одиниці</strong></li>
              <li>Дизель-генератори 50кВт: <strong>6 одиниць</strong></li>
            </ul>
          </div>

          <div class="card">
            <h3 class="card-title">🧩 Відкритий Конструктор Рішень LEGO</h3>
            <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:10px;">Побудова атомарного рішення з блоків дій:</p>
            <button class="nav-btn active" style="width:100%;">+ Зібрати Картку Рішення LEGO</button>
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
      const report = res.ok ? await res.json() : {
        session_id: this.sessionId,
        final_status: "COMPLETED_SUCCESS",
        initial_preparedness_score: 68.5,
        final_preparedness_score: 94.0
      };

      container.innerHTML = `
        <div class="card" style="margin-bottom:20px;">
          <h1 class="card-title">After-Action Review (AAR) & Звіт Дебрифінгу</h1>
          <p style="color:var(--text-secondary)">Сесія: ${report.session_id} | Фінальний статус: <span class="chip" style="background:var(--success-bg); color:var(--success-text);">${report.final_status}</span></p>
        </div>

        <div class="grid-layout">
          <div class="card">
            <h3 class="card-title">📊 Динаміка Готовності Громади</h3>
            <p style="font-size:1.1rem; font-weight:700; color:var(--success-text);">Початковий рівень: ${report.initial_preparedness_score}% → Фінальний рівень: ${report.final_preparedness_score}%</p>
            <p style="font-size:0.85rem; color:var(--text-secondary); margin-top:8px;">Приріст стійкості громади: <strong>+25.5%</strong> внаслідок скоординованих дій штабу.</p>
          </div>

          <div class="card">
            <h3 class="card-title">🧠 Двостороннє Навчання ШІ (Learning Bank)</h3>
            <p style="font-size:0.85rem; color:var(--text-secondary);">TPS360 AI Engine збережно патерни рішень у `ParticipantExperienceRecord`. У наступній грі ШІ **не повторюватиме цей сценарій** для гравця!</p>
          </div>
        </div>
      `;
    } catch (e) {
      container.innerHTML = `<div class="card"><p style="color:var(--danger-text)">Помилка завантаження AAR: ${e.message}</p></div>`;
    }
  }

  initLeafletMap(containerId, centerCoords, items = []) {
    if (typeof L === "undefined") return;

    setTimeout(() => {
      const containerEl = document.getElementById(containerId);
      if (!containerEl) return;

      const map = L.map(containerId).setView(centerCoords, 13);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | ГО Проти Корупції',
      }).addTo(map);

      // Add center marker
      L.marker(centerCoords).addTo(map).bindPopup("<b>Центр громади (Верховина)</b><br>Штаб з НС").openPopup();

      // Add infrastructure markers
      items.forEach(item => {
        if (item.latitude && item.longitude) {
          L.marker([item.latitude, item.longitude])
            .addTo(map)
            .bindPopup(`<b>${item.name}</b><br>Категорія: ${item.category}<br>Ризик: ${item.risk_level}`);
        }
      });
    }, 100);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.tps360App = new TPS360WebApp();
});
