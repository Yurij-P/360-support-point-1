// ==========================================================================
// TPS360 OPERATIONAL HEADQUARTERS APP LOGIC
// ==========================================================================

const CONFIG = {
    communityId: "a29d6fbd-02c3-4d43-a651-7efd6fbd02c3",
    scenarioId: "s89d6fbd-02c3-4d43-a651-7efd6fbd089c",
    simulationId: "e72d6fbd-02c3-4d43-a651-7efd6fbd077c"
};

let simulationState = {
    id: null,
    status: "draft",
    startedAt: null,
    decisions: [],
    resources: {
        personnel: { max: 120, avail: 68, busy: 52 },
        transport: { max: 28, avail: 14, busy: 14 },
        water: 620,
        budget: 2450000,
        connection: "Норма"
    }
};

let timerInterval = null;
let simulationTimeSeconds = 84 * 60 + 36; // Initial time 01:24:36 in seconds
let waterDepletionActive = true;

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

async function initApp() {
    showToast("Ініціалізація системи Операційного штабу...");
    
    // 1. Setup local environment / repositories in backend
    await ensureBackendSetup();

    // 2. Fetch or create simulation
    await startSimulationSession();

    // 3. Start running clock
    startClock();

    // 4. Start water depletion simulation (local visual behavior)
    startLocalWaterSimulation();

    // 5. Setup UI event listeners
    setupEventListeners();
}

async function ensureBackendSetup() {
    try {
        // Create community if not exists
        await fetch('/communities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: CONFIG.communityId,
                name: "Березнегуватська громада",
                code: "BRZ-01",
                oblast: "Миколаївська",
                population: 15400,
                area_km2: 124.5
            })
        });

        // Create scenario if not exists
        await fetch('/scenarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: CONFIG.scenarioId,
                title: "Аварія системи водопостачання",
                description: "Критична аварія на магістральному трубопроводі",
                duration_minutes: 180
            })
        });
    } catch (e) {
        console.warn("Backend seeding skipped or already seeded:", e);
    }
}

async function startSimulationSession() {
    try {
        // Try to get simulation if already exists
        let res = await fetch(`/simulations/${CONFIG.simulationId}`);
        if (!res.ok) {
            // Create simulation
            const simPayload = {
                id: CONFIG.simulationId,
                scenario_id: CONFIG.scenarioId,
                community_id: CONFIG.communityId,
                status: "draft",
                started_at: new Date().toISOString()
            };
            
            res = await fetch('/simulations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(simPayload)
            });

            if (res.ok) {
                // Start simulation
                await fetch(`/simulations/${CONFIG.simulationId}/start`, { method: 'POST' });
                showToast("Розпочато нову симуляційну сесію");
            }
        } else {
            showToast("Завантажено існуючу симуляційну сесію");
            const data = await res.json();
            restoreDecisionsFromState(data);
        }
    } catch (e) {
        console.error("Error setting up simulation session:", e);
        showToast("Помилка з'єднання з API. Запущено в офлайн-режимі.", "error");
    }
}

function restoreDecisionsFromState(state) {
    if (state && state.decisions && state.decisions.length > 0) {
        state.decisions.forEach(d => {
            let decId = 1;
            if (d.selected_action.includes("2")) decId = 2;
            else if (d.selected_action.includes("3")) decId = 3;
            applyDecisionUI(decId, false);
        });
    }
}

function startClock() {
    const timeEl = document.getElementById("simulation-time");
    
    timerInterval = setInterval(() => {
        simulationTimeSeconds++;
        const hrs = String(Math.floor(simulationTimeSeconds / 3600)).padStart(2, '0');
        const mins = String(Math.floor((simulationTimeSeconds % 3600) / 60)).padStart(2, '0');
        const secs = String(simulationTimeSeconds % 60).padStart(2, '0');
        
        timeEl.textContent = `${hrs}:${mins}:${secs}`;
        
        // Update critical event duration
        const durationEl = document.getElementById("event-duration");
        const eventMins = String(Math.floor((simulationTimeSeconds - (81 * 60 + 10)) / 60)).padStart(2, '0');
        const eventSecs = String((simulationTimeSeconds - (81 * 60 + 10)) % 60).padStart(2, '0');
        if (simulationTimeSeconds > (81 * 60 + 10)) {
            durationEl.textContent = `00:${eventMins}:${eventSecs}`;
        }
    }, 1000);
}

function startLocalWaterSimulation() {
    setInterval(() => {
        if (waterDepletionActive && simulationState.resources.water > 100) {
            simulationState.resources.water -= 1;
            updateResourceUI("water", simulationState.resources.water);
        }
    }, 4000);
}

