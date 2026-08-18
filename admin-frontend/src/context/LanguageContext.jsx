import { createContext, useContext, useEffect, useState } from "react"
import { translations } from "../i18n/translations"

const LanguageContext = createContext(null)

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => localStorage.getItem("aptwatch_lang") || "en")

  useEffect(() => {
    const root = document.documentElement
    root.dir = language === "ar" ? "rtl" : "ltr"
    root.lang = language
    localStorage.setItem("aptwatch_lang", language)
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
