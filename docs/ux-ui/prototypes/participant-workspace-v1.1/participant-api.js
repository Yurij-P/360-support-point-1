"use strict";

(function (root, factory) {
  const api = factory();
  if (root) root.TPS360ParticipantApi = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
}(typeof window !== "undefined" ? window : null, function () {
  class ParticipantApiError extends Error {
    constructor(message, status) {
      super(message);
      this.name = "ParticipantApiError";
      this.status = status;
    }
  }

  function createClient(options) {
    const config = options || {};
    const request = config.request || (typeof window !== "undefined" ? window.fetch.bind(window) : null);
    const storage = config.storage || (typeof window !== "undefined" ? window.localStorage : null);
    const baseUrl = String(config.baseUrl || "http://127.0.0.1:8000").replace(/\/$/, "");
    const storageKey = "tps360-participant-session-v1";

    if (typeof request !== "function") throw new Error("A fetch-compatible request function is required");

    async function jsonRequest(path, init) {
      let response;
      try {
        response = await request(baseUrl + path, init);
      } catch (_error) {
        throw new ParticipantApiError("API unavailable. Check that the backend is running.", 0);
      }
      let body = null;
      try { body = await response.json(); } catch (_error) { body = null; }
      if (!response.ok) {
        const detail = body && typeof body.detail === "string" ? body.detail : "Request failed.";
        throw new ParticipantApiError(detail, response.status);
      }
      return body;
    }

    return {
      async joinSession(sessionId, joinToken, displayName) {
        return jsonRequest("/sessions/" + encodeURIComponent(sessionId) + "/participants/join", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ join_token: joinToken, display_name: displayName })
        });
      },
      async getParticipant(sessionId, participantToken) {
        return jsonRequest("/sessions/" + encodeURIComponent(sessionId) + "/participant", {
          method: "GET",
          headers: { "X-Participant-Token": participantToken }
        });
      },
      async submitDecision(sessionId, injectId, participantToken, participantId, decisionPayload) {
        return jsonRequest("/sessions/" + encodeURIComponent(sessionId) + "/injects/" + encodeURIComponent(injectId) + "/decisions", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Participant-Token": participantToken },
          body: JSON.stringify({
            participant_id: participantId,
            decision_payload: decisionPayload
          })
        });
      },
      saveSession(session) {
        if (!storage) return;
        storage.setItem(storageKey, JSON.stringify({
          session_id: session.session_id,
          participant_id: session.participant_id,
          participant_token: session.participant_token
        }));
      },
      loadSession() {
        if (!storage) return null;
        try {
          const saved = JSON.parse(storage.getItem(storageKey) || "null");
          if (!saved || !saved.session_id || !saved.participant_token) return null;
          return saved;
        } catch (_error) {
          return null;
        }
      },
      clearSession() {
        if (storage) storage.removeItem(storageKey);
      },
      ParticipantApiError
    };
  }

  return { createClient, ParticipantApiError };
}));