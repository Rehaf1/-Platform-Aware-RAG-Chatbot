import { createContext, useContext, useEffect, useState } from "react"
import { translations } from "../i18n/translations"

const LanguageContext = createContext(null)

/**
 * This toggle controls the UI chrome (buttons, placeholders, header
 * text) -- it's independent from the backend's per-message language
 * auto-detection (Arabic question -> Arabic answer). It does NOT flip
 * the page's overall layout direction (dir on <html>) -- that would
 * mirror the entire flex layout (sidebar side, rounded corners, borders)
 * which is a much bigger visual change than "translate the text".
 * Individual RTL text alignment is applied locally, per element, where
 * needed (see App.jsx / ConversationSidebar.jsx / MessageInput.jsx).
 */
export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => localStorage.getItem("aptwatch_chat_lang") || "en")

  useEffect(() => {
    localStorage.setItem("aptwatch_chat_lang", language)
  }, [language])

  function toggleLanguage() {
    setLanguage((l) => (l === "en" ? "ar" : "en"))
  }

  function t(key) {
    return translations[language]?.[key] ?? translations.en[key] ?? key
  }

  return (
    <LanguageContext.Provider value={{ language, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error("useLanguage must be used inside a LanguageProvider")
  return ctx
}