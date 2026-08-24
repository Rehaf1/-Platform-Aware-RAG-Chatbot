import { useState, useRef } from "react"
import { api } from "../api/client"
import PipelineTrail from "./PipelineTrail"
import { useLanguage } from "../context/LanguageContext"

export default function UploadPanel({ onUploaded }) {
  const { t } = useLanguage()
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
    <div className="bg-white dark:bg-indigo-deep/40 border border-line dark:border-white/10 rounded-xl p-6">
      <h2 className="font-display text-lg font-semibold mb-4 dark:text-white">{t("uploadTitle")}</h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="block text-xs font-semibold text-muted dark:text-white/60 mb-1.5">{t("fieldFile")}</label>
          <input
            ref={fileInputRef}
            type="file"
            onChange={(e) => setFile(e.target.files[0] || null)}
            className="w-full text-sm border border-line dark:border-white/15 rounded-lg px-3 py-2 bg-paper dark:bg-white/5 dark:text-white file:me-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:bg-indigo file:text-white file:text-xs file:font-medium"
          />
        </div>

        <Field label={t("fieldModule")} value={module} onChange={setModule} placeholder="e.g. compliance" optional optLabel={t("optional")} />
        <Field label={t("fieldAccessLevel")} value={accessLevel} onChange={setAccessLevel} placeholder="e.g. internal" optional optLabel={t("optional")} />
        <Field label={t("fieldRoles")} value={roles} onChange={setRoles} placeholder="compliance_manager,auditor" optional optLabel={t("optional")} />
        <Field label={t("fieldVersion")} value={version} onChange={setVersion} placeholder="1.0" />
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="mt-5 bg-amber hover:bg-amber-hover text-white text-sm font-semibold px-4 py-2 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {uploading ? t("uploading") : t("uploadButton")}
      </button>

      {stage > -1 && <PipelineTrail stage={stage} />}

      {result && (
        <div
          className={`mt-4 rounded-lg p-3.5 text-xs font-mono whitespace-pre-wrap ${
            result.ok ? "bg-mint-bg dark:bg-mint/10 text-mint" : "bg-garnet-bg dark:bg-garnet/10 text-garnet"
          }`}
        >
          {JSON.stringify(result.body, null, 2)}
        </div>
      )}
    </div>
  )
}

function Field({ label, value, onChange, placeholder, optional, optLabel }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-muted dark:text-white/60 mb-1.5">
        {label} {optional && <span className="font-normal text-muted/60 dark:text-white/40">{optLabel}</span>}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full text-sm border border-line dark:border-white/15 rounded-lg px-3 py-2 bg-paper dark:bg-white/5 dark:text-white focus:outline-none focus:border-indigo dark:focus:border-amber"
      />
    </div>
  )
}
