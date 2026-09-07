import { useEffect, useState, useRef } from "react"
import { MessageSquare, Plus, Loader2, Pencil, Check, X } from "lucide-react"
import { api } from "../api/client"
import { useLanguage } from "../context/LanguageContext.jsx"

const ARABIC_PATTERN = /[\u0600-\u06FF]/

/**
 * Formats an ISO timestamp for the sidebar the same way most chat apps
 * do: just the time if it's today, otherwise a short date. Avoids
 * showing a full date+time stamp for every single entry, which reads as
 * noisy clutter in a narrow sidebar.
 */
function formatConversationDate(isoString) {
  const date = new Date(isoString)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()

  if (isToday) {
    return date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })
  }
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

/**
 * Lists the user's past conversations (GET /api/v1/conversations) and
 * lets them click one to reload it (GET /api/v1/conversations/{id}), or
 * rename it inline (PATCH /api/v1/conversations/{id}).
 */
export default function ConversationSidebar({
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  refreshKey,
}) {
  const { t } = useLanguage()
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState(null)
  const [editingValue, setEditingValue] = useState("")
  const editInputRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api.listConversations().then(({ ok, body }) => {
      if (cancelled) return
      if (ok) setConversations(body.conversations)
      setLoading(false)
    })
    return () => {
      cancelled = true
    }
  }, [refreshKey])

  useEffect(() => {
    if (editingId) editInputRef.current?.focus()
  }, [editingId])

  function startEditing(e, conv) {
    e.stopPropagation()
    setEditingId(conv.id)
    setEditingValue(conv.title || "")
  }

  function cancelEditing(e) {
    e?.stopPropagation()
    setEditingId(null)
    setEditingValue("")
  }

  async function saveEditing(e, conversationId) {
    e.stopPropagation()
    const trimmed = editingValue.trim()
    if (!trimmed) return cancelEditing()

    const { ok, body } = await api.renameConversation(conversationId, trimmed)
    if (ok) {
      setConversations((prev) =>
        prev.map((c) => (c.id === conversationId ? { ...c, title: body.title } : c))
      )
    }
    setEditingId(null)
    setEditingValue("")
  }

  return (
    <div className="w-64 shrink-0 border-r border-line dark:border-white/10 bg-paper dark:bg-[#1D1730] flex flex-col h-full">
      <div className="p-3">
        <button
          onClick={onNewConversation}
          className="w-full flex items-center gap-2 text-sm font-medium text-white
            bg-indigo hover:bg-indigo-deep rounded-lg px-3 py-2 transition-colors"
        >
          <Plus size={15} />
          {t("newChat")}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-3 space-y-1">
        {loading && (
          <div className="flex items-center justify-center py-8 text-muted">
            <Loader2 size={16} className="animate-spin" />
          </div>
        )}

        {!loading && conversations.length === 0 && (
          <div className="text-xs text-muted dark:text-white/40 text-center py-8 px-3">
            {t("noConversations")}
          </div>
        )}

        {conversations.map((c) => {
          const isActive = c.id === activeConversationId
          const isEditing = editingId === c.id
          const isArabic = ARABIC_PATTERN.test(c.title || "")

          if (isEditing) {
            return (
              <div
                key={c.id}
                className="flex items-center gap-1 rounded-lg px-2 py-1.5 bg-indigo/5"
              >
                <input
                  ref={editInputRef}
                  value={editingValue}
                  onChange={(e) => setEditingValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") saveEditing(e, c.id)
                    if (e.key === "Escape") cancelEditing(e)
                  }}
                  dir="auto"
                  className={`flex-1 min-w-0 text-sm bg-white border border-indigo/30 rounded px-2 py-1
                    focus:outline-none focus:ring-1 focus:ring-indigo ${isArabic ? "font-arabic" : ""}`}
                />
                <button
                  onClick={(e) => saveEditing(e, c.id)}
                  className="shrink-0 text-mint hover:bg-mint-bg rounded p-1"
                  title="Save"
                >
                  <Check size={14} />
                </button>
                <button
                  onClick={cancelEditing}
                  className="shrink-0 text-muted hover:bg-line/60 rounded p-1"
                  title="Cancel"
                >
                  <X size={14} />
                </button>
              </div>
            )
          }

          return (
            <button
              key={c.id}
              onClick={() => onSelectConversation(c.id)}
              className={`group w-full flex items-start gap-2 text-left rounded-lg px-3 py-2
                transition-colors ${
                  isActive ? "bg-indigo/10 dark:bg-indigo/25 text-indigo dark:text-white" : "text-ink dark:text-white/80 hover:bg-line/60 dark:hover:bg-white/5"
                }`}
            >
              <MessageSquare size={14} className="shrink-0 mt-0.5 opacity-60" />
              <div className="flex-1 min-w-0">
                <div
                  dir="auto"
                  className={`truncate text-sm ${isActive ? "font-medium" : ""} ${isArabic ? "font-arabic" : ""}`}
                >
                  {c.title || t("untitledConversation")}
                </div>
                <div className="text-[11px] text-muted dark:text-white/40 mt-0.5">
                  {formatConversationDate(c.created_at)}
                </div>
              </div>
              <span
                onClick={(e) => startEditing(e, c)}
                className="shrink-0 opacity-0 group-hover:opacity-60 hover:!opacity-100
                  text-muted hover:text-indigo p-1 -m-1 rounded"
                title="Rename"
              >
                <Pencil size={12} />
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
