import { useState } from "react"
import { getToken, setToken } from "../api/client"

const NAV_ITEMS = [
  { id: "documents", label: "Documents" },
  { id: "unanswered", label: "Unanswered Questions" },
  { id: "faq", label: "Frequently Asked" },
]

export default function Sidebar({ active, onNavigate }) {
  const [tokenValue, setTokenValue] = useState(getToken())

  function handleTokenChange(e) {
    const value = e.target.value.trim()
    setTokenValue(value)
    setToken(value)
  }

  return (
    <aside className="w-64 shrink-0 bg-indigo-deep text-white flex flex-col p-6">
      <div className="mb-8">
        <div className="font-display text-xl font-bold">APTWatch</div>
        <div className="text-xs text-white/50 tracking-wide mt-0.5">Knowledge Base Admin</div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`text-left px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              active === item.id
                ? "bg-indigo text-white"
                : "text-white/70 hover:bg-white/5"
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div className="mt-auto pt-5 border-t border-white/10">
        <label className="block text-[11px] uppercase tracking-wide text-white/40 mb-2 font-medium">
          Admin token
        </label>
        <textarea
          rows={3}
          value={tokenValue}
          onChange={handleTokenChange}
          placeholder="Paste your bearer token"
          className="w-full bg-white/8 border border-white/15 rounded-md px-2.5 py-2 text-[11px] font-mono text-white placeholder:text-white/30 resize-none focus:outline-none focus:border-amber"
        />
        <div className={`text-[11px] mt-1.5 ${tokenValue ? "text-mint" : "text-white/40"}`}>
          {tokenValue ? "Token set" : "No token — actions will fail"}
        </div>
      </div>
    </aside>
  )
}
