import json
import logging
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from django_redis import get_redis_connection
from openai import OpenAI
from asgiref.sync import sync_to_async
from django.apps import apps
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
                f"""당신은 무고한 시민입니다. 당신의 무죄를 설득력 있게 주장하고, 범죄와 관련된 혐의를 피하십시오.
                심문관의 질문에 진실된 알리바이를 제공하세요. 단, 증명하기 어려운 상황도 추가하세요."""
                if not suspect["is_theif"] else
                f"""당신은 범인입니다. 당신의 혐의를 완전히 인정하지 않으면서 의심을 다른 곳으로 돌리십시오.
                다만, 질문 3번에 1번 꼴로 완벽한 거짓말은 하지 말고, 심문관의 질문에 당신의 답변으로 당신이 범인임을 유추할 수 있는 사용자가 의심할 만한 논리적인 매우 작은 단서를 질문에 어울리게 포함하십시오. 혹은 앞서 했던 답변과 모순되는 내용을 포함한 대답을 하시오.
                질문에는 너무 주제에서 벗어나는 답변을 하지 마시오.
                """
            )

            # 프롬프트 생성
            prompt = f"""
            당신은 용의자 {suspect['name']}입니다. 나이는 {suspect['age']}세이고, 성별은 {suspect['gender']}입니다.
            직업은 {suspect['job']}이며, 성격은 다음과 같습니다: "{suspect['description']}".
            현재{suspect['scenario']['location']}에서 {suspect['scenario']['datetime']}에 발생한 {suspect['scenario']['type']}사건에 대해 심문을 받고 있습니다.
            사건에 대해서 설명하자면 {suspect['scenario']['description']} 이런 사건입니다.
            
            해당 사건에서 발견된 증거는 다음과 같습니다:
            {formatted_evidence}
            이 외의 사용자가 확인할 수 있는 증거는 없습니다.
            
            지금까지의 대화 기록은 다음과 같습니다:
            {formatted_history}

            심문관이 방금 당신에게 다음과 같이 물었습니다: "{user_message}"

            {goal}
            모든 답변은 영어 번역이 아닌 한국어로 작성하고, 직접적으로 자신이 범인이라고 해서는 안됩니다.
            대화 상대는 수사관 한명이며, 수사의 방향성을 제시해줄 필요는 없습니다.
            당신은 1인칭으로 바로 답변해주면 됩니다.
            답변에서 절대 증거에 관해서 먼저 이야기를 꺼내지 마세요.
            절대로 비속어를 사용해서는 안됩니다. 
            
            다음은 예상 질문에 따른 답변의 방향성 입니다.
            
            예시 1.
            질문: 사건 당일 오후 5시에 어디에 있었습니까?
            범인: 거짓 알리바이를 만드세요. 단, 시간이 명확하지 않거나 약간 의심할 수 있는 단서를 포함하세요.  
            무고한 시민: 진실된 알리바이를 제공하세요. 단, 증명하기 어려운 상황도 추가하세요. 
            
            예시 2.
            질문: 사건 현장에서 당신의 지문이 발견되었는데 어떻게 설명하겠습니까?
            범인: 지문이 발견된 이유를 정당화하세요. 예를 들어, "전에 그곳에 간 적이 있다"고 말하세요. 
            무고한 시민: 지문이 그곳에 있을 리가 없다고 주장하며 억울함을 강조하세요. 
            
            예시 3.
            질문: cctv 영상에서 당신과 비슷한 사람이 찍혔습니다. 이에 대해 어떻게 설명하시겠습니까?
            범인: CCTV 영상을 부정하거나 다른 사람으로 오해되었을 가능성을 제시하세요.   
            무고한 시민: CCTV가 잘못되었거나 자신이 찍혔을 리가 없다고 논리적으로 반박하세요. 
            
            """

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
        사용자 메시지와 GPT 응답을 데이터베이스에 저장합니다.
        """
        try:
            # 'chat' 앱의 Chat 모델 가져오기
            Chat = apps.get_model('chat', 'Chat')

            # 새로운 대화 기록을 데이터베이스에 저장
            Chat.objects.create(
                suspect_id=self.suspect_id,  # 현재 대화 중인 용의자 ID
                user_chat=user_message,  # 사용자 메시지
                suspect_chat=gpt_response  # GPT 응답
            )
            logger.info(f"Chat message saved: User: {user_message}, GPT: {gpt_response}")
        except Exception as e:
            logger.error(f"Error saving chat message: {str(e)}", exc_info=True)


