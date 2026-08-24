const STAGE_KEYS = ["Upload", "Validate", "Clean", "Chunk", "Embed", "Store"]

export default function PipelineTrail({ stage }) {
  return (
    <div className="flex items-center gap-0 py-2">
      {STAGE_KEYS.map((label, i) => {
        const isDone = stage >= 6 || i < stage
        const isActive = stage === i
        const isFailed = stage === -2 && i === 0

        return (
          <div key={label} className="flex flex-1 flex-col items-center relative">
            {i < STAGE_KEYS.length - 1 && (
              <div className={`absolute top-[7px] start-1/2 w-full h-[2px] ${isDone ? "bg-mint" : "bg-line dark:bg-white/15"}`} />
            )}
            <div
              className={`w-3.5 h-3.5 rounded-full border-2 z-10 transition-colors duration-300 ${
                isFailed
                  ? "bg-garnet border-garnet"
                  : isDone
                  ? "bg-mint border-mint"
                  : isActive
                  ? "bg-amber border-amber animate-pulse"
                  : "bg-paper dark:bg-transparent border-line dark:border-white/20"
              }`}
            />
            <span className="mt-1.5 text-[10px] font-medium text-muted dark:text-white/50 text-center leading-tight">
              {label}
            </span>
          </div>
        )
      })}
    </div>
  )
}
