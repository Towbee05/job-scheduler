from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import uuid

def broadcast_event(event_type: str, job_id: uuid.UUID, status: str, retry_count: int):
    async_to_sync(get_channel_layer().group_send)("live_job_updates", {
        "type":"broadcast_event",
        "event_type": event_type,
        "job_id": str(job_id),
        "status": status,
        "retry_count": retry_count
    })