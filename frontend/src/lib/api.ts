const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchJson(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const err = await res.json();
      errorDetail = err.detail || err.message || errorDetail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return res.json();
}

// Participants
export const api = {
  getParticipants: (params?: { search?: string; status_filter?: string; limit?: number; skip?: number }) => {
    const query = new URLSearchParams();
    if (params?.search) query.append("search", params.search);
    if (params?.status_filter) query.append("status_filter", params.status_filter);
    if (params?.limit) query.append("limit", params.limit.toString());
    if (params?.skip) query.append("skip", params.skip.toString());
    return fetchJson(`/participants?${query.toString()}`);
  },

  getParticipant: (id: string) => fetchJson(`/participants/${id}`),

  getParticipantEvidence: (id: string) => fetchJson(`/participants/${id}/evidence`),

  getParticipantProfile: (id: string) => fetchJson(`/participants/${id}/profile`),

  createParticipant: (data: {
    name: string;
    linkedin_url: string;
    instagram_url: string;
    consent_confirmed: boolean;
    age?: number;
    gender?: string;
    target_gender?: string;
    location?: string;
  }) => fetchJson("/participants", { method: "POST", body: JSON.stringify(data) }),

  deleteParticipant: (id: string) => fetchJson(`/participants/${id}`, { method: "DELETE" }),

  triggerAnalysis: (id: string) => fetchJson(`/participants/${id}/analyze`, { method: "POST" }),

  // Dating Sessions
  getDates: (params?: { status_filter?: string; run_id?: string; limit?: number; skip?: number }) => {
    const query = new URLSearchParams();
    if (params?.status_filter) query.append("status_filter", params.status_filter);
    if (params?.run_id) query.append("run_id", params.run_id);
    if (params?.limit) query.append("limit", params.limit.toString());
    if (params?.skip) query.append("skip", params.skip.toString());
    return fetchJson(`/dates?${query.toString()}`);
  },

  getDateSession: (id: string) => fetchJson(`/dates/${id}`),

  startDatingSession: (data: { participant_a_id: string; participant_b_id: string; max_turns?: number; run_id?: string }) =>
    fetchJson("/dates", { method: "POST", body: JSON.stringify(data) }),

  // Rankings
  getRankings: (participantId: string, runId?: string) => {
    const query = runId ? `?run_id=${encodeURIComponent(runId)}` : "";
    return fetchJson(`/participants/${participantId}/rankings${query}`);
  },

  recalculateRankings: (participantId: string, weights: any, runId?: string) => {
    const query = runId ? `?run_id=${encodeURIComponent(runId)}` : "";
    return fetchJson(`/participants/${participantId}/rankings/recalculate${query}`, {
      method: "POST",
      body: JSON.stringify(weights),
    });
  },

  // Demonstration Runs
  getRuns: () => fetchJson("/runs"),

  getRun: (runId: string) => fetchJson(`/runs/${runId}`),

  getRunProgress: (runId: string) => fetchJson(`/runs/${runId}/progress`),

  startRun: (data: { run_id?: string; name?: string }) =>
    fetchJson("/runs", { method: "POST", body: JSON.stringify(data) }),

  resumeRun: (runId: string) => fetchJson(`/runs/${runId}/resume`, { method: "POST" }),

  // Admin & Health
  getHealth: () => fetchJson("/health"),

  getMetrics: () => fetchJson("/admin/metrics"),

  getAdminConfig: () => fetchJson("/admin/config"),

  updateAdminConfig: (data: any) => fetchJson("/admin/config", { method: "POST", body: JSON.stringify(data) }),

  seedDemo: () => fetchJson("/admin/seed-demo", { method: "POST" }),
};
