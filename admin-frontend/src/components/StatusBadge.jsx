const STYLES = {
  indexed: "bg-mint-bg text-mint dark:bg-mint/15 dark:text-mint",
  processing: "bg-amber/10 text-amber-hover dark:bg-amber/15 dark:text-amber",
  failed: "bg-garnet-bg text-garnet dark:bg-garnet/15 dark:text-garnet",
  not_found: "bg-line text-muted dark:bg-white/10 dark:text-white/50",
}

export default function StatusBadge({ status }) {
  const style = STYLES[status] || STYLES.not_found
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold font-mono ${style}`}>
      {status || "unknown"}
    </span>
  )
}
