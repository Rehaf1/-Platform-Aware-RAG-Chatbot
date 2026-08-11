import { useEffect, useState } from "react"
import { api } from "../api/client"
import StatusBadge from "./StatusBadge"

export default function DocumentTable({ refreshSignal }) {
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
    return <div className="text-sm text-muted py-8 text-center">Loading documents…</div>
  }

  if (state.error) {
    return (
      <div className="bg-garnet-bg text-garnet text-sm rounded-lg p-4">
        Couldn't load documents: {state.error}
      </div>
    )
  }

  if (state.documents.length === 0) {
    return (
      <div className="text-center py-14 border border-dashed border-line rounded-xl">
        <p className="text-sm text-muted">No documents yet.</p>
        <p className="text-xs text-muted/70 mt-1">Upload one above to see it appear here.</p>
      </div>
    )
  }

  return (
    <div className="border border-line rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-paper border-b border-line text-left">
            <th className="px-4 py-3 font-semibold text-muted text-xs uppercase tracking-wide">Document</th>
            <th className="px-4 py-3 font-semibold text-muted text-xs uppercase tracking-wide">Status</th>
            <th className="px-4 py-3 font-semibold text-muted text-xs uppercase tracking-wide">Module</th>
            <th className="px-4 py-3 font-semibold text-muted text-xs uppercase tracking-wide">Language</th>
            <th className="px-4 py-3 font-semibold text-muted text-xs uppercase tracking-wide text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {state.documents.map((doc) => (
            <tr key={doc.document_name} className="border-b border-line last:border-0 hover:bg-paper/60">
              <td className="px-4 py-3 font-mono text-[13px]">{doc.document_name}</td>
              <td className="px-4 py-3"><StatusBadge status={doc.status} /></td>
              <td className="px-4 py-3 text-muted">{doc.module || "—"}</td>
              <td className="px-4 py-3 text-muted uppercase text-xs">{doc.language || "—"}</td>
              <td className="px-4 py-3">
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => handleReindex(doc.document_name)}
                    disabled={actionInFlight === doc.document_name + ":reindex"}
                    className="text-xs font-medium text-indigo border border-line rounded-md px-2.5 py-1 hover:bg-indigo/5 disabled:opacity-50"
                  >
                    {actionInFlight === doc.document_name + ":reindex" ? "Reindexing…" : "Reindex"}
                  </button>
                  <button
                    onClick={() => handleDelete(doc.document_name)}
                    disabled={actionInFlight === doc.document_name + ":delete"}
                    className="text-xs font-medium text-garnet border border-garnet/20 rounded-md px-2.5 py-1 hover:bg-garnet-bg disabled:opacity-50"
                  >
                    {actionInFlight === doc.document_name + ":delete" ? "Deleting…" : "Delete"}
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
