const test = require("node:test");
const assert = require("node:assert/strict");
const { createClient } = require("./participant-api.js");

function response(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

function memoryStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) || null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key)
  };
}

test("join sends join token and stores participant session without facilitator token", async () => {
  const calls = [];
  const client = createClient({
    baseUrl: "http://127.0.0.1:8000",
    storage: memoryStorage(),
    request: async (url, init) => {
      calls.push({ url, init });
      return response(200, {
        participant_id: "participant-1",
        participant_token: "participant-secret",
        role_assigned: false,
        lifecycle: "role_pending",
        status: "LOBBY"
      });
    }
  });

  const payload = await client.joinSession("session-1", "join-secret", "Alice");
  client.saveSession({ session_id: "session-1", participant_id: payload.participant_id, participant_token: payload.participant_token });

  assert.equal(calls[0].url, "http://127.0.0.1:8000/sessions/session-1/participants/join");
  assert.deepEqual(JSON.parse(calls[0].init.body), { join_token: "join-secret", display_name: "Alice" });
  assert.equal(calls[0].init.headers["X-Facilitator-Token"], undefined);
  assert.deepEqual(client.loadSession(), {
    session_id: "session-1",
    participant_id: "participant-1",
    participant_token: "participant-secret"
  });
});

test("participant refresh uses only participant token", async () => {
  let request;
  const client = createClient({
    baseUrl: "http://127.0.0.1:8000",
    request: async (url, init) => {
      request = { url, init };
      return response(200, { participant_id: "participant-1", role_assigned: true, role_id: "role-1" });
    }
  });

  await client.getParticipant("session-1", "participant-secret");

  assert.equal(request.url, "http://127.0.0.1:8000/sessions/session-1/participant");
  assert.deepEqual(request.init.headers, { "X-Participant-Token": "participant-secret" });
  assert.equal(request.init.headers["X-Facilitator-Token"], undefined);
});

test("invalid participant response is surfaced and local session can be cleared", async () => {
  const storage = memoryStorage();
  const client = createClient({ storage, request: async () => response(401, { detail: "invalid token" }) });
  client.saveSession({ session_id: "session-1", participant_id: "participant-1", participant_token: "bad" });
  await assert.rejects(() => client.getParticipant("session-1", "bad"), (error) => error.status === 401);
  client.clearSession();
  assert.equal(client.loadSession(), null);
});
test("logout control is wired and clears only participant session storage", async () => {
  const fs = require("node:fs");
  const html = fs.readFileSync("./docs/ux-ui/prototypes/participant-workspace-v1.1/TPS360 Participant Wireframes.html", "utf8");
  assert.match(html, /<button[^>]*onClick="\{\{ logout \}\}"/);

  const storage = memoryStorage();
  const client = createClient({ storage, request: async () => response(200, {}) });
  storage.setItem("unrelated", "keep-me");
  client.saveSession({ session_id: "session-1", participant_id: "participant-1", participant_token: "secret" });
  client.clearSession();

  assert.equal(client.loadSession(), null);
  assert.equal(storage.getItem("tps360-participant-session-v1"), null);
  assert.equal(storage.getItem("unrelated"), "keep-me");
});
test("logout implementation removes the workspace session after resetting UI state", () => {
  const fs = require("node:fs");
  const html = fs.readFileSync("./docs/ux-ui/prototypes/participant-workspace-v1.1/TPS360 Participant Wireframes.html", "utf8");
  assert.match(html, /onClick="\{\{ logout \}\}"/);
  assert.match(html, /window\.localStorage\.removeItem\("tps360-participant-workspace-v1\.1"\)/);
});
test("participant refresh exposes active injects and own decisions", async () => {
  const client = createClient({
    baseUrl: "http://127.0.0.1:8000",
    request: async () => response(200, {
      participant_id: "participant-1",
      role_assigned: true,
      role_id: "role-1",
      injects: [{ id: "inject-1", title: "Pressure drop", description: "Main line pressure dropped" }],
      decisions: [{ id: "decision-1", inject_id: "inject-1", participant_id: "participant-1", decision_payload: { kind: "structured_decision_placeholder", blocks: [] } }]
    })
  });

  const payload = await client.getParticipant("session-1", "participant-secret");

  assert.equal(payload.injects.length, 1);
  assert.equal(payload.injects[0].title, "Pressure drop");
  assert.equal(payload.decisions.length, 1);
  assert.equal(payload.decisions[0].participant_id, "participant-1");
});

test("submit decision uses participant token and session inject endpoint", async () => {
  let request;
  const client = createClient({
    baseUrl: "http://127.0.0.1:8000",
    request: async (url, init) => {
      request = { url, init };
      return response(200, { id: "decision-1", participant_id: "participant-1", inject_id: "inject-1" });
    }
  });

  const decisionPayload = {
    schema_version: "participant-decision-draft-0.1",
    kind: "structured_decision_placeholder",
    blocks: [],
    notes: {
      title: "Open reserve water point",
      description: "Open a temporary reserve water point.",
      rationale: "Fastest available mitigation"
    }
  };
  const payload = await client.submitDecision(
    "session-1",
    "inject-1",
    "participant-secret",
    "participant-1",
    decisionPayload
  );

  assert.equal(request.url, "http://127.0.0.1:8000/sessions/session-1/injects/inject-1/decisions");
  assert.deepEqual(request.init.headers, {
    "Content-Type": "application/json",
    "X-Participant-Token": "participant-secret"
  });
  assert.equal(request.init.headers["X-Facilitator-Token"], undefined);
  assert.deepEqual(JSON.parse(request.init.body), {
    participant_id: "participant-1",
    decision_payload: decisionPayload
  });
  assert.equal(JSON.parse(request.init.body).selected_action, undefined);
  assert.equal(payload.id, "decision-1");
});

test("submit decision errors are surfaced", async () => {
  const client = createClient({ request: async () => response(403, { detail: "Inject is not available" }) });

  await assert.rejects(
    () => client.submitDecision("session-1", "inject-1", "bad", "participant-1", { schema_version: "participant-decision-draft-0.1", kind: "structured_decision_placeholder", blocks: [] }),
    (error) => error.status === 403 && /Inject/.test(error.message)
  );
});

test("workspace decision UI is wired to API submission states", () => {
  const fs = require("node:fs");
  const html = fs.readFileSync("./docs/ux-ui/prototypes/participant-workspace-v1.1/TPS360 Participant Wireframes.html", "utf8");

  assert.match(html, /this\.api\.submitDecision/);
  assert.match(html, /decision_submitted/);
  assert.match(html, /Submitted to facilitator/);
  assert.match(html, /structured_decision_placeholder/);
  assert.match(html, /LEGO DECISION BUILDER WILL FOLLOW/);
  assert.doesNotMatch(html, /Submitted - local MOCK DATA/);
  assert.doesNotMatch(html, /persistence: "MOCK DATA - API REQUIRED"/);
});
