export type JobStatus = "pending" | "processing" | "completed" | "failed" | "cancelled"

export type JobPriority = 1 | 2 | 3

export type JobInterval = "every_1_minute" | "every_5_minutes" | "every_1_hour" | null

export interface Job {
  id: string
  type: string
  priority: JobPriority
  mutated_priority: number
  payload: Record<string, unknown>
  status: JobStatus
  retry_count: number
  scheduled_at: string
  processed_at: string | null
  interval: JobInterval
  created_at: string
  updated_at: string
  dependencies: string[]
}

export interface DLQEntry {
  id: string
  job: Job
  error: string
  failed_at: string
  resolved: boolean
}

export interface StatsResponse {
  total: number
  pending: number
  processing: number
  completed: number
  failed: number
  cancelled: number
  dlq: number
}

export interface ApiResponse<T> {
  status: "success" | "error"
  data: T | null
  message?: string
  error?: string
}

export interface CreateJobPayload {
  type: string
  priority: JobPriority
  payload: Record<string, unknown>
  scheduled_at: string
  interval: JobInterval
  dependencies: string[]
}

export interface WebSocketEvent {
  event: "job.updated" | "job.created" | "job.cancelled"
  job_id: string
  status: JobStatus
  retry_count: number
}