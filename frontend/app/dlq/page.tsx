"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { DLQEntry } from "@/lib/types"

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

export default function DLQPage() {
  const [entries, setEntries] = useState<DLQEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [retrying, setRetrying] = useState<string | null>(null)

  useEffect(() => {
    api.getDLQ()
      .then((res) => setEntries(res.data))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false))
  }, [])

  const handleRetry = async (entry: DLQEntry) => {
    setRetrying(entry.id)
    try {
      const res = await api.retryDLQ(entry.id)
      if (res.status === "success") {
        // remove from DLQ view — it's been re-queued
        setEntries((prev) => prev.filter((e) => e.id !== entry.id))
      }
    } catch {
      // keep it in the list if retry fails
    } finally {
      setRetrying(null)
    }
  }

  const unresolved = entries.filter((e) => !e.resolved)

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-medium text-neutral-900 mb-1">
            Dead-letter queue
          </h1>
          <p className="text-sm text-neutral-400">
            Jobs that exhausted all retry attempts
          </p>
        </div>

        {/* Threshold warning */}
        {unresolved.length >= 10 && (
          <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg px-4 py-2.5">
            <span className="text-red-500 text-base">⚠</span>
            <p className="text-sm text-red-700 font-medium">
              Alert threshold reached — {unresolved.length} unresolved jobs
            </p>
          </div>
        )}
      </div>

      {/* Summary strip */}
      <div className="flex items-center gap-6 bg-neutral-50 border border-neutral-200 rounded-xl px-5 py-3 mb-6">
        <div>
          <p className="text-[11px] uppercase tracking-widest text-neutral-400">
            Unresolved
          </p>
          <p className="text-2xl font-medium text-red-600 leading-none mt-1">
            {unresolved.length}
          </p>
        </div>
        <div className="w-px h-8 bg-neutral-200" />
        <div>
          <p className="text-[11px] uppercase tracking-widest text-neutral-400">
            Total
          </p>
          <p className="text-2xl font-medium text-neutral-700 leading-none mt-1">
            {entries.length}
          </p>
        </div>
        <div className="w-px h-8 bg-neutral-200" />
        <div>
          <p className="text-[11px] uppercase tracking-widest text-neutral-400">
            Alert threshold
          </p>
          <p className="text-2xl font-medium text-neutral-700 leading-none mt-1">
            10
          </p>
        </div>
      </div>

      {/* DLQ list */}
      {loading ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-24 rounded-xl border border-neutral-200 animate-pulse bg-neutral-50"
            />
          ))}
        </div>
      ) : entries.length === 0 ? (
        <div className="border border-neutral-200 rounded-xl bg-white py-16 text-center">
          <p className="text-sm text-neutral-400">No failed jobs</p>
          <p className="text-xs text-neutral-300 mt-1">
            Jobs that exhaust all retries will appear here
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {entries.map((entry) => (
            <div
              key={entry.id}
              className="border border-neutral-200 rounded-xl bg-white px-5 py-4 flex items-start justify-between gap-6"
            >
              {/* Left — job info */}
              <div className="flex-1 min-w-0">
                {/* Top row */}
                <div className="flex items-center gap-3 mb-2">
                  <span className="font-mono text-[11px] text-neutral-400">
                    {shortId(entry.job.id)}
                  </span>
                  <span className="text-[11px] text-neutral-400">·</span>
                  <span className="text-sm text-neutral-700 font-medium">
                    {entry.job.type}
                  </span>
                  <span className="text-[11px] text-neutral-400">·</span>
                  <span className="text-[11px] text-neutral-400">
                    {entry.job.retry_count} attempts
                  </span>
                </div>

                {/* Error message */}
                <div className="bg-red-50 border border-red-100 rounded-lg px-3 py-2 mb-2">
                  <p className="text-xs font-mono text-red-700 truncate">
                    {entry.error}
                  </p>
                </div>

                {/* Payload preview */}
                <div className="bg-neutral-50 border border-neutral-100 rounded-lg px-3 py-2 mb-2">
                  <p className="text-[11px] font-mono text-neutral-400 truncate">
                    {JSON.stringify(entry.job.payload)}
                  </p>
                </div>

                {/* Meta */}
                <p className="text-[11px] text-neutral-400">
                  Failed {formatDate(entry.failed_at)}
                  {entry.resolved && (
                    <span className="ml-2 text-emerald-600 font-medium">
                      · resolved
                    </span>
                  )}
                </p>
              </div>

              {/* Right — retry button */}
              {!entry.resolved && (
                <button
                  onClick={() => handleRetry(entry)}
                  disabled={retrying === entry.id}
                  className="
                    shrink-0 flex items-center gap-1.5 text-sm
                    border border-neutral-200 rounded-lg px-4 py-2
                    text-neutral-600 hover:border-emerald-500 hover:text-emerald-700
                    disabled:opacity-50 disabled:cursor-not-allowed
                    transition-colors
                  "
                >
                  {retrying === entry.id ? (
                    <>
                      <span className="animate-spin text-base">↻</span>
                      Retrying…
                    </>
                  ) : (
                    <>↻ Retry</>
                  )}
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}