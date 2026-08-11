import { useEffect, useState } from "react"
import { api } from "../api/client"

export default function FrequentlyAsked() {
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
      <h1 className="font-display text-2xl font-bold mb-1.5">Frequently Asked</h1>
      <p className="text-sm text-muted mb-6">
        The unanswered questions your platform sees most often — good candidates for new documentation.
      </p>

      <div className="bg-white border border-line rounded-xl p-6">
        {state.loading && <p className="text-sm text-muted">Loading…</p>}
        {state.error && <p className="text-sm text-garnet">{state.error}</p>}
        {!state.loading && !state.error && state.items.length === 0 && (
          <div className="text-center py-10">
            <p className="text-sm text-muted">Nothing recurring yet.</p>
          </div>
        )}
        {state.items.map((q, i) => (
          <div key={i} className="flex justify-between items-center py-3 border-b border-line last:border-0 text-sm">
            <span>{q.question}</span>
            <span className="text-xs font-mono bg-paper border border-line rounded-full px-2.5 py-0.5 text-indigo shrink-0 ml-4">
              {q.times_asked}×
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
