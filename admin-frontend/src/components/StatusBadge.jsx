const STYLES = {
  indexed: "bg-mint-bg text-mint",
  processing: "bg-amber/10 text-amber-hover",
  failed: "bg-garnet-bg text-garnet",
  not_found: "bg-line text-muted",
}

export default function StatusBadge({ status }) {
  const style = STYLES[status] || STYLES.not_found
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold font-mono ${style}`}>
      {status || "unknown"}
    </span>
  )
}
