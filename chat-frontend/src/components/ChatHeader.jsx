import { RotateCcw, Sun, Moon, Languages } from "lucide-react"
import logo from "../assets/aptwatch-logo.png"
import { useTheme } from "../context/ThemeContext.jsx"
import { useLanguage } from "../context/LanguageContext.jsx"

export default function ChatHeader({ onNewConversation }) {
  const { theme, toggleTheme } = useTheme()
  const { language, toggleLanguage, t } = useLanguage()

  return (
    <div className="flex items-center justify-between px-5 py-4 border-b border-indigo-deep dark:border-white/10 bg-indigo-deep rounded-t-2xl">
      <div className="flex items-center gap-2.5">
        <img src={logo} alt="APTWatch" className="h-9 w-auto shrink-0" />
        <div>
          <h1 className="font-display font-semibold text-base leading-tight text-white">
            {t("brand")}
          </h1>
          <p className="text-xs text-white/60 leading-tight">{t("brandSub")}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={toggleLanguage}
          className="flex items-center gap-1 text-xs text-white/70 hover:text-white
            border border-white/20 hover:border-white/40 rounded-lg px-2.5 py-1.5 transition-colors"
          title="Toggle language"
        >
          <Languages size={13} />
          {language === "en" ? "AR" : "EN"}
        </button>

        <button
          onClick={toggleTheme}
          className="flex items-center text-xs text-white/70 hover:text-white
            border border-white/20 hover:border-white/40 rounded-lg p-1.5 transition-colors"
          title="Toggle theme"
        >
          {theme === "light" ? <Moon size={14} /> : <Sun size={14} />}
        </button>

        <button
          onClick={onNewConversation}
          className="flex items-center gap-1.5 text-xs text-white/70 hover:text-white
            border border-white/20 hover:border-white/40 rounded-lg px-3 py-1.5 transition-colors"
        >
          <RotateCcw size={13} />
          {t("newConversation")}
        </button>
      </div>
    </div>
  )
}
