import { useEffect, useState } from "react"
import { api } from "../api/client"

export default function UnansweredQuestions() {
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
      <h1 className="font-display text-2xl font-bold mb-1.5">Unanswered Questions</h1>
      <p className="text-sm text-muted mb-6">
        Questions the knowledge base couldn't ground an answer to, for your platform.
      </p>

      <div className="bg-white border border-line rounded-xl p-6">
        {state.loading && <p className="text-sm text-muted">Loading…</p>}
        {state.error && <p className="text-sm text-garnet">{state.error}</p>}
        {!state.loading && !state.error && state.questions.length === 0 && (
          <div className="text-center py-10">
            <p className="text-sm text-muted">Nothing unanswered yet — good sign.</p>
          </div>
        )}
        {state.questions.map((q, i) => (
          <div key={i} className="flex justify-between items-center py-3 border-b border-line last:border-0 text-sm">
            <span>{q.question}</span>
            <span className="text-xs font-mono text-muted shrink-0 ml-4">
              {new Date(q.timestamp).toLocaleDateString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
