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
        action = data.get("action", "chat")  # chat or image

        # OpenAI API Key 설정
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        try:
            if action == "chat":
                # OpenAI GPT 응답 생성
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": user_input}],
                    temperature=temperature,
                )
                gpt_response = response.choices[0].message.content

                # 클라이언트에 GPT 응답 전송
                await self.send(text_data=json.dumps({
                    "type": "chat",
                    "message": gpt_response
                }))

            elif action == "image":
                # DALL-E 이미지 생성
                image_prompt = data.get("prompt", user_input)  # 메시지를 이미지 프롬프트로 사용
                image_size = data.get("size", "1024x1024")  # 이미지 크기 (기본값 1024x1024)
                image_count = max(1, min(data.get("n", 1), 5))  # 생성 이미지 수 (1~5 제한)

                img_response = client.images.generate(
                    model="dall-e-3",
                    prompt=image_prompt,
                    n=image_count,
                    size=image_size
                )
                image_urls = img_response.data[0].url

                # 클라이언트에 이미지 URL 전송
                await self.send(text_data=json.dumps({
                    "type": "image",
                    "urls": image_urls
                }))

            else:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "Invalid action specified."
                }))

        except Exception as e:
            # 에러 응답 전송
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Error generating response: {str(e)}"
            }))
