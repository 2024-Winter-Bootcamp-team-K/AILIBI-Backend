# your_app_name/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # WebSocket 연결 시 실행
        await self.accept()

    async def disconnect(self, close_code):
        # WebSocket 연결 종료 시 실행
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_input = data.get("message", "No message received!")
        # Echo the message back as a simple test
        await self.send(text_data=json.dumps({
            "message": f"Received: {user_input}"
        }))