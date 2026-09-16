import { Sun, Moon, Languages, LogOut } from "lucide-react"
import { setToken } from "../api/client"
import { useTheme } from "../context/ThemeContext"
import { useLanguage } from "../context/LanguageContext"

export default function Sidebar({ active, onNavigate }) {
  const { theme, toggleTheme } = useTheme()
  const { t, toggleLanguage } = useLanguage()

  const NAV_ITEMS = [
    { id: "documents", label: t("navDocuments") },
    { id: "unanswered", label: t("navUnanswered") },
    { id: "faq", label: t("navFaq") },
    { id: "accounts", label: "Accounts" },
  ]

  function handleLogout() {
    // Clears the token and reloads -- App.jsx's hasToken check then
    // falls back to the login screen. A full reload (rather than a
    // state flip) also resets any in-memory data tied to the previous
    // session (uploaded document lists, etc.).
    setToken("")
    window.location.reload()
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
        <button
          type="button"
          onClick={handleLogout}
          className="flex items-center gap-2 text-xs text-white/60 hover:text-white transition-colors"
        >
          <LogOut size={14} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
