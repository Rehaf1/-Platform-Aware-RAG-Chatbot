const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api/v1"

/**
 * Every request needs the user's bearer token. Stored in localStorage so
 * it survives a page refresh mid-conversation. A real deployment would
 * get this token from each platform's own login flow, not a manual
 * paste box -- see README.
 */
export function getToken() {
  return localStorage.getItem("aptwatch_chat_token") || ""
}

export function setToken(token) {
  localStorage.setItem("aptwatch_chat_token", token)
}

/**
 * Conversation continuity: the server never guesses based on elapsed
 * time -- WE decide whether a message continues the last conversation
 * or starts fresh, by sending (or omitting) this stored id. Cleared
 * whenever the user explicitly starts a new chat.
 */
export function getConversationId() {
  return localStorage.getItem("aptwatch_conversation_id") || null
}

export function setConversationId(id) {
  if (id) localStorage.setItem("aptwatch_conversation_id", id)
}

export function clearConversationId() {
  localStorage.removeItem("aptwatch_conversation_id")
}

async function request(path, options = {}) {
  const token = getToken()
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  let body = null
  try {
    body = await response.json()
  } catch {
    // some responses have no JSON body
  }

  return { ok: response.ok, status: response.status, body }
}

export const api = {
  login: (email, password) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  // language omitted by default -- the backend auto-detects it from the
  // question text (Arabic in, Arabic out; English in, English out).
  // Pass an explicit language only to override that.
  sendMessage: ({ question, language, conversationId }) =>
    request("/chat", {
      method: "POST",
      body: JSON.stringify({
        question,
        language: language || undefined,
        conversation_id: conversationId || undefined,
      }),
    }),

  // messageId comes from a previous sendMessage() response's message_id field.
  sendFeedback: ({ messageId, isHelpful, comment }) =>
    request("/feedback", {
      method: "POST",
      body: JSON.stringify({
        message_id: messageId,
        is_helpful: isHelpful,
        comment: comment || undefined,
      }),
    }),

  // Conversation history sidebar
  listConversations: () => request("/conversations", { method: "GET" }),

  getConversation: (conversationId) =>
    request(`/conversations/${conversationId}`, { method: "GET" }),

  renameConversation: (conversationId, title) =>
    request(`/conversations/${conversationId}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    }),
}
