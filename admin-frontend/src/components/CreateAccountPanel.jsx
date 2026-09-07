import { useState } from "react"
import { UserPlus, CheckCircle2 } from "lucide-react"
import { api } from "../api/client"

const ROLES = ["compliance_manager", "auditor", "admin"]

/**
 * Admin-only account creation (POST /api/v1/admin/accounts). This is
 * the ONLY way a chat-user or admin account comes into existence now --
 * there is no self-signup on the chat side. Platform/tenant/role are
 * set here explicitly by the admin, not inferred from anything the new
 * user could control themselves.
 */
export default function CreateAccountPanel() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [platformId, setPlatformId] = useState("imtithal")
  const [tenantId, setTenantId] = useState("demo_tenant")
  const [role, setRole] = useState("compliance_manager")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  async function submit(e) {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setSubmitting(true)

    const { ok, body } = await api.createAccount({
      email: email.trim(),
      password,
      platform_id: platformId.trim(),
      tenant_id: tenantId.trim(),
      role,
    })

    setSubmitting(false)

    if (!ok) {
      setError(body?.detail || "Could not create the account.")
      return
    }

    setSuccess(`Account created: ${body.email} (${body.platform_id}/${body.tenant_id}, ${body.role})`)
    setEmail("")
    setPassword("")
  }

  return (
    <div>
      <h1 className="font-display text-2xl font-bold mb-1.5 dark:text-white">
        Create Chat User Account
      </h1>
      <p className="text-sm text-muted dark:text-white/50 mb-6">
        Chat users don't self-register -- every account is created here by an
        admin, with its platform, tenant, and role set explicitly.
      </p>

      <form
        onSubmit={submit}
        className="max-w-md bg-white dark:bg-[#1D1730] border border-line dark:border-white/10
          rounded-2xl p-6 space-y-4"
      >
        <div>
          <label className="block text-xs font-medium text-muted dark:text-white/50 mb-1.5">
            Email
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="user@example.com"
            className="w-full rounded-lg border border-line dark:border-white/10 dark:bg-[#241832]
              dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo/30"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-muted dark:text-white/50 mb-1.5">
            Password
          </label>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 8 characters"
            className="w-full rounded-lg border border-line dark:border-white/10 dark:bg-[#241832]
              dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo/30"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-muted dark:text-white/50 mb-1.5">
              Platform
            </label>
            <input
              required
              value={platformId}
              onChange={(e) => setPlatformId(e.target.value)}
              className="w-full rounded-lg border border-line dark:border-white/10 dark:bg-[#241832]
                dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo/30"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-muted dark:text-white/50 mb-1.5">
              Tenant
            </label>
            <input
              required
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
              className="w-full rounded-lg border border-line dark:border-white/10 dark:bg-[#241832]
                dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo/30"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-muted dark:text-white/50 mb-1.5">
            Role
          </label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="w-full rounded-lg border border-line dark:border-white/10 dark:bg-[#241832]
              dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo/30"
          >
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="text-xs text-garnet bg-garnet-bg dark:bg-garnet/15 rounded-lg py-2 px-3">
            {error}
          </div>
        )}
        {success && (
          <div className="flex items-start gap-1.5 text-xs text-mint bg-mint-bg dark:bg-mint/15 rounded-lg py-2 px-3">
            <CheckCircle2 size={14} className="shrink-0 mt-0.5" />
            <span>{success}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full flex items-center justify-center gap-2 bg-indigo hover:bg-indigo-deep
            text-white rounded-lg py-2.5 text-sm font-medium transition-colors disabled:opacity-60"
        >
          <UserPlus size={15} />
          {submitting ? "Creating..." : "Create Account"}
        </button>
      </form>
    </div>
  )
}
