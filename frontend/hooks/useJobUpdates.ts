import { useEffect, useCallback } from "react"
import { WebSocketEvent, Job } from "@/lib/types"

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/live_job_updates/"

export function useJobUpdates(
  onUpdate: (event: WebSocketEvent) => void
) {
  const connect = useCallback(() => {
    const ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      console.info("[ws] connected")
    }

    ws.onmessage = (e) => {
      try {
        const event: WebSocketEvent = JSON.parse(e.data)
        onUpdate(event)
      } catch {
        console.error("[ws] failed to parse message", e.data)
      }
    }

    ws.onclose = () => {
      console.info("[ws] disconnected, reconnecting in 3s")
      setTimeout(connect, 3000)  // auto-reconnect
    }

    ws.onerror = (err) => {
      console.error("[ws] error", err)
      ws.close()
    }

    return ws
  }, [onUpdate])

  useEffect(() => {
    const ws = connect()
    return () => ws.close()  // cleanup on unmount
  }, [connect])
}