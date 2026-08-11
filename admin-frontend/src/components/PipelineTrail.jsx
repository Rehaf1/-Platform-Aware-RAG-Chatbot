const STAGES = ["Upload", "Validate", "Clean", "Chunk", "Embed", "Store"]

/**
 * stage: -1 idle, 0..5 in progress at that index, 6 done, -2 failed at stage 0
 */
export default function PipelineTrail({ stage }) {
  return (
    <div className="flex items-center gap-0 py-2">
      {STAGES.map((label, i) => {
        const isDone = stage >= 6 || i < stage
        const isActive = stage === i
        const isFailed = stage === -2 && i === 0

        return (
          <div key={label} className="flex flex-1 flex-col items-center relative">
            {i < STAGES.length - 1 && (
              <div
                className={`absolute top-[7px] left-1/2 w-full h-[2px] ${
                  isDone ? "bg-mint" : "bg-line"
                }`}
              />
            )}
            <div
              className={`w-3.5 h-3.5 rounded-full border-2 z-10 transition-colors duration-300 ${
                isFailed
                  ? "bg-garnet border-garnet"
                  : isDone
                  ? "bg-mint border-mint"
                  : isActive
                  ? "bg-amber border-amber animate-pulse"
                  : "bg-paper border-line"
              }`}
            />
            <span className="mt-1.5 text-[10px] font-medium text-muted text-center leading-tight">
              {label}
            </span>
          </div>
        )
      })}
    </div>
  )
}
