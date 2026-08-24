import { useEffect, useState } from "react"
import { api } from "../api/client"
import { useLanguage } from "../context/LanguageContext"

export default function UnansweredQuestions() {
  const { t } = useLanguage()
  const [state, setState] = useState({ loading: true, error: null, questions: [] })

  useEffect(() => {
    api.unansweredQuestions().then((res) => {
      if (res.ok) {
        setState({ loading: false, error: null, questions: res.body.questions })
      } else {
        setState({ loading: false, error: res.body?.detail || "Could not load.", questions: [] })
      }
    })
  }, [])

  return (
    <div>
      <h1 className="font-display text-2xl font-bold mb-1.5 dark:text-white">{t("unansweredTitle")}</h1>
      <p className="text-sm text-muted dark:text-white/50 mb-6">{t("unansweredSubtitle")}</p>

      <div className="bg-white dark:bg-indigo-deep/40 border border-line dark:border-white/10 rounded-xl p-6">
        {state.loading && <p className="text-sm text-muted dark:text-white/50">{t("loading")}</p>}
        {state.error && <p className="text-sm text-garnet">{state.error}</p>}
        {!state.loading && !state.error && state.questions.length === 0 && (
          <div className="text-center py-10">
            <p className="text-sm text-muted dark:text-white/50">{t("nothingUnanswered")}</p>
          </div>
        )}
        {state.questions.map((q, i) => (
          <div key={i} className="flex justify-between items-center py-3 border-b border-line dark:border-white/10 last:border-0 text-sm dark:text-white">
            <span>{q.question}</span>
            <span className="text-xs font-mono text-muted dark:text-white/40 shrink-0 ms-4">
              {new Date(q.timestamp).toLocaleDateString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