function updateResourceUI(type, value) {
    if (type === "water") {
        document.getElementById("val-water").textContent = value;
        const pct = Math.min(100, (value / 1000) * 100);
        document.querySelector("#res-water .progress-bar").style.width = `${pct}%`;
        
        // Trigger low water warning if needed
        if (value < 400) {
            document.querySelector("#res-water .progress-bar").className = "progress-bar red";
        }
    } else if (type === "budget") {
        document.getElementById("val-budget").textContent = value.toLocaleString('uk-UA');
        const pct = Math.min(100, (value / 3000000) * 100);
        document.querySelector("#res-budget .progress-bar").style.width = `${pct}%`;
    } else if (type === "personnel") {
        document.getElementById("val-personnel").textContent = value.busy;
        document.getElementById("val-personnel-busy").textContent = value.busy;
        document.getElementById("val-personnel-avail").textContent = value.avail;
        const pct = Math.min(100, (value.busy / value.max) * 100);
        document.querySelector("#res-personnel .progress-bar").style.width = `${pct}%`;
    } else if (type === "transport") {
        document.getElementById("val-transport").textContent = value.busy;
        document.getElementById("val-transport-busy").textContent = value.busy;
        document.getElementById("val-transport-avail").textContent = value.avail;
        const pct = Math.min(100, (value.busy / value.max) * 100);
        document.querySelector("#res-transport .progress-bar").style.width = `${pct}%`;
    }
}

