import { User, Bot, ShieldAlert } from "lucide-react"
import FeedbackButtons from "./FeedbackButtons"
import CitationList from "./CitationList"

const ARABIC_PATTERN = /[\u0600-\u06FF]/

export default function MessageBubble({ message }) {
  const isUser = message.role === "user"
  const isArabic = ARABIC_PATTERN.test(message.content)

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center
          ${isUser ? "bg-indigo text-white" : "bg-mint-bg text-mint"}`}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      <div className={`max-w-[75%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-1.5`}>
        <div
          dir={isArabic ? "rtl" : "ltr"}
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap
            ${isUser
              ? "bg-indigo text-white rounded-tr-sm"
              : message.fallbackUsed
                ? "bg-garnet-bg text-ink rounded-tl-sm border border-garnet/20"
                : "bg-white text-ink rounded-tl-sm border border-line"}`}
        >
          {message.fallbackUsed && !isUser && (
            <div className="flex items-center gap-1.5 text-garnet text-xs font-medium mb-1.5">
              <ShieldAlert size={13} />
              <span>{isArabic ? "لم يتم العثور على إجابة دقيقة" : "No confident answer found"}</span>
            </div>
          )}
          {message.content}
        </div>

        {!isUser && message.citations?.length > 0 && (
          <CitationList citations={message.citations} />
        )}

        {!isUser && message.messageId && (
          <FeedbackButtons messageId={message.messageId} />
        )}
      </div>
    </div>
  )
}