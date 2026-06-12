"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import StatCard from "@/components/dashboard/StatCard"
import StatusBadge from "@/components/jobs/StatusBadge"
import PriorityDot from "@/components/jobs/PriorityDot"
import { api } from "@/lib/api"
import { Job, StatsResponse } from "@/lib/types"

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

export default function DashboardPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [recentJobs, setRecentJobs] = useState<Job[]>([])
  const [statsLoading, setStatsLoading] = useState(true)
  const [jobsLoading, setJobsLoading] = useState(true)

  // fetch stats
  useEffect(() => {
    api.getStats()
      .then((res) => setStats(res.data))
      .catch(() => setStats(null))
      .finally(() => setStatsLoading(false))
  }, [])

  // fetch last 5 jobs
  useEffect(() => {
    api.getJobs(undefined, 1, 5)
      .then((res) => setRecentJobs(res.data))
      .catch(() => setRecentJobs([]))
      .finally(() => setJobsLoading(false))
  }, [])

  const dlqCount = stats?.dlq ?? 0

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-medium text-neutral-900 mb-1">Dashboard</h1>
        <p className="text-sm text-neutral-400">Live overview of all background jobs</p>
      </div>

      {/* DLQ alert strip */}
      {dlqCount > 0 && (
        <Link href="/dlq">
          <div className="flex items-center justify-between bg-red-50 border border-red-200 rounded-xl px-5 py-3 mb-6 hover:bg-red-100 transition-colors cursor-pointer">
            <div className="flex items-center gap-3">
              <span className="text-red-500 text-lg">⚠</span>
              <div>
                <p className="text-sm font-medium text-red-700">
                  {dlqCount} job{dlqCount > 1 ? "s" : ""} in the dead-letter queue
                </p>
                <p className="text-xs text-red-400 mt-0.5">
                  These jobs have exhausted all retry attempts and need attention
                </p>
              </div>
            </div>
            <span className="text-xs text-red-500 font-medium">
              View DLQ →
            </span>
          </div>
        </Link>
      )}

      {/* Stat cards */}
      {statsLoading ? (
        <div className="grid grid-cols-5 gap-3 mb-8">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-neutral-100 rounded-lg px-4 py-3 animate-pulse h-20" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-5 gap-3 mb-8">
          <StatCard label="Total"      value={stats?.total      ?? 0} sub="all time"       />
          <StatCard label="Pending"    value={stats?.pending    ?? 0} sub="in queue"       variant="pending"    />
          <StatCard label="Processing" value={stats?.processing ?? 0} sub="active workers" variant="processing" />
          <StatCard label="Completed"  value={stats?.completed  ?? 0} sub="successful"     variant="completed"  />
          <StatCard label="DLQ"        value={stats?.dlq        ?? 0} sub="need attention" variant="dlq"        />
        </div>
      )}

      {/* Recent jobs */}
      <div className="flex items-center justify-between mb-3">
        <p className="text-[11px] uppercase tracking-widest text-neutral-400 font-medium">
          Recent jobs
        </p>
        <Link
          href="/jobs"
          className="text-xs text-emerald-600 hover:text-emerald-700 font-medium transition-colors"
        >
          View all →
        </Link>
      </div>

      <div className="border border-neutral-200 rounded-xl overflow-hidden bg-white">
        {jobsLoading ? (
          <>
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="h-12 border-b border-neutral-100 animate-pulse bg-neutral-50"
              />
            ))}
          </>
        ) : recentJobs.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-sm text-neutral-400">No jobs yet</p>
            <Link
              href="/create"
              className="text-xs text-emerald-600 hover:text-emerald-700 mt-1 inline-block"
            >
              Create your first job →
            </Link>
          </div>
        ) : (
          <table className="w-full text-sm" style={{ tableLayout: "fixed" }}>
            <thead>
              <tr className="bg-neutral-50 border-b border-neutral-200">
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[12%]">ID</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[18%]">Type</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[14%]">Priority</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[14%]">Status</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[8%]">Retries</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[18%]">Scheduled</th>
                <th className="text-left px-4 py-2.5 text-[11px] font-medium text-neutral-400 w-[16%]">Created</th>
              </tr>
            </thead>
            <tbody>
              {recentJobs.map((job, i) => (
                <tr
                  key={job.id}
                  className={`
                    border-b border-neutral-100 hover:bg-neutral-50 transition-colors
                    ${i === recentJobs.length - 1 ? "border-b-0" : ""}
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
                    <StatusBadge status={job.status} />
                  </td>
                  <td className="px-4 py-3 text-neutral-500 text-center">
                    {job.retry_count}
                  </td>
                  <td className="px-4 py-3 font-mono text-[11px] text-neutral-400">
                    {formatDate(job.scheduled_at)}
                  </td>
                  <td className="px-4 py-3 font-mono text-[11px] text-neutral-400">
                    {formatDate(job.created_at)}
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