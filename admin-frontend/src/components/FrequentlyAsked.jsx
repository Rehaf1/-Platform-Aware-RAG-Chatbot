import { useEffect, useState } from "react"
import { api } from "../api/client"
import { useLanguage } from "../context/LanguageContext"

export default function FrequentlyAsked() {
  const { t } = useLanguage()
  const [state, setState] = useState({ loading: true, error: null, items: [] })

  useEffect(() => {
    api.frequentlyAsked().then((res) => {
      if (res.ok) {
        setState({ loading: false, error: null, items: res.body.top_unanswered_questions })
      } else {
        setState({ loading: false, error: res.body?.detail || "Could not load.", items: [] })
      }
    })
  }, [])

  return (
    <div>
      <h1 className="font-display text-2xl font-bold mb-1.5 dark:text-white">{t("faqTitle")}</h1>
      <p className="text-sm text-muted dark:text-white/50 mb-6">{t("faqSubtitle")}</p>

      <div className="bg-white dark:bg-indigo-deep/40 border border-line dark:border-white/10 rounded-xl p-6">
        {state.loading && <p className="text-sm text-muted dark:text-white/50">{t("loading")}</p>}
        {state.error && <p className="text-sm text-garnet">{state.error}</p>}
        {!state.loading && !state.error && state.items.length === 0 && (
          <div className="text-center py-10">
            <p className="text-sm text-muted dark:text-white/50">{t("nothingRecurring")}</p>
          </div>
        )}
        {state.items.map((q, i) => (
          <div key={i} className="flex justify-between items-center py-3 border-b border-line dark:border-white/10 last:border-0 text-sm dark:text-white">
            <span>{q.question}</span>
            <span className="text-xs font-mono bg-paper dark:bg-white/10 border border-line dark:border-white/15 rounded-full px-2.5 py-0.5 text-indigo dark:text-white shrink-0 ms-4">
              {q.times_asked}×
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
