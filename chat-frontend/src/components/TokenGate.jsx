import { useState } from "react"
import { KeyRound } from "lucide-react"
import { setToken } from "../api/client"

/**
 * Stand-in for a real login screen. Each APTWatch platform is expected
 * to issue its own JWT and hand it to this frontend (e.g. embedded as a
 * query param when launching the chat widget) -- this manual paste box
 * exists only so the chat UI is testable before that integration exists.
 */
export default function TokenGate({ onTokenSet }) {
  const [value, setValue] = useState("")

  function submit(e) {
    e.preventDefault()
    if (!value.trim()) return
    setToken(value.trim())
    onTokenSet()
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper px-4">
      <form
        onSubmit={submit}
        className="bg-white border border-line rounded-2xl p-8 w-full max-w-sm shadow-sm"
      >
        <div className="w-10 h-10 rounded-lg bg-indigo flex items-center justify-center text-white mb-4">
          <KeyRound size={18} />
        </div>
        <h2 className="font-display text-lg font-semibold mb-1">Sign in</h2>
        <p className="text-sm text-muted mb-4">
          Paste your session token to start chatting.
        </p>
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Bearer token"
          className="w-full rounded-lg border border-line px-3 py-2 text-sm font-mono
            focus:outline-none focus:ring-2 focus:ring-indigo/30 focus:border-indigo mb-4"
        />
        <button
          type="submit"
          className="w-full bg-indigo text-white rounded-lg py-2 text-sm font-medium
            hover:bg-indigo-deep transition-colors"
        >
          Continue
        </button>
      </form>
    </div>
  )
}
