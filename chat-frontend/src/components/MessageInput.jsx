import { useState } from "react"
import { SendHorizontal } from "lucide-react"

export default function MessageInput({ onSend, disabled }) {
  const [value, setValue] = useState("")

  function submit(e) {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue("")
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      submit(e)
    }
  }

  return (
    <form onSubmit={submit} className="flex items-end gap-2 p-4 border-t border-line bg-white rounded-b-2xl">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question about your platform's documentation..."
        rows={1}
        disabled={disabled}
        className="flex-1 resize-none rounded-xl border border-line px-3.5 py-2.5 text-sm
          focus:outline-none focus:ring-2 focus:ring-indigo/30 focus:border-indigo
          disabled:opacity-60 disabled:cursor-not-allowed max-h-32"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="shrink-0 w-10 h-10 rounded-xl bg-indigo text-white flex items-center
          justify-center hover:bg-indigo-deep transition-colors disabled:opacity-40
          disabled:cursor-not-allowed"
      >
        <SendHorizontal size={17} />
      </button>
    </form>
  )
}
