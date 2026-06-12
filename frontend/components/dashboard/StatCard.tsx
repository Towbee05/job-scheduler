interface StatCardProps {
  label: string
  value: number
  sub: string
  variant?: "default" | "pending" | "processing" | "completed" | "failed" | "dlq"
}

const variantStyles: Record<string, string> = {
  default:     "text-neutral-900",
  pending:     "text-amber-700",
  processing:  "text-blue-700",
  completed:   "text-emerald-700",
  failed:      "text-red-700",
  dlq:         "text-orange-700",
}

export default function StatCard({ label, value, sub, variant = "default" }: StatCardProps) {
  return (
    <div className="bg-neutral-100 rounded-lg px-4 py-3">
      <p className="text-[11px] uppercase tracking-widest text-neutral-400 mb-1.5">
        {label}
      </p>
      <p className={`text-3xl font-medium leading-none ${variantStyles[variant]}`}>
        {value.toLocaleString()}
      </p>
      <p className="text-[11px] text-neutral-400 mt-1.5">{sub}</p>
    </div>
  )
}