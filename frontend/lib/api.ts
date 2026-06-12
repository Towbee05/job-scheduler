import axios from "./axios"
import {
  Job,
  DLQEntry,
  StatsResponse,
  CreateJobPayload,
} from "./types"

interface ApiResponse<T> {
  status: string
  data: T
  message?: string
  error?: string
}

interface Paginated<T> {
  status: string
  total_pages: number
  current_page: number
  limit: number
  data: T[]
}

export const api = {
  // stats
  getStats: async () => {
    const res = await axios.get<ApiResponse<StatsResponse>>("/api/v1/stats")
    return res.data
  },

  // jobs
  getJobs: async (status?: string, page = 1, limit = 15) => {
    const params: Record<string, unknown> = { page, limit }
    if (status) params.status = status
    const res = await axios.get<Paginated<Job>>("/api/v1/jobs", { params })
    return res.data
  },

  getJob: async (id: string) => {
    const res = await axios.get<ApiResponse<Job>>(`/api/v1/jobs/${id}`)
    return res.data
  },

  createJob: async (payload: CreateJobPayload) => {
    const res = await axios.post<ApiResponse<Job>>("/api/v1/jobs", payload)
    return res.data
  },

  cancelJob: async (id: string) => {
    const res = await axios.patch<ApiResponse<Job>>(`/api/v1/jobs/${id}/cancel`)
    return res.data
  },

  // dlq
  getDLQ: async (page = 1, limit = 15) => {
    const res = await axios.get<Paginated<DLQEntry>>("/api/v1/dlq", {
      params: { page, limit },
    })
    return res.data
  },

  retryDLQ: async (id: string) => {
    const res = await axios.put<ApiResponse<Job>>(`/api/v1/dlq/${id}/retry`)
    return res.data
  },
}