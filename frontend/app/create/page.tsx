"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { JobPriority, JobInterval, CreateJobPayload } from "@/lib/types"

const JOB_TYPES = ["send_email", "log_processing", "generate_report"]

const PRIORITIES: { label: string; value: JobPriority; description: string }[] = [
  { label: "High", value: 1, description: "Runs first, ahead of all other jobs" },
  { label: "Medium", value: 2, description: "Default priority" },
  { label: "Low", value: 3, description: "Runs after high and medium jobs" },
]

const INTERVALS: { label: string; value: JobInterval }[] = [
  { label: "None (run once)", value: null },
  { label: "Every 1 minute", value: "every_1_minute" },
  { label: "Every 5 minutes", value: "every_5_minutes" },
  { label: "Every 1 hour", value: "every_1_hour" },
]

const DEFAULT_PAYLOADS: Record<string, string> = {
  send_email: JSON.stringify(
    { to: "user@example.com", subject: "Hello", body: "Message body" },
    null,
    2
  ),
}

export default function CreateJobPage() {
  const router = useRouter()

  const [type, setType] = useState("send_email")
  const [priority, setPriority] = useState<JobPriority>(2)
  const [payload, setPayload] = useState(DEFAULT_PAYLOADS["send_email"])
  const [payloadError, setPayloadError] = useState<string | null>(null)
  const [scheduledAt, setScheduledAt] = useState("")
  const [interval, setInterval] = useState<JobInterval>(null)
  const [dependencies, setDependencies] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleTypeChange = (newType: string) => {
    setType(newType)
    setPayload(DEFAULT_PAYLOADS[newType] ?? "{}")
  }

  const validatePayload = (value: string) => {
    try {
      JSON.parse(value)
      setPayloadError(null)
      return true
    } catch {
      setPayloadError("Invalid JSON")
      return false
    }
  }

  const handleSubmit = async () => {
    if (!validatePayload(payload)) return
    setSubmitting(true)
    setError(null)

    const depList = dependencies
      .split(",")
      .map((d) => d.trim())
      .filter(Boolean)

    const body: CreateJobPayload = {
      type,
      priority,
      payload: JSON.parse(payload),
      scheduled_at: scheduledAt
        ? new Date(scheduledAt).toISOString()
        : new Date().toISOString(),
      interval,
      dependencies: depList,
    }

    try {
      const res = await api.createJob(body)
      if (res.status === "success") {
        router.push("/jobs")
      } else {
        setError(res.error ?? res.message ?? "Failed to create job")
      }
    } catch {
      setError("Could not reach the server")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-xl font-medium text-neutral-900 mb-1">Create job</h1>
        <p className="text-sm text-neutral-400">
          Schedule a new background job for processing
        </p>
      </div>

      <div className="flex flex-col gap-6">

        {/* Job type */}
        <div>
          <label className="block text-xs font-medium text-neutral-500 uppercase tracking-widest mb-2">
            Job type
          </label>
          <select
            value={type}
            onChange={(e) => handleTypeChange(e.target.value)}
            className="w-full border border-neutral-200 rounded-lg px-3 py-2.5 text-sm text-neutral-900 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          >
            {JOB_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        {/* Priority */}
        <div>
          <label className="block text-xs font-medium text-neutral-500 uppercase tracking-widest mb-2">
            Priority
          </label>
          <div className="grid grid-cols-3 gap-2">
            {PRIORITIES.map((p) => (
              <button
                key={p.value}
                onClick={() => setPriority(p.value)}
                className={`
                  text-left px-4 py-3 rounded-lg border transition-colors
                  ${priority === p.value
                    ? "border-emerald-500 bg-emerald-50"
                    : "border-neutral-200 bg-white hover:border-neutral-300"
                  }
                `}
              >
                <p className={`text-sm font-medium ${priority === p.value ? "text-emerald-700" : "text-neutral-700"}`}>
                  {p.label}
                </p>
                <p className="text-xs text-neutral-400 mt-0.5">{p.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Payload */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-xs font-medium text-neutral-500 uppercase tracking-widest">
              Payload
            </label>
            {payloadError && (
              <span className="text-xs text-red-500">{payloadError}</span>
            )}
          </div>
          <textarea
            value={payload}
            onChange={(e) => {
              setPayload(e.target.value)
              validatePayload(e.target.value)
            }}
            rows={6}
            spellCheck={false}
            className={`
              w-full border rounded-lg px-3 py-2.5 text-sm font-mono bg-neutral-50
              focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent
              resize-none
              ${payloadError ? "border-red-300" : "border-neutral-200"}
            `}
          />
        </div>

        {/* Scheduled at */}
        <div>
          <label className="block text-xs font-medium text-neutral-500 uppercase tracking-widest mb-2">
            Scheduled at
            <span className="normal-case text-neutral-400 font-normal ml-1">
              — leave empty to run immediately
            </span>
          </label>
          <input
            type="datetime-local"
            value={scheduledAt}
            onChange={(e) => setScheduledAt(e.target.value)}
            className="w-full border border-neutral-200 rounded-lg px-3 py-2.5 text-sm text-neutral-900 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>

        {/* Interval */}
        <div>
          <label className="block text-xs font-medium text-neutral-500 uppercase tracking-widest mb-2">
            Recurring interval
          </label>
          <div className="grid grid-cols-2 gap-2">
            {INTERVALS.map((i) => (
              <button
                key={String(i.value)}
                onClick={() => setInterval(i.value)}
                className={`
                  text-left px-4 py-2.5 rounded-lg border text-sm transition-colors
                  ${interval === i.value
                    ? "border-emerald-500 bg-emerald-50 text-emerald-700"
                    : "border-neutral-200 bg-white text-neutral-600 hover:border-neutral-300"
                  }
                `}
              >
                {i.label}
              </button>
            ))}
          </div>
        </div>

        {/* Dependencies */}
        <div>
          <label className="block text-xs font-medium text-neutral-500 uppercase tracking-widest mb-2">
            Dependencies
            <span className="normal-case text-neutral-400 font-normal ml-1">
              — comma-separated job IDs
            </span>
          </label>
          <input
            type="text"
            value={dependencies}
            onChange={(e) => setDependencies(e.target.value)}
            placeholder="a3f19c2d-…, b7e21a4f-…"
            className="w-full border border-neutral-200 rounded-lg px-3 py-2.5 text-sm font-mono bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent placeholder:text-neutral-300"
          />
          <p className="text-xs text-neutral-400 mt-1.5">
            This job will not run until all listed jobs have completed
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={handleSubmit}
            disabled={submitting || !!payloadError}
            className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-neutral-200 disabled:text-neutral-400 text-white text-sm font-medium px-6 py-2.5 rounded-lg transition-colors"
          >
            {submitting ? "Creating…" : "Create job"}
          </button>
          <button
            onClick={() => router.back()}
            className="text-sm text-neutral-500 hover:text-neutral-700 transition-colors"
          >
            Cancel
          </button>
        </div>

      </div>
    </div>
  )
}