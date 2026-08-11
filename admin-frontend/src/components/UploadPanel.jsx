import { useState, useRef } from "react"
import { api } from "../api/client"
import PipelineTrail from "./PipelineTrail"

export default function UploadPanel({ onUploaded }) {
  const [file, setFile] = useState(null)
  const [module, setModule] = useState("")
  const [accessLevel, setAccessLevel] = useState("")
  const [roles, setRoles] = useState("")
  const [version, setVersion] = useState("1.0")
  const [stage, setStage] = useState(-1)
  const [result, setResult] = useState(null)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)

  async function handleUpload() {
    if (!file) return
    setUploading(true)
    setResult(null)
    setStage(0)

    const tick = setInterval(() => setStage((s) => (s < 4 ? s + 1 : s)), 350)

    const form = new FormData()
    form.append("file", file)
    if (module) form.append("module", module)
    if (accessLevel) form.append("access_level", accessLevel)
    if (roles) form.append("roles", roles)
    if (version) form.append("version", version)

    const res = await api.uploadDocument(form)
    clearInterval(tick)
    setUploading(false)
    setResult(res)
    setStage(res.ok ? 6 : -2)

    if (res.ok) {
      setFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ""
      onUploaded?.()
    }
  }

  return (
    <div className="bg-white border border-line rounded-xl p-6">
      <h2 className="font-display text-lg font-semibold mb-4">Upload a document</h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="block text-xs font-semibold text-muted mb-1.5">File</label>
          <input
            ref={fileInputRef}
            type="file"
            onChange={(e) => setFile(e.target.files[0] || null)}
            className="w-full text-sm border border-line rounded-lg px-3 py-2 bg-paper file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:bg-indigo file:text-white file:text-xs file:font-medium"
          />
        </div>

        <Field label="Module" value={module} onChange={setModule} placeholder="e.g. compliance" optional />
        <Field label="Access level" value={accessLevel} onChange={setAccessLevel} placeholder="e.g. internal" optional />
        <Field label="Roles" value={roles} onChange={setRoles} placeholder="compliance_manager,auditor" optional />
        <Field label="Version" value={version} onChange={setVersion} placeholder="1.0" />
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="mt-5 bg-amber hover:bg-amber-hover text-white text-sm font-semibold px-4 py-2 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {uploading ? "Uploading…" : "Upload document"}
      </button>

      {stage > -1 && <PipelineTrail stage={stage} />}

      {result && (
        <div
          className={`mt-4 rounded-lg p-3.5 text-xs font-mono whitespace-pre-wrap ${
            result.ok ? "bg-mint-bg text-mint" : "bg-garnet-bg text-garnet"
          }`}
        >
          {JSON.stringify(result.body, null, 2)}
        </div>
      )}
    </div>
  )
}

function Field({ label, value, onChange, placeholder, optional }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-muted mb-1.5">
        {label} {optional && <span className="font-normal text-muted/60">(optional)</span>}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full text-sm border border-line rounded-lg px-3 py-2 bg-paper focus:outline-none focus:border-indigo"
      />
    </div>
  )
}
