"use client"

import { Job, JobStatus, JobPriority } from "@/lib/types"
import StatusBadge from "./StatusBadge"
import PriorityDot from "./PriorityDot"

const FILTERS: { label: string; value: JobStatus | "all" }[] = [
  { label: "All", value: "all" },
  { label: "Pending", value: "pending" },
  { label: "Processing", value: "processing" },
  { label: "Completed", value: "completed" },
  { label: "Failed", value: "failed" },
  { label: "Cancelled", value: "cancelled" },
]

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function shortId(id: string) {
  return id.slice(0, 8) + "…"
}

interface JobsTableProps {
  jobs: Job[]
  activeFilter: JobStatus | "all"
  onFilterChange: (filter: JobStatus | "all") => void
  onCancel?: (id: string) => void
}

export default function JobsTable({
  jobs,
  activeFilter,
  onFilterChange,
  onCancel,
}: JobsTableProps) {
  return (
    <div>
      {/* Filter row */}
      <div className="flex items-center justify-between mb-3">
        <p className="text-[11px] uppercase tracking-widest text-neutral-400 font-medium">
          Jobs
        </p>
        <div className="flex gap-1">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => onFilterChange(f.value)}
              className={`
                text-xs px-3 py-1 rounded-md border transition-colors
                ${activeFilter === f.value
                  ? "bg-neutral-900 text-white border-neutral-900"
                  : "bg-white text-neutral-500 border-neutral-200 hover:border-neutral-400 hover:text-neutral-700"
                }
              `}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="border border-neutral-200 rounded-xl overflow-hidden bg-white">
        {jobs.length === 0 ? (
          <div className="py-16 text-center">
            <p className="text-sm text-neutral-400">No jobs found</p>
            <p className="text-xs text-neutral-300 mt-1">
              Jobs will appear here once created
            </p>
          </div>
        ) : (
          <table className="w-full text-sm" style={{ tableLayout: "fixed" }}>
            <thead>
              <tr className="bg-neutral-50 border-b border-neutral-200">
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[10%]">ID</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[13%]">Type</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[10%]">Priority</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[10%]">Effective priority</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[12%]">Status</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[7%]">Retries</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[15%]">Scheduled</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[11%]">Interval</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[14%]">Created</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[8%]"></th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job, i) => (
                <tr
                  key={job.id}
                  className={`
                    border-b border-neutral-100 hover:bg-neutral-50 transition-colors
                    ${i === jobs.length - 1 ? "border-b-0" : ""}
                  `}
                >
                  <td className="px-4 py-3 font-mono text-[11px] text-neutral-400">
                    {shortId(job.id)}
                  </td>
                  <td className="px-4 py-3 text-neutral-700 truncate">
                    {job.type}
                  </td>
                  <td className="px-4 py-3">
                    <PriorityDot priority={job.priority} />
                  </td>
                  <td className="px-4 py-3">
                    <PriorityDot priority={job.mutated_priority as JobPriority} />
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={job.status} />
                  </td>
                  <td className="px-4 py-3 text-neutral-500 text-center">
                    {job.retry_count}
                  </td>
                  <td className="px-4 py-3 font-mono text-[11px] text-neutral-400">
                    {formatDate(job.scheduled_at)}
                  </td>
                  <td className="px-4 py-3 text-[11px] text-neutral-400">
                    {job.interval ?? "—"}
                  </td>
                  <td className="px-4 py-3 font-mono text-[11px] text-neutral-400">
                    {formatDate(job.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    {(job.status === "pending" || job.status === "processing") && (
                      <button
                        onClick={() => onCancel?.(job.id)}
                        className="text-[11px] text-red-500 hover:text-red-700 transition-colors"
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}