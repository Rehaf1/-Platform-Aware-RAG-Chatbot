import { useEffect, useState } from "react"
import { api } from "../api/client"
import StatusBadge from "./StatusBadge"
import { useLanguage } from "../context/LanguageContext"

export default function DocumentTable({ refreshSignal }) {
  const { t } = useLanguage()
  const [state, setState] = useState({ loading: true, error: null, documents: [] })
  const [actionInFlight, setActionInFlight] = useState(null)

  async function load() {
    setState((s) => ({ ...s, loading: true, error: null }))
    const res = await api.listDocuments()
    if (res.ok) {
      setState({ loading: false, error: null, documents: res.body.documents })
    } else {
      setState({ loading: false, error: res.body?.detail || "Could not load documents.", documents: [] })
    }
  }

  useEffect(() => {
    load()
  }, [refreshSignal])

  async function handleReindex(name) {
    setActionInFlight(name + ":reindex")
    await api.reindexDocument(name)
    setActionInFlight(null)
    load()
  }

  async function handleDelete(name) {
    setActionInFlight(name + ":delete")
    await api.deleteDocument(name)
    setActionInFlight(null)
    load()
  }

  if (state.loading) {
    return <div className="text-sm text-muted dark:text-white/50 py-8 text-center">{t("loadingDocuments")}</div>
  }

  if (state.error) {
    return (
      <div className="bg-garnet-bg dark:bg-garnet/10 text-garnet text-sm rounded-lg p-4">
        {t("couldNotLoad")} {state.error}
      </div>
    )
  }

  if (state.documents.length === 0) {
    return (
      <div className="text-center py-14 border border-dashed border-line dark:border-white/15 rounded-xl">
        <p className="text-sm text-muted dark:text-white/50">{t("noDocuments")}</p>
        <p className="text-xs text-muted/70 dark:text-white/30 mt-1">{t("noDocumentsHint")}</p>
      </div>
    )
  }

  return (
    <div className="border border-line dark:border-white/10 rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-paper dark:bg-white/5 border-b border-line dark:border-white/10 text-start">
            <th className="px-4 py-3 font-semibold text-muted dark:text-white/60 text-xs uppercase tracking-wide text-start">{t("tableDocument")}</th>
            <th className="px-4 py-3 font-semibold text-muted dark:text-white/60 text-xs uppercase tracking-wide text-start">{t("tableStatus")}</th>
            <th className="px-4 py-3 font-semibold text-muted dark:text-white/60 text-xs uppercase tracking-wide text-start">{t("tableModule")}</th>
            <th className="px-4 py-3 font-semibold text-muted dark:text-white/60 text-xs uppercase tracking-wide text-start">{t("tableLanguage")}</th>
            <th className="px-4 py-3 font-semibold text-muted dark:text-white/60 text-xs uppercase tracking-wide text-end">{t("tableActions")}</th>
          </tr>
        </thead>
        <tbody>
          {state.documents.map((doc) => (
            <tr key={doc.document_name} className="border-b border-line dark:border-white/10 last:border-0 hover:bg-paper/60 dark:hover:bg-white/5 dark:text-white">
              <td className="px-4 py-3 font-mono text-[13px]">{doc.document_name}</td>
              <td className="px-4 py-3"><StatusBadge status={doc.status} /></td>
              <td className="px-4 py-3 text-muted dark:text-white/50">{doc.module || "—"}</td>
              <td className="px-4 py-3 text-muted dark:text-white/50 uppercase text-xs">{doc.language || "—"}</td>
              <td className="px-4 py-3">
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => handleReindex(doc.document_name)}
                    disabled={actionInFlight === doc.document_name + ":reindex"}
                    className="text-xs font-medium text-indigo dark:text-white border border-line dark:border-white/20 rounded-md px-2.5 py-1 hover:bg-indigo/5 dark:hover:bg-white/10 disabled:opacity-50"
                  >
                    {actionInFlight === doc.document_name + ":reindex" ? t("reindexing") : t("reindex")}
                  </button>
                  <button
                    onClick={() => handleDelete(doc.document_name)}
                    disabled={actionInFlight === doc.document_name + ":delete"}
                    className="text-xs font-medium text-garnet border border-garnet/20 rounded-md px-2.5 py-1 hover:bg-garnet-bg dark:hover:bg-garnet/10 disabled:opacity-50"
                  >
                    {actionInFlight === doc.document_name + ":delete" ? t("deleting") : t("deleteAction")}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