async function makeDecision(decisionId) {
    let actionName = "";
    let desc = "";
    let cost = 0;
    
    if (decisionId === 1) {
        actionName = "Ремонтні роботи";
        desc = "Ремонтні роботи на магістралі. Направлено аварійну бригаду.";
        cost = 150000;
        simulationState.resources.personnel.busy += 15;
        simulationState.resources.personnel.avail -= 15;
        simulationState.resources.transport.busy += 2;
        simulationState.resources.transport.avail -= 2;
    } else if (decisionId === 2) {
        actionName = "Переключення на резерв";
        desc = "Переключення на резервну лінію. Запущено Насосну станцію №2.";
        cost = 50000;
        simulationState.resources.personnel.busy += 5;
        simulationState.resources.personnel.avail -= 5;
        waterDepletionActive = false; // Water stabilizes
    } else if (decisionId === 3) {
        actionName = "Підвіз води";
        desc = "Організовано підвіз води автоцистернами до лікарні та кварталів.";
        cost = 20000;
        simulationState.resources.transport.busy += 8;
        simulationState.resources.transport.avail -= 8;
        simulationState.resources.water += 150; // Visual boost
    }

    simulationState.resources.budget -= cost;

    // Send decision to backend API
    const decisionPayload = {
        id: uuidv4(),
        simulation_id: CONFIG.simulationId,
        actor: "Керівник штабу",
        description: desc,
        rationale: "Негайне реагування на падіння тиску",
        selected_action: `${decisionId}. ${actionName}`
    };

    try {
        await fetch(`/simulations/${CONFIG.simulationId}/decisions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(decisionPayload)
        });
        showToast(`Обрано рішення: ${actionName}`);
    } catch(e) {
        console.error("Offline decision registered:", e);
        showToast(`Обрано рішення (офлайн): ${actionName}`);
    }

    applyDecisionUI(decisionId, true);
}

function applyDecisionUI(decisionId, animate = true) {
    // 1. Update decision cards state
    const cards = document.querySelectorAll(".decision-card");
    cards.forEach(card => {
        card.classList.add("disabled");
        const btn = card.querySelector(".select-decision-btn");
        if (btn) btn.disabled = true;
    });

    const selectedCard = document.querySelector(`.decision-card[data-decision-id="${decisionId}"]`);
    if (selectedCard) {
        selectedCard.classList.remove("disabled");
        selectedCard.classList.add("selected");
        const btn = selectedCard.querySelector(".select-decision-btn");
        if (btn) btn.textContent = "Обрано";
    }

    // 2. Update resource displays
    updateResourceUI("budget", simulationState.resources.budget);
    updateResourceUI("water", simulationState.resources.water);
    updateResourceUI("personnel", simulationState.resources.personnel);
    updateResourceUI("transport", simulationState.resources.transport);

    // 3. Modify SVG Map visual state based on selection
    const hospNode = document.getElementById("node-hospital");
    const soniachnyiNode = document.getElementById("node-soniachnyi");
    const pipePumpHosp = document.getElementById("pipe-pump-hosp");

    if (decisionId === 2) {
        // Switch to reserve line fixes the map status
        hospNode.classList.remove("critical", "pulse-node");
        hospNode.querySelector("circle").setAttribute("stroke", "#00e676");
        hospNode.querySelector("circle").setAttribute("fill", "rgba(0, 230, 90, 0.15)");
        hospNode.querySelector(".node-sublabel").textContent = "Тиск відновлено · Норма";
        hospNode.querySelector(".node-sublabel").className = "node-sublabel green-text";

        soniachnyiNode.querySelector("circle").setAttribute("stroke", "#00e676");
        soniachnyiNode.querySelector(".node-sublabel").textContent = "Тиск: 1.2 bar · Норма";

        pipePumpHosp.setAttribute("stroke", "#00e5ff");
        pipePumpHosp.setAttribute("filter", "url(#cyan-glow)");
    } else if (decisionId === 3) {
        // Water delivery mitigates hospital danger slightly
        hospNode.querySelector(".node-sublabel").textContent = "Підвіз води організовано";
        hospNode.querySelector(".node-sublabel").className = "node-sublabel blue-text";
    }

    // 4. Append new timeline card
    appendTimelineCard(decisionId);

    // 5. Add new notification
    appendAlert(decisionId);
}

function appendTimelineCard(decisionId) {
    const container = document.getElementById("timeline-cards-container");
    const lockedCard = document.getElementById("future-complication-card");
    
    // Check if decision timeline card already appended
    if (document.getElementById(`timeline-card-decision-${decisionId}`)) return;

    // Get current simulation clock format
    const hrs = String(Math.floor(simulationTimeSeconds / 3600)).padStart(2, '0');
    const mins = String(Math.floor((simulationTimeSeconds % 3600) / 60)).padStart(2, '0');
    const secs = String(simulationTimeSeconds % 60).padStart(2, '0');
    const timeStr = `${hrs}:${mins}:${secs}`;

    let title = "";
    let desc = "";
    let outcome = "";
    let borderClass = "";
    let textClass = "";

    if (decisionId === 1) {
        title = "Початок ремонтних робіт";
        desc = "Направлено аварійну бригаду на ділянку витоку.";
        outcome = "Наслідки: Ремонт триває, очікується локалізація.";
        borderClass = "orange-border";
        textClass = "orange-text";
    } else if (decisionId === 2) {
        title = "Активація резервного каналу";
        desc = "Водопостачання переведено на резервну лінію через Насосну станцію №2.";
        outcome = "Наслідки: Тиск стабілізовано в критичних точках.";
        borderClass = "blue-border";
        textClass = "blue-text";
    } else if (decisionId === 3) {
        title = "Організація підвозу води";
        desc = "Автоцистерни вирушили до Березнегуватської лікарні.";
        outcome = "Наслідки: Забезпечено мінімальну потребу лікарні.";
        borderClass = "purple-border";
        textClass = "purple-text";
    }

    const card = document.createElement("div");
    card.className = "timeline-card done-card active-card";
    card.id = `timeline-card-decision-${decisionId}`;
    card.innerHTML = `
        <div class="card-time">${timeStr}</div>
        <div class="card-inner ${borderClass}">
            <h3>${title}</h3>
            <p>${desc}</p>
            <div class="card-consequences ${textClass}">${outcome}</div>
        </div>
    `;

    // Insert before the locked card
    container.insertBefore(card, lockedCard);
    
    // Dim the locked card completely
    lockedCard.style.opacity = "0.15";
    lockedCard.querySelector("h3").textContent = "Загрозу нейтралізовано";
    lockedCard.querySelector("p").textContent = "Попереджено повне припинення водопостачання.";
    lockedCard.querySelector(".card-consequences").className = "card-consequences green-text";
    lockedCard.querySelector(".card-consequences").textContent = "Наслідки: Ризики знято";
}

function appendAlert(decisionId) {
    const container = document.getElementById("alerts-container");
    
    let text = "";
    let bulletClass = "";
    
    if (decisionId === 1) {
        text = "Аварійна бригада виїхала на об'єкт";
        bulletClass = "orange-bullet";
    } else if (decisionId === 2) {
        text = "Успішно перемкнено на резервну гілку";
        bulletClass = "blue-bullet";
    } else if (decisionId === 3) {
        text = "Водовоз №1 прибув до лікарні";
        bulletClass = "blue-bullet";
    }

    const hrs = String(Math.floor(simulationTimeSeconds / 3600)).padStart(2, '0');
    const mins = String(Math.floor((simulationTimeSeconds % 3600) / 60)).padStart(2, '0');
    const timeStr = `${hrs}:${mins}`;

    const alertItem = document.createElement("div");
    alertItem.className = `alert-item ${bulletClass}`;
    alertItem.innerHTML = `
        <span class="bullet"></span>
        <span class="alert-text">${text}</span>
        <span class="alert-time">${timeStr}</span>
    `;

    container.insertBefore(alertItem, container.firstChild);
    
    // Update badge count
    const badge = document.querySelector(".alert-count-badge");
    badge.textContent = parseInt(badge.textContent) + 1;
}

function setupEventListeners() {
    // Show effects toggle logic
    const toggleEffects = document.getElementById("toggle-effects");
    toggleEffects.addEventListener("change", (e) => {
        const consequences = document.querySelectorAll(".card-consequences");
        consequences.forEach(c => {
            c.style.display = e.target.checked ? "block" : "none";
        });
        showToast(e.target.checked ? "Відображення наслідків увімкнено" : "Відображення наслідків вимкнено");
    });
}

function showToast(message, type = "info") {
    const toast = document.getElementById("toast-notification");
    toast.textContent = message;
    toast.className = `toast ${type === 'error' ? 'red-border' : ''}`;
    toast.classList.remove("hidden");
    
    setTimeout(() => {
        toast.classList.add("hidden");
    }, 4000);
}

// Helper to generate UUIDs
function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}
