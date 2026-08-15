import { useState } from "react"
import { FileText, ChevronDown, ChevronUp } from "lucide-react"

export default function CitationList({ citations }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="text-xs">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 text-muted hover:text-indigo transition-colors"
      >
        <FileText size={12} />
        <span>{citations.length} source{citations.length !== 1 ? "s" : ""}</span>
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {open && (
        <ul className="mt-1.5 space-y-1.5 pl-1">
          {citations.map((c, i) => (
            <li key={i} className="border-l-2 border-line pl-2.5 py-0.5">
              <div className="font-medium text-ink">
                {c.document_name}
                {c.document_version && (
                  <span className="text-muted font-normal"> · v{c.document_version}</span>
                )}
                {c.section && <span className="text-muted font-normal"> · {c.section}</span>}
              </div>
              {c.excerpt && (
                <div className="text-muted mt-0.5 line-clamp-2">{c.excerpt}</div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
