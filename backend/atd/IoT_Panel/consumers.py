from channels.generic.websocket import AsyncWebsocketConsumer

BROADCAST_GROUP = "broadcast"

class EchoBroadcastConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(BROADCAST_GROUP, self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(BROADCAST_GROUP, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Forwards the payload EXACTLY as received to all clients.
        - If text frame: forwards the same text string
        - If binary frame: forwards the same bytes
        """
        if text_data is not None:
            # (Optional) quick sanity check for JSON without changing formatting:
            # If you want to ensure valid JSON but still keep original text:
            # import json; json.loads(text_data)  # will raise if invalid
            await self.channel_layer.group_send(
                BROADCAST_GROUP,
                {"type": "chat.text", "text": text_data},
            )
        elif bytes_data is not None:
            await self.channel_layer.group_send(
                BROADCAST_GROUP,
                {"type": "chat.bytes", "bytes": bytes_data},
            )

    async def chat_text(self, event):
        await self.send(text_data=event["text"])

    async def chat_bytes(self, event):
        await self.send(bytes_data=event["bytes"])



