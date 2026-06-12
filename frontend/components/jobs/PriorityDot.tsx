import { JobPriority } from "@/lib/types"

const styles: Record<JobPriority, string> = {
  1: "bg-red-500",
  2: "bg-amber-400",
  3: "bg-emerald-500",
}

const labels: Record<JobPriority, string> = {
  1: "High",
  2: "Medium",
  3: "Low",
}

export default function PriorityDot({ priority }: { priority: JobPriority }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm text-neutral-600">
      <span className={`w-2 h-2 rounded-full ${styles[priority]}`} />
      {labels[priority]}
    </span>
  )
}