const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api/v1"

/**
 * Every request needs the admin's bearer token. The token is stored in
 * localStorage so it survives a page refresh during a work session, but
 * it is never sent anywhere except this API — see README for how a real
 * login flow would replace this later.
 */
export function getToken() {
  return localStorage.getItem("aptwatch_admin_token") || ""
}

export function setToken(token) {
  localStorage.setItem("aptwatch_admin_token", token)
}

async function request(path, options = {}) {
  const token = getToken()
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  let body = null
  try {
    body = await response.json()
  } catch {
    // some responses (like a plain 204) have no JSON body
  }

  return { ok: response.ok, status: response.status, body }
}

export const api = {
  health: () => request("/../health", { method: "GET" }),
  listDocuments: () => request("/documents", { method: "GET" }),
  getStatus: (name) => request(`/documents/${encodeURIComponent(name)}/status`, { method: "GET" }),
  deleteDocument: (name) => request(`/documents/${encodeURIComponent(name)}`, { method: "DELETE" }),
  reindexDocument: (name) => request(`/documents/${encodeURIComponent(name)}/reindex`, { method: "POST" }),
  uploadDocument: (formData) => request("/documents/upload", { method: "POST", body: formData }),
  unansweredQuestions: () => request("/documents/unanswered-questions", { method: "GET" }),
  frequentlyAsked: () => request("/documents/frequently-asked", { method: "GET" }),

  createAccount: (payload) =>
    request("/admin/accounts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
}
