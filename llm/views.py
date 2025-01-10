import json
import redis
import uuid
from openai import OpenAI
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import sync_to_async

# Redis 클라이언트 설정
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def truncate_prompt(prompt, max_length=1000):
    """Truncate the prompt to ensure it does not exceed max_length."""
    if len(prompt) > max_length:
        return prompt[:max_length - 3] + "..."
    return prompt

@csrf_exempt
def create_scenario(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # 사용자 입력 데이터 가져오기
            year = data.get("year")
            month = data.get("month")
            day = data.get("day")
            hour = data.get("hour")
            minute = data.get("minute")
            location = data.get("location")
            event_type = data.get("event_type")

            # 필수 필드 검증
            if not (year and month and day and hour and minute and location and event_type):
                return JsonResponse({"error": "Year, month, day, hour, minute, location, and event_type must be provided."}, status=502)

            if location not in ["미술관", "박물관"]:
                return JsonResponse({"error": "Location must be one of '미술관' or '박물관'."}, status=502)

            if event_type not in ["도난 사건", "살인 사건", "방화 사건"]:
                return JsonResponse({"error": "Event type must be one of '도난 사건', '살인 사건', or '방화 사건'."}, status=502)

            # 시나리오 입력 구성
            scenario_input = (f"{location}에서 발생한 {event_type}에 대한 해결되지 않은 시나리오를 생성해줘."
                              f"발생한 날짜는 {year}-{month}-{day} {hour}:{minute}이고,"
                              f"길지 않고 간결하게 100자 이내로 만들어줘.")
            scenario_input = truncate_prompt(scenario_input)

            evidence_count = int(data.get("evidence_count", 2))
            suspect_count = int(data.get("suspect_count", 3))

            # 1-1. GPT-4 시나리오 생성
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": scenario_input}]
            )
            scenario_description = response.choices[0].message.content

            # 1-2. DALL-E 시나리오 이미지 생성
            image_prompt = f"{location}에서 일어난 {event_type} 그려줘."
            image_response = client.images.generate(
                prompt=truncate_prompt(image_prompt),
                n=1,
                size="1024x1024"
            )
            scenario_image_url = image_response.data[0].url
            print(f"DALL-E Image Prompt: {image_prompt}")

            # Redis에 시나리오 저장
            scenario_id = str(uuid.uuid4())
            redis_client.set(f"scenario:{scenario_id}:description", scenario_description)
            redis_client.set(f"scenario:{scenario_id}:image", scenario_image_url)

            # 2. 증거 생성
            evidence_list = []
            for i in range(evidence_count):
                evidence_prompt = (f"다음 시나리오를 참고하여 단 하나의 증거 {i + 1}를 만들어줘: {scenario_description}."
                                   f"설명은 간결하게 두 문장 내로 작성해줘.")
                evidence_prompt = truncate_prompt(evidence_prompt)
                evidence_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": evidence_prompt}]
                )
                evidence_description = evidence_response.choices[0].message.content

                evidence_image_prompt = f"{location}에서 발견된 {event_type} 관련 증거{i + 1}를 {evidence_description}를 참고하여 그려줘."
                evidence_image_response = client.images.generate(
                    prompt=truncate_prompt(evidence_image_prompt),
                    n=1,
                    size="1024x1024"
                )
                evidence_image_url = evidence_image_response.data[0].url
                print(f"DALL-E Evidence Image Prompt: {evidence_image_prompt}")

                evidence = {
                    "description": evidence_description,
                    "image_url": evidence_image_url
                }
                evidence_list.append(evidence)
                redis_client.set(f"scenario:{scenario_id}:evidence:{i}", json.dumps(evidence))

            # 3. 용의자 생성
            suspect_list = []
            for i in range(suspect_count):
                suspect_prompt = (f"다음 시나리오를 참고하여 용의자 {i + 1}를 만들어줘: {scenario_description}."
                                  f"이름, 성별, 나이, 직업, 설명을 포함하고 설명은 간결하게 두 문장 내로 작성해줘."
                                  f"한국인이고, 이름은 3글자야.")
                suspect_prompt = truncate_prompt(suspect_prompt)
                suspect_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": suspect_prompt}]
                )
                suspect_description = suspect_response.choices[0].message.content

                suspect_ini_chat_prompt = f"다음 시나리오를 참고하여 용의자 {i + 1}의 초기 진술을 한 문장으로 작성해줘: {scenario_description}"
                suspect_ini_chat_prompt = truncate_prompt(suspect_ini_chat_prompt)
                suspect_ini_chat_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": suspect_ini_chat_prompt}]
                )
                suspect_ini_chat = suspect_ini_chat_response.choices[0].message.content

                suspect_image_prompt = f"{location}에서 발생한 {event_type}에 연루된 용의자{i + 1}를 {scenario_description}를 참고하여 그려줘."
                suspect_image_response = client.images.generate(
                    prompt=truncate_prompt(suspect_image_prompt),
                    n=1,
                    size="1024x1024"
                )
                suspect_image_url = suspect_image_response.data[0].url

                suspect = {
                    "description": suspect_description,
                    "image_url": suspect_image_url,
                    "ini_chat": suspect_ini_chat
                }
                suspect_list.append(suspect)
                redis_client.set(f"scenario:{scenario_id}:suspect:{i}", json.dumps(suspect))

            # 4. 범인 설정
            criminal_index = 0  # 무작위 선택 가능
            redis_client.set(f"시나리오:{scenario_id}:범인", criminal_index)

            return JsonResponse({
                "scenario_id": scenario_id,
                "scenario_description": scenario_description,
                "scenario_image": scenario_image_url,
                "evidence": evidence_list,
                "suspects": suspect_list
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=502)
