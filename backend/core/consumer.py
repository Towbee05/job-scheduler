from channels.generic.websocket import AsyncWebsocketConsumer
import json

MISCONFIGURED_REDIS_ERR_CODE = 4000
event_type_set = {
    "job_created", "job_cancelled", "job_retried", "job_resolved", "job_completed", "job_failed", "job_failed_and_retried", "job_processing"
}

def send_dump_message(type: str, message: str) -> str:
    return json.dumps({
        "type": type,
        "message": message
    })

class JobConsumer(AsyncWebsocketConsumer):
    """ Websocket for job live updates """
    async def connect(self) -> None:
        """Run when websocket connects"""
        self.room_group_name = "live_job_updates"

        if self.channel_name is None:
            await self.close(code=MISCONFIGURED_REDIS_ERR_CODE)
            return

        # join room group 
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # accept connection
        await self.accept()

    async def disconnect(self, code: int) -> None:
        """Called when WebSocket disconnects"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data: str, bytes_data: bytes | None = None) -> None:
        """Called when message is sent to websocket"""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=send_dump_message("error", "could not dump provided json. malformed JSON"))
            return
        event_type = data.get("type")

        if event_type in event_type_set:
            pass
        else:
            await self.send(text_data=send_dump_message("error", f"unknown event type send via websocket: {event_type}"))

    async def broadcast_event(self, event):
        try:
            await self.send(text_data=json.dumps({
                "type": event["event_type"],
                "job_id": event["job_id"],
                "status": event["status"],
                "retry_count": event["retry_count"]
            }))
        except KeyError as e:
            await self.send(text_data=send_dump_message("error", f"Missing field in event: {e}"))
