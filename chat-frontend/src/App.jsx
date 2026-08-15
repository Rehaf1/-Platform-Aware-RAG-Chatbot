import { useState, useRef, useEffect } from "react"
import ChatHeader from "./components/ChatHeader"
import MessageBubble from "./components/MessageBubble"
import MessageInput from "./components/MessageInput"
import TokenGate from "./components/TokenGate"
import { api, getToken, getConversationId, setConversationId, clearConversationId } from "./api/client"

export default function App() {
  const [hasToken, setHasToken] = useState(!!getToken())
  const [messages, setMessages] = useState([])
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, sending])

  async function handleSend(question) {
    setError(null)
    setMessages((prev) => [...prev, { role: "user", content: question }])
    setSending(true)

    const { ok, status, body } = await api.sendMessage({
      question,
      conversationId: getConversationId(),
    })

    setSending(false)

    if (!ok) {
      if (status === 401) {
        setError("Your session has expired. Please sign in again.")
      } else {
        setError(body?.detail || "Something went wrong. Please try again.")
      }
      return
    }

    if (body.conversation_id) setConversationId(body.conversation_id)

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
  }

  function handleNewConversation() {
    clearConversationId()
    setMessages([])
    setError(null)
  }

  if (!hasToken) {
    return <TokenGate onTokenSet={() => setHasToken(true)} />
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper px-4 py-8">
      <div
        className="flex flex-col w-full max-w-3xl h-[85vh] bg-white
          border border-line rounded-2xl shadow-lg overflow-hidden"
      >
        <ChatHeader onNewConversation={handleNewConversation} />

        <div className="flex-1 overflow-y-auto px-5 py-6 space-y-5 bg-paper">
          {messages.length === 0 && (
            <div className="text-center text-muted text-sm mt-16">
              Ask a question to get started -- answers are grounded in your
              platform's approved documentation.
            </div>
          )}

          {messages.map((m, i) => (
            <MessageBubble key={i} message={m} />
          ))}

          {sending && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-mint-bg flex items-center justify-center shrink-0">
                <span className="w-1.5 h-1.5 rounded-full bg-mint animate-pulse" />
              </div>
              <div className="bg-white border border-line rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm text-muted">
                Thinking...
              </div>
            </div>
          )}

          {error && (
            <div className="text-center text-xs text-garnet bg-garnet-bg rounded-lg py-2 px-3">
              {error}
            </div>
          )}

          <div ref={scrollRef} />
        </div>

        <MessageInput onSend={handleSend} disabled={sending} />
      </div>
    </div>
  )
}
