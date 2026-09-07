import { useState } from "react"
import { Eye, EyeOff, Sun, Moon, Languages } from "lucide-react"
import { getToken, setToken } from "../api/client"
import { useTheme } from "../context/ThemeContext"
import { useLanguage } from "../context/LanguageContext"

export default function Sidebar({ active, onNavigate }) {
  const [tokenValue, setTokenValue] = useState(getToken())
  const [showToken, setShowToken] = useState(false)
  const { theme, toggleTheme } = useTheme()
  const { t, toggleLanguage } = useLanguage()

  const NAV_ITEMS = [
    { id: "documents", label: t("navDocuments") },
    { id: "unanswered", label: t("navUnanswered") },
    { id: "faq", label: t("navFaq") },
    { id: "accounts", label: "Accounts" },
  ]

  function handleTokenChange(e) {
    const value = e.target.value.trim()
    setTokenValue(value)
    setToken(value)
  }

  return (
    <aside className="w-64 shrink-0 bg-indigo-deep text-white flex flex-col p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="font-display text-xl font-bold">APTWatch</div>
          <div className="text-xs text-white/50 tracking-wide mt-0.5">{t("brandSub")}</div>
        </div>
        <div className="flex gap-1.5">
          <button
            type="button"
            onClick={toggleTheme}
            title={t("toggleTheme")}
            className="p-1.5 rounded-md text-white/60 hover:text-white hover:bg-white/10"
          >
            {theme === "light" ? <Moon size={15} /> : <Sun size={15} />}
          </button>
          <button
            type="button"
            onClick={toggleLanguage}
            title={t("toggleLanguage")}
            className="p-1.5 rounded-md text-white/60 hover:text-white hover:bg-white/10"
          >
            <Languages size={15} />
          </button>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`text-start px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              active === item.id
                ? "bg-indigo text-white"
                : "text-white/70 hover:bg-white/5"
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <a
        href="http://localhost:5174"
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs text-white/50 hover:text-white/80 mt-4 mb-2 inline-block"
      >
        → {t("openChat")}
      </a>

      <div className="mt-auto pt-5 border-t border-white/10">
        <label className="block text-[11px] uppercase tracking-wide text-white/40 mb-2 font-medium">
          {t("adminToken")}
        </label>
        <div className="relative">
          <input
            type={showToken ? "text" : "password"}
            value={tokenValue}
            onChange={handleTokenChange}
            placeholder={t("tokenPlaceholder")}
            className="w-full bg-white/8 border border-white/15 rounded-md ps-2.5 pe-8 py-2 text-[11px] font-mono text-white placeholder:text-white/30 focus:outline-none focus:border-amber"
          />
          <button
            type="button"
            onClick={() => setShowToken((s) => !s)}
            className="absolute end-2 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70"
          >
            {showToken ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        </div>
        <div className={`text-[11px] mt-1.5 ${tokenValue ? "text-mint" : "text-white/40"}`}>
          {tokenValue ? t("tokenSet") : t("tokenNotSet")}
        </div>
      </div>
    </aside>
  )
}
