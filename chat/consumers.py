import json
from openai import OpenAI
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_input = data.get("message", "No message received!")
        temperature = max(0, min(data.get("temperature", 1.5), 2))  # 0~2로 제한

        # OpenAI API Key 설정
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        try:
            # OpenAI GPT 응답 생성
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": user_input}],
                temperature=temperature,
            )
            gpt_response = response.choices[0].message.content
        except Exception as e:
            gpt_response = f"Error generating response: {str(e)}"

        # 클라이언트에 응답 전송
        await self.send(text_data=json.dumps({
            "message": gpt_response
        }))