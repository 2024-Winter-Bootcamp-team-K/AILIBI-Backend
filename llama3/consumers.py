# your_app_name/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # WebSocket 연결 시 실행
        await self.accept()
        await self.send(text_data=json.dumps({
            "message": "WebSocket 연결 성공!"
        }))

    async def disconnect(self, close_code):
        # WebSocket 연결 종료 시 실행
        pass

    async def receive(self, text_data):
        # 클라이언트로부터 메시지를 받을 때 실행
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({
            "response": f"메시지 수신: {data['message']}"
        }))
