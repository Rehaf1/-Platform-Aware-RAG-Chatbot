import { useState } from "react"
import { SendHorizontal } from "lucide-react"
import { useLanguage } from "../context/LanguageContext.jsx"

const ARABIC_PATTERN = /[\u0600-\u06FF]/

export default function MessageInput({ onSend, disabled }) {
  const { t, language } = useLanguage()
  const [value, setValue] = useState("")
  const isArabic = ARABIC_PATTERN.test(value)

  function submit(e) {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue("")
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      submit(e)
    }
  }

  return (
    <form onSubmit={submit} className="flex items-end gap-2 p-4 border-t border-line dark:border-white/10 bg-white dark:bg-[#1D1730] rounded-b-2xl">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        dir={language === "ar" ? "rtl" : "ltr"}
        placeholder={t("inputPlaceholder")}
        rows={1}
        disabled={disabled}
        className={`flex-1 resize-none rounded-xl border border-line dark:border-white/10 dark:bg-[#241832] dark:text-white/90 px-3.5 py-2.5 text-sm
          focus:outline-none focus:ring-2 focus:ring-indigo/30 focus:border-indigo
          disabled:opacity-60 disabled:cursor-not-allowed max-h-32
          ${isArabic ? "font-arabic" : ""}`}
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="shrink-0 w-10 h-10 rounded-xl bg-indigo text-white flex items-center
          justify-center hover:bg-indigo-deep transition-colors disabled:opacity-40
          disabled:cursor-not-allowed"
      >
        <SendHorizontal size={17} />
      </button>
    </form>
  )
}
