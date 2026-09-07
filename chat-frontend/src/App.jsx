import { useState, useRef, useEffect } from "react"
import ChatHeader from "./components/ChatHeader"
import MessageBubble from "./components/MessageBubble"
import MessageInput from "./components/MessageInput"
import LoginForm from "./components/LoginForm"
import ConversationSidebar from "./components/ConversationSidebar"
import { useLanguage } from "./context/LanguageContext.jsx"
import {
  api,
  getToken,
  getConversationId,
  setConversationId,
  clearConversationId,
} from "./api/client"

export default function App() {
  const { t } = useLanguage()
  const [hasToken, setHasToken] = useState(!!getToken())
  const [messages, setMessages] = useState([])
  const [sending, setSending] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [error, setError] = useState(null)
  const [activeConversationId, setActiveConversationId] = useState(getConversationId())
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, sending])

  async function handleSend(question) {
    setError(null)
    setMessages((prev) => [...prev, { role: "user", content: question }])
    setSending(true)

    const wasNewConversation = !getConversationId()

    const { ok, status, body } = await api.sendMessage({
      question,
      conversationId: getConversationId(),
    })

    setSending(false)

    if (!ok) {
      if (status === 401) {
        setError(t("sessionExpired"))
      } else {
        setError(body?.detail || t("genericError"))
      }
      return
    }

    if (body.conversation_id) {
      setConversationId(body.conversation_id)
      setActiveConversationId(body.conversation_id)
    }

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: body.answer,
        citations: body.citations,
        fallbackUsed: body.fallback_used,
        messageId: body.message_id,
      },
    ])

    if (wasNewConversation) {
      setSidebarRefreshKey((k) => k + 1)
    }
  }

  function handleNewConversation() {
    clearConversationId()
    setActiveConversationId(null)
    setMessages([])
    setError(null)
  }

  async function handleSelectConversation(conversationId) {
    setError(null)
    setLoadingHistory(true)
    const { ok, body } = await api.getConversation(conversationId)
    setLoadingHistory(false)

    if (!ok) {
      setError(t("genericError"))
      return
    }

    setConversationId(conversationId)
    setActiveConversationId(conversationId)
    setMessages(
      body.messages.map((m) => ({
        role: m.role,
        content: m.content,
        citations: m.citations,
        fallbackUsed: m.fallback_used,
      }))
    )
  }

  if (!hasToken) {
    return <LoginForm onLoggedIn={() => setHasToken(true)} />
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper dark:bg-[#16101f] px-4 py-8">
      <div
        className="flex w-full max-w-5xl h-[85vh] bg-white dark:bg-[#1D1730]
          border border-line dark:border-white/10 rounded-2xl shadow-lg overflow-hidden"
      >
        <ConversationSidebar
          activeConversationId={activeConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          refreshKey={sidebarRefreshKey}
        />

        <div className="flex flex-col flex-1 min-w-0">
          <ChatHeader onNewConversation={handleNewConversation} />

          <div className="flex-1 overflow-y-auto px-5 py-6 space-y-5 bg-paper dark:bg-[#16101f]">
            {loadingHistory && (
              <div className="text-center text-muted dark:text-white/60 text-sm mt-16">
                {t("loadingConversation")}
              </div>
            )}

            {!loadingHistory && messages.length === 0 && (
              <div className="text-center text-muted dark:text-white/60 text-sm mt-16">
                {t("getStarted")}
              </div>
            )}

            {!loadingHistory &&
              messages.map((m, i) => <MessageBubble key={i} message={m} />)}

            {sending && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-mint-bg dark:bg-mint/20 flex items-center justify-center shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-mint animate-pulse" />
                </div>
                <div className="bg-white dark:bg-[#241832] border border-line dark:border-white/10 rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm text-muted dark:text-white/60">
                  {t("thinking")}
                </div>
              </div>
            )}

            {error && (
              <div className="text-center text-xs text-garnet bg-garnet-bg dark:bg-garnet/15 rounded-lg py-2 px-3">
                {error}
              </div>
            )}

            <div ref={scrollRef} />
          </div>

          <MessageInput onSend={handleSend} disabled={sending} />
        </div>
      </div>
    </div>
  )
}
