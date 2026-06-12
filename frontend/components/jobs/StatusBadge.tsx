import { JobStatus } from "@/lib/types"

const styles: Record<JobStatus, string> = {
  pending:    "bg-amber-50 text-amber-800",
  processing: "bg-blue-50 text-blue-800",
  completed:  "bg-emerald-50 text-emerald-800",
  failed:     "bg-red-50 text-red-800",
  cancelled:  "bg-neutral-100 text-neutral-600",
}

export default function StatusBadge({ status }: { status: JobStatus }) {
  return (
    <span className={`inline-flex items-center text-[11px] font-medium px-2 py-0.5 rounded-full ${styles[status]}`}>
      {status}
    </span>
  )
}