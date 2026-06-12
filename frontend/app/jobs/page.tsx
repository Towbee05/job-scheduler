"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import Link from "next/link"
import JobsTable from "@/components/jobs/JobsTable"
import { api } from "@/lib/api"
import { Job, JobStatus, WebSocketEvent } from "@/lib/types"
import { useJobUpdates } from "@/hooks/useJobUpdates"

const LIMIT = 15

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [activeFilter, setActiveFilter] = useState<JobStatus | "all">("all")
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  const fetchJobs = useCallback(async (status: JobStatus | "all", page: number) => {
    setLoading(true)
    try {
      const res = await api.getJobs(
        status === "all" ? undefined : status,
        page,
        LIMIT
      )
      setJobs(res.data ?? [])
      setTotalPages(res.total_pages ?? 1)
    } catch (e) {
      setJobs([])
    } finally {
      setLoading(false)
    }
  }, [])

  // background poll — keeps list in sync without triggering loading skeleton
  const pollJobs = useCallback(async (status: JobStatus | "all", page: number) => {
    try {
      const res = await api.getJobs(
        status === "all" ? undefined : status,
        page,
        LIMIT
      )
      setJobs(res.data ?? [])
      setTotalPages(res.total_pages ?? 1)
    } catch {
      // silent
    }
  }, [])

  // refetch when filter or page changes
  useEffect(() => {
    fetchJobs(activeFilter, currentPage)
    const interval = setInterval(() => pollJobs(activeFilter, currentPage), 15000)
    return () => clearInterval(interval)
  }, [activeFilter, currentPage, fetchJobs, pollJobs])

  // reset to page 1 when filter changes
  const handleFilterChange = (filter: JobStatus | "all") => {
    setActiveFilter(filter)
    setCurrentPage(1)
  }

  // keep a ref so the ws handler can read the latest filter without reconnecting
  const filterRef = useRef(activeFilter)
  filterRef.current = activeFilter

  // websocket — update row in place, or remove if no longer matches filter
  const handleWsUpdate = useCallback((event: WebSocketEvent) => {
    setJobs((prev) => {
      const filter = filterRef.current
      if (filter !== "all" && event.status !== filter) {
        return prev.filter((job) => job.id !== event.job_id)
      }
      return prev.map((job) =>
        job.id === event.job_id
          ? { ...job, status: event.status, retry_count: event.retry_count }
          : job
      )
    })
  }, [])

  useJobUpdates(handleWsUpdate)

  const handleCancel = async (id: string) => {
    await api.cancelJob(id)
    setJobs((prev) =>
      prev.map((job) =>
        job.id === id ? { ...job, status: "cancelled" } : job
      )
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-medium text-neutral-900 mb-1">Jobs</h1>
          <p className="text-sm text-neutral-400">All scheduled and processed jobs</p>
        </div>
        <Link
          href="/create"
          className="bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors"
        >
          + New job
        </Link>
      </div>

      {/* Table */}
      {loading ? (
        <div className="border border-neutral-200 rounded-xl overflow-hidden bg-white">
          {Array.from({ length: LIMIT }).map((_, i) => (
            <div
              key={i}
              className="h-12 border-b border-neutral-100 animate-pulse bg-neutral-50"
            />
          ))}
        </div>
      ) : (
        <JobsTable
          jobs={jobs}
          activeFilter={activeFilter}
          onFilterChange={handleFilterChange}
          onCancel={handleCancel}
        />
      )}

      {/* Pagination */}
      {!loading && totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          {/* Page info */}
          <p className="text-xs text-neutral-400">
            Page {currentPage} of {totalPages}
          </p>

          {/* Controls */}
          <div className="flex items-center gap-1">
            {/* Prev */}
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 text-xs border border-neutral-200 rounded-lg text-neutral-600 hover:border-neutral-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              ← Prev
            </button>

            {/* Page numbers */}
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter((p) => {
                // always show first, last, current, and neighbours
                return (
                  p === 1 ||
                  p === totalPages ||
                  Math.abs(p - currentPage) <= 1
                )
              })
              .reduce<(number | "...")[]>((acc, p, i, arr) => {
                // insert ellipsis where pages are skipped
                if (i > 0 && p - (arr[i - 1] as number) > 1) {
                  acc.push("...")
                }
                acc.push(p)
                return acc
              }, [])
              .map((p, i) =>
                p === "..." ? (
                  <span
                    key={`ellipsis-${i}`}
                    className="px-2 py-1.5 text-xs text-neutral-400"
                  >
                    …
                  </span>
                ) : (
                  <button
                    key={p}
                    onClick={() => setCurrentPage(p as number)}
                    className={`
                      px-3 py-1.5 text-xs border rounded-lg transition-colors
                      ${currentPage === p
                        ? "bg-neutral-900 text-white border-neutral-900"
                        : "border-neutral-200 text-neutral-600 hover:border-neutral-400"
                      }
                    `}
                  >
                    {p}
                  </button>
                )
              )}

            {/* Next */}
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 text-xs border border-neutral-200 rounded-lg text-neutral-600 hover:border-neutral-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}