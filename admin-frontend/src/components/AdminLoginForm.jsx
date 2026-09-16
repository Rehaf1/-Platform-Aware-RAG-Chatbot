import { useState } from "react"
import { LogIn, Mail, Lock } from "lucide-react"
import { api, setToken } from "../api/client"

/**
 * Real email+password login for the admin panel (POST /api/v1/auth/login),
 * replacing the manual-token paste box that used to live in Sidebar.jsx.
 * Uses the exact same login endpoint as the chat frontend -- the backend
 * doesn't distinguish "admin login" from "chat user login", it just
 * issues a token carrying whatever role the account actually has. An
 * account created without the "admin" role would still be able to log
 * in here, but every admin-only endpoint (upload, delete, reindex,
 * create account) independently re-checks the role server-side via
 * require_admin, so this page itself doesn't need to gatekeep who's
 * allowed to attempt a login.
 */
export default function AdminLoginForm({ onLoggedIn }) {
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
    <div className="min-h-screen flex items-center justify-center bg-paper dark:bg-[#16101f] px-4">
      <form
        onSubmit={submit}
        className="bg-white dark:bg-[#1D1730] border border-line dark:border-white/10
          rounded-2xl p-8 w-full max-w-sm shadow-sm"
      >
        <div className="w-10 h-10 rounded-lg bg-indigo flex items-center justify-center text-white mb-4">
          <LogIn size={18} />
        </div>
        <h2 className="font-display text-lg font-semibold mb-1 dark:text-white">
          Admin Sign In
        </h2>
        <p className="text-sm text-muted dark:text-white/50 mb-5">
          Sign in with your admin account to manage documents and users.
        </p>

        <div className="space-y-3 mb-4">
          <div className="relative">
            <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@example.com"
              className="w-full rounded-lg border border-line dark:border-white/10 dark:bg-[#241832]
                dark:text-white pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo/30"
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
              className="w-full rounded-lg border border-line dark:border-white/10 dark:bg-[#241832]
                dark:text-white pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo/30"
            />
          </div>
        </div>

        {error && (
          <div className="text-xs text-garnet bg-garnet-bg dark:bg-garnet/15 rounded-lg py-2 px-3 mb-4">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-indigo text-white rounded-lg py-2 text-sm font-medium
            hover:bg-indigo-deep transition-colors disabled:opacity-60"
        >
          {submitting ? "..." : "Sign In"}
        </button>
      </form>
    </div>
  )
}
