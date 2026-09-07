import { useState } from "react"
import { Mail, Lock, LogIn } from "lucide-react"
import { api, setToken } from "../api/client"
import { useLanguage } from "../context/LanguageContext.jsx"

/**
 * Real email+password login (POST /api/v1/auth/login), replacing the old
 * manual-token paste box. Accounts are created ahead of time by an admin
 * (POST /api/v1/admin/accounts) -- there is no self-signup here, by
 * design: platform/tenant/role assignment has to be a deliberate admin
 * action, not something a user picks for themselves.
 */
export default function LoginForm({ onLoggedIn }) {
  const { t } = useLanguage()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    const { ok, body } = await api.login(email.trim(), password)

    setSubmitting(false)

    if (!ok) {
      setError(body?.detail || "Invalid email or password.")
      return
    }

    setToken(body.access_token)
    onLoggedIn()
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper px-4">
      <form
        onSubmit={submit}
        className="bg-white border border-line rounded-2xl p-8 w-full max-w-sm shadow-sm"
      >
        <div className="w-10 h-10 rounded-lg bg-indigo flex items-center justify-center text-white mb-4">
          <LogIn size={18} />
        </div>
        <h2 className="font-display text-lg font-semibold mb-1">{t("signInTitle")}</h2>
        <p className="text-sm text-muted mb-5">
          Sign in with the account your administrator created for you.
        </p>

        <div className="space-y-3 mb-4">
          <div className="relative">
            <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full rounded-lg border border-line pl-9 pr-3 py-2 text-sm
                focus:outline-none focus:ring-2 focus:ring-indigo/30 focus:border-indigo"
            />
          </div>

          <div className="relative">
            <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full rounded-lg border border-line pl-9 pr-3 py-2 text-sm
                focus:outline-none focus:ring-2 focus:ring-indigo/30 focus:border-indigo"
            />
          </div>
        </div>

        {error && (
          <div className="text-xs text-garnet bg-garnet-bg rounded-lg py-2 px-3 mb-4">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-indigo text-white rounded-lg py-2 text-sm font-medium
            hover:bg-indigo-deep transition-colors disabled:opacity-60"
        >
          {submitting ? "..." : t("continue")}
        </button>
      </form>
    </div>
  )
}
