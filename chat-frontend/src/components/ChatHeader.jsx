import { RotateCcw } from "lucide-react"
import logo from "../assets/aptwatch-logo.png"

export default function ChatHeader({ onNewConversation }) {
  return (
    <div className="flex items-center justify-between px-5 py-4 border-b border-line bg-indigo-deep rounded-t-2xl">
      <div className="flex items-center gap-2.5">
        <img src={logo} alt="APTWatch" className="h-9 w-auto shrink-0" />
        <div>
          <h1 className="font-display font-semibold text-base leading-tight text-white">
            APTWatch Assistant
          </h1>
          <p className="text-xs text-white/60 leading-tight">Answers grounded in your documentation</p>
        </div>
      </div>

      <button
        onClick={onNewConversation}
        className="flex items-center gap-1.5 text-xs text-white/70 hover:text-white
          border border-white/20 hover:border-white/40 rounded-lg px-3 py-1.5 transition-colors"
      >
        <RotateCcw size={13} />
        New conversation
      </button>
    </div>
  )
}