import { useState } from "react"
import { ThumbsUp, ThumbsDown, Check } from "lucide-react"
import { api } from "../api/client"

export default function FeedbackButtons({ messageId }) {
  // "idle" -> "sending" -> "sent" (or back to "idle" on error, silently
  // retryable). Once sent, the choice is locked in -- matches the
  // one-shot feel of thumbs up/down elsewhere.
  const [status, setStatus] = useState("idle")
  const [choice, setChoice] = useState(null)

  async function rate(isHelpful) {
    if (status === "sending" || status === "sent") return
    setStatus("sending")
    setChoice(isHelpful)

    const { ok } = await api.sendFeedback({ messageId, isHelpful })
    setStatus(ok ? "sent" : "idle")
  }

  if (status === "sent") {
    return (
      <div className="flex items-center gap-1 text-xs text-mint">
        <Check size={12} />
        <span>Thanks for the feedback</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => rate(true)}
        disabled={status === "sending"}
        className={`p-1 rounded transition-colors ${
          choice === true ? "text-mint" : "text-muted hover:text-mint"
        }`}
        title="Helpful"
      >
        <ThumbsUp size={13} />
      </button>
      <button
        onClick={() => rate(false)}
        disabled={status === "sending"}
        className={`p-1 rounded transition-colors ${
          choice === false ? "text-garnet" : "text-muted hover:text-garnet"
        }`}
        title="Not helpful"
      >
        <ThumbsDown size={13} />
      </button>
    </div>
  )
}
