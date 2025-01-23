import json
import logging
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from django_redis import get_redis_connection
from openai import OpenAI
from asgiref.sync import sync_to_async
from django.apps import apps
from django.shortcuts import get_object_or_404
import os

# 로깅 설정
logger = logging.getLogger(__name__)

# Redis 연결
redis_conn = get_redis_connection("default")

# OpenAI API 초기화
client = OpenAI(api_key=settings.OPENAI_API_KEY)

class MyConsumer(AsyncWebsocketConsumer):
    """
    WebSocket을 기반으로 용의자와 심문 대화를 진행하는 Consumer 클래스.
    - `suspect_id`를 기준으로 각 대화를 관리합니다.
    - Redis를 통해 대화 히스토리를 캐싱하며, OpenAI GPT를 호출하여 응답을 생성합니다.
    - 사용자 질문 및 GPT 응답을 데이터베이스에 저장합니다.
    """

    async def connect(self):
        """
        WebSocket 연결 시 호출.
        - `suspect_id`를 URL에서 추출합니다.
        - Redis 캐시를 초기화하고 초기 메시지를 클라이언트로 전송합니다.
        """

        logger.info("WebSocket connection request received.")

        # URL에서 suspect_id 추출
        self.suspect_id = self.scope['url_route']['kwargs']['suspect_id']
        self.room_group_name = f'chat_{self.suspect_id}'
        logger.info(f"Connecting to WebSocket with suspect_id: {self.suspect_id}")

        # chat_id 가져오기
        
        self.chat_id = await self.get_chat_id()
        if not self.chat_id: # chat_id가 없을경우 새로 생성
            self.chat_id = await self.create_new_chat()
            logger.info(f"New chat created for suspect_id {self.suspect_id} with chat_id {self.chat_id}")

        # Redis 캐시 초기화 (기존 대화 기록 삭제)
        cache_key = f'gptchat_suspect_{self.suspect_id}'
        redis_conn.delete(cache_key)
        logger.debug(f"Redis cache cleared for key: {cache_key}")

        # 용의자 정보 로드
        self.suspect = await self.get_suspect_info(self.suspect_id)
        if not self.suspect:
            logger.warning(f"Suspect with ID {self.suspect_id} not found.")
            await self.send(json.dumps({
                "error": "용의자를 찾을 수 없습니다."
            }, ensure_ascii=False))
            await self.close()
            return

        # 초기 진술 불러오기
        initial_statement = self.suspect.get('init_chat', "현재 이 용의자는 초기 진술이 없습니다.")

        # 그룹에 사용자 추가 (다중 사용자 지원)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        logger.info(f"WebSocket connection established for suspect_id: {self.suspect_id}")

        # 초기 메시지 클라이언트로 전송
        await self.send(json.dumps({
            "message": f"{initial_statement}",
            "suspect": self.suspect
        }, ensure_ascii=False))



    async def disconnect(self, close_code):
        """
        WebSocket 연결 종료 시 호출.
        - 그룹에서 사용자를 제거합니다.
        """
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f'WebSocket disconnected for suspect_id: {self.suspect_id}, close_code: {close_code}')
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {str(e)}")



    async def receive(self, text_data):
        """
        클라이언트 메시지를 받아 GPT에 전달하고 응답을 반환하는 간단한 테스트 함수.
        """
        try:
            # JSON 형식으로 클라이언트 메시지 파싱
            data = json.loads(text_data)
            user_message = data.get('message', '').strip()

            if not user_message:
                logger.warning("Received empty message from client.")
                await self.send(json.dumps({
                    "error": "빈 메시지는 처리할 수 없습니다."
                }, ensure_ascii=False))
                return

            logger.info(f"Message received from client: {user_message}")

            # Redis에서 대화 히스토리 로드
            cache_key = f'gptchat_suspect_{self.suspect_id}'
            chat_history = redis_conn.lrange(cache_key, 0, -1) or []
            messages_history = [json.loads(msg) for msg in chat_history]

            # 히스토리가 없으면 초기 진술 추가
            if len(messages_history) == 0:
                initial_statement = self.suspect.get('init_chat', "현재 이 용의자는 초기 진술이 없습니다.")
                messages_history.append({"role": "system", "content": f"초기 진술: {initial_statement}"})

            # 사용자 메시지를 히스토리에 추가
            messages_history.append({"role": "user", "content": user_message})

            # GPT 호출을 위한 프롬프트 생성
            prompt = await self.create_prompt(self.suspect, messages_history, user_message)

            # GPT API 호출
            gpt_response = await self.get_gpt_response(prompt)

            # Redis에 대화 기록 저장
            redis_conn.rpush(cache_key, json.dumps({"role": "user", "content": user_message}))
            redis_conn.rpush(cache_key, json.dumps({"role": "assistant", "content": gpt_response}))
            logger.debug(f"Updated Redis cache for suspect_id: {self.suspect_id}")

            # 데이터베이스에 사용자 메시지와 GPT 응답 저장
            await self.save_chat_message(user_message, gpt_response)

            # 클라이언트로 GPT 응답 전송
            await self.send(json.dumps({
                "user_chat": user_message,
                "suspect_chat": gpt_response
            }, ensure_ascii=False))

            logger.info(f"GPT response sent: {gpt_response}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON received.")
            await self.send(json.dumps({
                "error": "잘못된 JSON 형식입니다."
            }, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send(json.dumps({
                "error": "내부 서버 오류가 발생했습니다."
            }, ensure_ascii=False))



    @sync_to_async
    def get_suspect_info(self, suspect_id):

        try:
            Suspect = apps.get_model('suspect', 'Suspect')
            suspect = Suspect.objects.get(pk=suspect_id)

            # Scenario 정보 가져오기 (Foreign Key로 연결된 경우)
            scenario = suspect.scenario  # Suspect에서 FK로 연결된 Scenario 객체

            logger.debug(f"Suspect info loaded: {suspect.name} ({suspect_id})")

            return {
                "name": suspect.name,
                "gender": "남성" if suspect.gender == 0 else "여성",
                "age": suspect.age,
                "job": suspect.job,
                "description": suspect.description,
                "is_theif": suspect.is_theif,
                "init_chat": suspect.init_chat,
                "scenario": {
                    "id": scenario.id,  # Scenario ID
                    "name": scenario.name,
                    "description": scenario.description,
                    "location": scenario.location,
                    "datetime": scenario.datetime,
                    "type": scenario.type
                } if scenario else None  # Scenario가 없을 경우 None 반환
            }
        except Suspect.DoesNotExist:
            logger.error(f"Suspect with ID {suspect_id} does not exist.")
            return None

    @sync_to_async
    def get_chat_id(self):
        """
        suspect_id를 기반으로 chat_id를 가져옵니다.
        """
        try:
            Chat = apps.get_model('chat', 'Chat')
            chat = Chat.objects.get(suspect_id=self.suspect_id)  # suspect_id와 연결된 레코드 조회
            return chat.id  # chat_id 반환
        except Chat.DoesNotExist:
            logger.error(f"No chat record found for suspect_id: {self.suspect_id}")
            return None

    @sync_to_async
    def create_new_chat(self):
        """
        새로운 chat_id를 생성하고 chat_id를 반환합니다.
        """
        # 'chat' 앱의 Chat 모델 가져오기
        Chat = apps.get_model('chat', 'Chat')

        new_chat = Chat.objects.create(user_chat="", suspect_chat="", suspect_id=self.suspect_id)
        return new_chat.id

    @sync_to_async
    def create_prompt(self, suspect, history, user_message):
        """
        Redis 대화 히스토리와 사용자 입력을 기반으로 GPT 프롬프트를 생성합니다.
        """
        try:
            # Redis 대화 히스토리를 텍스트로 변환
            formatted_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])

            # 관련 증거 조회
            Evidence = apps.get_model('evidence', 'Evidence')
            scenario_id = suspect['scenario']['id']
            evidence_list = Evidence.objects.filter(scenario_id=scenario_id)

            # 증거를 텍스트로 변환
            formatted_evidence = "\n".join([f"- {evidence.name}: {evidence.description}" for evidence in evidence_list])

            # 용의자가 범인인지 여부에 따라 목표 설정
            goal = (
                f"You play the role of an innocent citizen among suspects. Convincingly argue your innocence and avoid being implicated in a crime."
                if not suspect["is_theif"] else
                f"You play the role of the culprit among the suspects. You need to divert the detective's suspicions without fully admitting your guilt. However, don't tell a complete lie. Don't identify yourself as the culprit. You can make contradictory statements, but they shouldn't be crucial to the investigation."
            )

            # 프롬프트 생성
            prompt = (
                f"We have created a fictional deduction game scenario and you need to create a suspect's answers to the detective's questions. Consider the following items as you answer the detective's questions.\n"
                f"0. All inputs are in Korean.\n"
                f"1. the fictional scenario is as follows\n"
                f"- The location of the incident: {suspect['scenario']['location']}\n"
                f"- Time of the incident : {suspect['scenario']['datetime']}\n"
                f"- Type of incident : {suspect['scenario']['type']}\n"
                f"- Detailed description of the incident : {suspect['scenario']['description']}\n\n"
                f"2. the suspect you need to create has the following characteristics\n"
                f"- Name : {suspect['name']}\n"
                f"- Age : {suspect['age']}\n"
                f"- Gender : {suspect['gender']}\n"
                f"- Job : {suspect['job']}\n"
                f"- description : {suspect['description']}\n"
                f"- Suspect's situation at the time of the incident : \n\n"
                f"3. evidence found in the case, including \n"
                f"{formatted_evidence}\n"
                f"To keep in mind that no other evidence exists.\n"
                f"4. the transcript of the conversation so far is as follows.\n"
                f"{formatted_history}\n"
                f"5. {goal}\n"
                f"6. The detective's questions were given as follows: {user_message} \n"
                f"Give the appropriate answers \n"
                f"The role of user's message is : {user_message}, Don't repeat again. \n"
                f"7. All answers should be printed in Korean. \n"
                f"8. Answer in the first person. \n"
                f"9. Output only one answer. \n"
                f"10. Do not include role that user && assistant on your message. \n"
            )

            logger.debug(f"Prompt created: {prompt}")
            return prompt.strip()
        except Exception as e:
            logger.error(f"Error creating GPT prompt: {str(e)}", exc_info=True)
            return "죄송합니다. 프롬프트 생성 중 오류가 발생했습니다."



    async def get_gpt_response(self, user_message):
        """
        OpenAI GPT API를 호출하여 응답을 생성합니다.
        """
        try:
            # OpenAI API 호출 (단순 메시지 전달)
            response = await sync_to_async(client.chat.completions.create)(
                model="gpt-4",
                messages=[{"role": "user", "content": user_message}]
            )
            # 응답에서 메시지 추출 (객체의 속성 접근)
            if response.choices and len(response.choices) > 0:
                logger.debug(f"GPT response retrieved successfully.")
                return response.choices[0].message.content  # 메시지 내용 반환
            else:
                logger.error("Invalid GPT response format.")
                return "죄송합니다. GPT 응답 형식에 문제가 발생했습니다."
        except Exception as e:
            logger.error(f"Error generating GPT response: {str(e)}", exc_info=True)
            return "죄송합니다. 응답을 생성하는 데 문제가 발생했습니다."

    @sync_to_async
    def save_chat_message(self, user_message, gpt_response):
        """
        사용자 메시지와 GPT 응답을 chat_id 레코드에 누적하여 저장합니다.
        """
        try:
            # 'chat' 앱의 Chat 모델 가져오기
            Chat = apps.get_model('chat', 'Chat')

            chat = get_object_or_404(Chat, suspect_id=self.suspect_id)

            # 기존의 user_chat, suspect_chat 불러오기
            user_chat = chat.user_chat
            suspect_chat = chat.suspect_chat

            # 새로운 대화 기록을 데이터베이스에 저장
            chat.user_chat = f"{user_chat}/CHANGE {user_message}"
            chat.suspect_chat = f"{suspect_chat}/CHANGE {gpt_response}"
            chat.save()

            logger.info(f"Chat message updated for chat_id {self.chat_id}: User: {user_message}, GPT: {gpt_response}")
        except Exception as e:
            logger.error(f"Error updating chat message: {str(e)}", exc_info=True)

