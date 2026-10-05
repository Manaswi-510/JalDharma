/**
 * Jal Dharma AI - API Client
 * Connects the React dashboard to the FastAPI backend on port 8000.
 * All functions return Promises. Components use useLiveData() hook below.
 */

const BASE_URL = 'http://localhost:8000/api';

// ── Generic fetch helper ──────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Endpoints ─────────────────────────────────────────────────────────────────
export const api = {
  health:           () => apiFetch('/health'),
  overview:         () => apiFetch('/overview'),
  villages:         () => apiFetch('/villages'),
  villageIds:       () => apiFetch('/village-ids'),
  predictions:      (villageId, days = 14) => apiFetch(`/predictions/${villageId}?days=${days}`),
  allocations:      (dateStr) => apiFetch(`/allocations${dateStr ? `?date_str=${dateStr}` : ''}`),
  adjustAllocation: (villageId, allocatedKL) =>
    apiFetch('/allocations/adjust', {
      method: 'POST',
      body: JSON.stringify({ village_id: villageId, allocated_kl: allocatedKL }),
    }),
  pipelines:        () => apiFetch('/pipelines'),
  waterSources:     () => apiFetch('/water-sources'),
  justice:          () => apiFetch('/justice'),
};
