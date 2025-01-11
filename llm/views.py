import json
import redis
import random
from openai import OpenAI
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from scenario.models import Scenario
from evidence.models import Evidence
from suspect.models import Suspect
from user.models import User
from random import randint, shuffle

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

            # user_id 가져오기
            user_id = data.get("user_id")
            if not user_id:
                return JsonResponse({"error": "user_id가 제공되지 않았습니다."}, status=400)

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

            # 시나리오 입력 구성
            scenario_input = (f"{location}에서 발생한 {event_type}에 대한 해결되지 않은 시나리오를 생성해줘. "
                              f"발생한 날짜는 {year}-{month}-{day} {hour}:{minute}이고, "
                              f"길지 않고 간결하게 100자 이내로 만들어줘.")
            scenario_input = truncate_prompt(scenario_input)

            # GPT-4 시나리오 생성
            gpt_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": scenario_input}]
            )
            if not gpt_response.choices or not gpt_response.choices[0].message.content:
                scenario_description = "시나리오 설명 오류 발생."
            else:
                scenario_description = gpt_response.choices[0].message.content

            # DALL-E 시나리오 이미지 생성
            image_prompt = f"{location}에서 발생한 {event_type}의 현장을 생생하게 그려줘."
            image_response = client.images.generate(
                model="dall-e-3",
                prompt=truncate_prompt(image_prompt),
                n=1,
                size="1024x1024"
            )
            scenario_image_url = image_response.data[0].url

            # Scenario 저장
            scenario = Scenario.objects.create(
                user_id=user_id,
                name=f"{event_type} 사건",
                location=location,
                type=event_type,
                datetime=f"{year}-{month}-{day} {hour}:{minute}",
                description=scenario_description,
                image=scenario_image_url,
                level=2
            )
            scenario_id = scenario.id  # AutoField에서 ID 가져오기

            # Evidence 생성
            evidence_list = []
            for i in range(int(data.get("evidence_count", 2))):
                evidence_prompt = (f"다음 시나리오를 참고하여 단 하나의 증거 {i + 1}를 만들어줘: {scenario_description}. "
                                   f"어떠한 증거인지, 증거의 이름을 포함하여 설명은 간결하게 두 문장 이내로 작성해줘."
                                   f"다음 양식으로 만들어줘."
                                   f"이름:"
                                   f"설명:"
                                   f"이미지 URL:")
                evidence_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": evidence_prompt}]
                )
                if not evidence_response.choices or not evidence_response.choices[0].message.content:
                    evidence_description = "증거 설명 오류 발생"
                else:
                    evidence_description = evidence_response.choices[0].message.content

                if ":" in evidence_description:
                    evidence_name = evidence_description.split(":")[1].strip()
                else:
                    evidence_name = "증거 이름 오류 발생"

                evidence_image_prompt = f"{location}에서 발견된 {event_type} 관련 증거 {i + 1}를 {evidence_description}를 참고하여 그려줘."
                evidence_image_response = client.images.generate(
                    model="dall-e-3",
                    prompt=truncate_prompt(evidence_image_prompt),
                    n=1,
                    size="1024x1024"
                )
                evidence_image_url = evidence_image_response.data[0].url

                evidence = Evidence.objects.create(
                    scenario=scenario,
                    name=evidence_name,
                    description=evidence_description,
                    image=evidence_image_url
                )
                evidence_list.append({
                    "id": evidence.id,
                    "name": evidence.name,
                    "description": evidence.description,
                    "image": evidence.image
                })

            # Suspect 생성
            suspect_list = []
            genders = [0, 0, 1]  # 0: 남성, 1: 여성
            shuffle(genders)  # 남성 2명, 여성 1명으로 섞음
            criminal_index = randint(0, 2)  # 랜덤으로 범인 지정

            for i in range(3):
                is_theif = (i == criminal_index)
                suspect_prompt = (f"다음 시나리오를 참고하여 용의자 {i + 1}를 만들어줘: {scenario_description}. "
                                  f"한국인 3글자 이름, 성별, 나이(20~40), 직업을 포함하고 설명은 간결하게 작성해줘."
                                  f"다음 양식으로 만들어줘."
                                  f"이름:"
                                  f"성별:"
                                  f"나이:"
                                  f"직업:"
                                  f"성격:"
                                  f"진범 유/무"
                                  f"이미지 URL")
                suspect_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": suspect_prompt}]
                )
                if not suspect_response.choices or not suspect_response.choices[0].message.content:
                    suspect_data = ["이름: 기본 이름", "성별: 남성", "나이: 30", "직업: 기본 직업", "성격: 기본 성격"]
                else:
                    suspect_data = suspect_response.choices[0].message.content.split("\n")

                try:
                    suspect_name = suspect_data[0].split(":")[1].strip()  # 이름 추출
                    suspect_job = suspect_data[3].split(":")[1].strip()  # 직업 추출
                    suspect_age = int(suspect_data[2].split(":")[1].strip())  # 나이 추출
                except (IndexError, ValueError) as e:
                    suspect_name = f"기본 이름 {i + 1}"
                    suspect_job = "기본 직업"
                    suspect_age = random.randint(20, 40)  # 기본 나이

                suspect_image_prompt = f"{location}에서 발생한 {event_type}에 연루된 용의자 {suspect_name}를 {suspect_job}으로 설정하고 그려줘."
                suspect_image_response = client.images.generate(
                    model="dall-e-3",
                    prompt=truncate_prompt(suspect_image_prompt),
                    n=1,
                    size="1024x1024"
                )
                suspect_image_url = suspect_image_response.data[0].url

                suspect = Suspect.objects.create(
                    scenario=scenario,
                    name=suspect_name,
                    gender=genders[i],
                    age=suspect_age,
                    job=suspect_job,
                    is_theif=is_theif,
                    image=suspect_image_url
                )
                suspect_list.append({
                    "id": suspect.id,
                    "name": suspect.name,
                    "gender": "남성" if genders[i] == 0 else "여성",
                    "age": suspect.age,
                    "job": suspect.job,
                    "is_theif": is_theif,
                    "image": suspect.image
                })

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
