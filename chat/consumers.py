import json
import logging
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from django_redis import get_redis_connection
from openai import OpenAI

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
        logger.info("WebSocket connection request received.")
        """
        WebSocket 연결 시 호출.
        - `suspect_id`를 URL에서 추출합니다.
        - Redis 캐시를 초기화하고 초기 메시지를 클라이언트로 전송합니다.
        """

        # URL에서 suspect_id 추출
        self.suspect_id = self.scope['url_route']['kwargs']['suspect_id']
        self.room_group_name = f'chat_{self.suspect_id}'
        logger.info(f"Connecting to WebSocket with suspect_id: {self.suspect_id}")

        # Redis 캐시 초기화 (기존 대화 기록 삭제)
        cache_key = f'gptchat_suspect_{self.suspect_id}'
        redis_conn.delete(cache_key)

        # 용의자 정보 로드
        self.suspect = self.get_suspect_info(self.suspect_id)
        if not self.suspect:
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

        # 초기 메시지 클라이언트로 전송
        await self.send(json.dumps({
            "message": f"용의자 {self.suspect['name']}의 심문을 시작합니다.\n초기 진술: {initial_statement}",
            "suspect": self.suspect
        }))



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
            logger.info(f'WebSocket disconnected for suspect ID {self.suspect_id}')
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {str(e)}")



    async def receive(self, text_data):
        """
        클라이언트 메시지 수신 시 호출.
        - 사용자 메시지를 Redis와 데이터베이스에 저장하고, GPT 응답을 생성하여 전송합니다.
        """
        try:
            # JSON 형식으로 메시지 파싱
            data = json.loads(text_data)
            user_message = data.get('message', '')

            # Redis에서 대화 히스토리 로드
            cache_key = f'gptchat_suspect_{self.suspect_id}'
            chat_history = redis_conn.lrange(cache_key, 0, -1) or []
            messages_history = [json.loads(msg) for msg in chat_history]
            messages_history.append({"role": "user", "content": user_message})  # 사용자 메시지 추가

            # GPT 응답 생성
            prompt = self.create_prompt(self.suspect, messages_history, user_message)
            gpt_response = await self.get_gpt_response(prompt)

            # 대화 기록 저장 (캐시 형태로 저장 후 DB에 저장하는 방식도 고려)
            await self.save_chat_message(user_message, gpt_response)

            # 클라이언트로 GPT 응답 전송
            await self.send(json.dumps({
                "message": gpt_response
            }))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send(json.dumps({'error': 'Internal server error'}))



    def get_suspect_info(self, suspect_id):
        """
        데이터베이스에서 용의자 정보를 조회합니다.
        """
        from django.apps import apps  # Lazy Import 사용
        try:
            Suspect = apps.get_model('suspect', 'Suspect')  # 문자열 참조로 Suspect 모델 가져오기
            suspect = Suspect.objects.get(pk=suspect_id)
            return {
                "name": suspect.name,
                "gender": "남성" if suspect.gender == 0 else "여성",
                "age": suspect.age,
                "job": suspect.job,
                "description": suspect.description,
                "is_thief": "범인" if suspect.is_thief else "무고한 시민",
                "image": suspect.image.url if suspect.image else None,
                "init_chat": suspect.init_chat  # 초기 진술 추가
            }
        except Suspect.DoesNotExist:
            logger.error(f"Suspect with ID {suspect_id} does not exist.")
            return None



    def get_scenario_info(self, scenario_id):
        """
        데이터베이스에서 시나리오 정보를 조회합니다.
        """
        from django.apps import apps  # Lazy Import 사용
        try:
            Scenario = apps.get_model('scenario', 'Scenario')  # 문자열 참조로 Scenario 모델 가져오기
            scenario = Scenario.objects.get(pk=scenario_id)
            return {
                "name": scenario.name,
                "description": scenario.description,
                "location": scenario.location,
                "datetime": scenario.datetime,
            }
        except Scenario.DoesNotExist:
            logger.error(f"Scenario with ID {scenario_id} does not exist.")
            return None



    async def save_chat_message(self, user_message, gpt_response):
        """
        사용자 메시지와 GPT 응답을 데이터베이스에 저장합니다.
        """
        from django.apps import apps  # Lazy Import 사용
        try:
            Chat = apps.get_model('chat', 'Chat')  # 문자열 참조로 Chat 모델 가져오기
            Chat.objects.create(
                suspect_id=self.suspect_id,
                user_chat=user_message,
                suspect_chat=gpt_response
            )
        except Exception as e:
            logger.error(f"Error saving chat message: {str(e)}")



    # 프롬프트는 좀더 고민해보고 진행 예정
    def create_prompt(self, suspect, scenario, history, user_message):
        """
        LLM이 생성한 데이터를 기반으로 GPT 프롬프트를 생성합니다.
        - 프롬프트를 한국어로 작성하여 LLM이 한국어로 응답하도록 유도.
        """
        # 증거 정리
        evidence_list = "\n- ".join(suspect.get("evidence", []))

        # 용의자가 범인인지 여부에 따라 목표 설정
        goal = "당신의 무죄를 설득력 있게 주장하고, 범죄와 관련된 혐의를 피하십시오." \
            if not suspect["is_thief"] else \
            "혐의를 완전히 인정하지 않으면서 의심을 다른 곳으로 돌리십시오."

        # 프롬프트 템플릿 생성
        prompt = f"""
    당신은 {suspect['name']}입니다. 나이는 {suspect['age']}세이고, 성별은 {suspect['gender']}입니다.
    직업은 {suspect['job']}이며, 성격은 다음과 같습니다: "{suspect['description']}".
    현재 {scenario['location']}에서 {scenario['datetime']}에 발생한 사건에 대해 심문을 받고 있습니다.

    다음은 당신에게 제시된 증거입니다:
    - {evidence_list}

    심문관이 방금 당신에게 다음과 같이 물었습니다: "{user_message}"
    당신의 목표는 {goal}

    모든 응답은 한국어로 작성하세요.
    직접적으로 범인이냐고 묻는 질문에는 무조건적으로 혐의를 부인하세요.
    """
        return prompt



    async def get_gpt_response(self, prompt):
        """
        OpenAI GPT API를 호출하여 응답을 생성합니다.
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating GPT response: {str(e)}")
            return "죄송합니다. 응답을 생성하는 데 문제가 발생했습니다."
