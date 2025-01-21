import json
import boto3
import redis
import random
from openai import OpenAI
from django.http import JsonResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from scenario.models import Scenario
from evidence.models import Evidence
from suspect.models import Suspect
from random import shuffle
import requests
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from urllib.parse import quote

import logging

logger = logging.getLogger(__name__)


# Redis 클라이언트 설정
redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=6379, db=0)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# S3 클라이언트 생성
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)

def get_scenario_image(location, event_type):
    # S3 파일 이름 형식: "scenario/{location} {event_type}.png"
    s3_scenario_name = f"scenario/{location}{event_type}.png"
    s3_scenario_name_encoded = quote(s3_scenario_name)
    s3_scenario_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{s3_scenario_name_encoded}"
    return s3_scenario_url


def get_suspect_images():
    # 여성 이미지 파일 리스트
    female_files = [f"suspect/여성{i}.png" for i in range(1, 5)]
    # 남성 이미지 파일 리스트
    male_files = [f"suspect/남성{i}.png" for i in range(1, 9)]

    # 랜덤으로 여성 1명, 남성 2명 선택
    female_image = random.choice(female_files)
    male_images = random.sample(male_files, 2)  # 두 명의 남성 선택, 중복 방지

    # S3 URL 생성
    female_image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{quote(female_image)}"  # URL 인코딩
    male_image_urls = [
        f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{quote(male_image)}" for male_image in male_images  # URL 인코딩
    ]

    return female_image_url, male_image_urls

def upload_to_s3(file_name, file_data, content_type):
    """
    파일을 AWS S3에 업로드하고 URL 반환.
    """
    try:
        s3_key = f"evidence_images/{file_name}"
        logger.info(f"Uploading file to S3: Bucket={settings.AWS_STORAGE_BUCKET_NAME}, Key={s3_key}")

        s3_client.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=s3_key,
            Body=file_data,
            ContentType=content_type,
        )
        s3_evidence_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{quote(s3_key)}"
        return s3_evidence_url
    except Exception as e:
        logger.error(f"Failed to upload to S3: {e}")
        return None

def truncate_prompt(prompt, max_length=1000):
    """Truncate the prompt to ensure it does not exceed max_length."""
    if len(prompt) > max_length:
        return prompt[:max_length - 3] + "..."
    return prompt


class ScenarioAPIView(APIView):
    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    @swagger_auto_schema(
        operation_id="시나리오 생성하기",
        operation_description="시나리오 생성하기",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'year': openapi.Schema(type=openapi.TYPE_STRING, description="연도"),
                'month': openapi.Schema(type=openapi.TYPE_STRING, description="월"),
                'day': openapi.Schema(type=openapi.TYPE_STRING, description="일"),
                'hour': openapi.Schema(type=openapi.TYPE_STRING, description="시"),
                'minute': openapi.Schema(type=openapi.TYPE_STRING, description="분"),
                'location': openapi.Schema(type=openapi.TYPE_STRING, description="사건 장소"),
                'event_type': openapi.Schema(type=openapi.TYPE_STRING, description="사건 종류"),
            },
            required=['year', 'month', 'day', 'hour', 'minute', 'location', 'event_type'],  # 필수 값 설정
        ),
        responses={
            201: openapi.Response('시나리오 생성 성공', schema=openapi.Schema(type=openapi.TYPE_OBJECT)),
            400: openapi.Response(description="user_id 오류"),
            500: openapi.Response(description="예상치 못한 예외 발생"),
            502: openapi.Response(description="입력 값이 잘 못 되었거나 HTTP method가 잘 못되었습니다.")
        }
    )
    def post(self, request):
        #디버그 옵션
        debug = False

        if request.method == "POST":
            try:
                data = json.loads(request.body)

                if debug:
                    print("start\n\n")

                # user_id 가져오기
                user_id = data.get("user_id")
                if not user_id:
                    logger.error(f"llm/views.py/post - error : user_id가 제공되지 않았습니다.")
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
                    logger.error(f"llm/views.py/post - error : Year, month, day, hour, minute, location, and event_type must be provided.")
                    return JsonResponse({"error": "Year, month, day, hour, minute, location, and event_type must be provided."}, status=502)

                if debug:
                    print("loading...\n\n")

                # 시나리오 입력 구성
                scenario_input = (
                    f"You are an AI that generates scenarios for a deduction game. "
                    f"I will play the role of a detective and try to find the real culprit. "
                    f"Create an appropriate case scenario, considering the suspects and evidence. "
                    f"First, generate only the case scenario.\n\n"
                    f"Here are the characteristics to follow when creating the scenario:\n"
                    f"1. Location of the incident: {location}\n"
                    f"2. Type of event: {event_type}\n"
                    f"3. Date and time of occurrence: {year}-{month}-{day} {hour}:{minute}\n"
                    f"4. There is only one culprit. There can be no accomplices.\n"
                    f"5. There are {3} suspects and {2} pieces of evidence. Do not include these in the scenario. However, keep them in mind when creating the scenario.\n"
                    f"6. The scenario should be 150 characters or less.\n"
                    f"7. All scenarios must be written and structured in Korean.\n\n"
                    f"Now, write the scenario."
                )

                scenario_input = truncate_prompt(scenario_input)

                scenario_image_url = get_scenario_image(location, event_type)
                female_image_url, male_image_urls = get_suspect_images()

                # GPT-4 시나리오 생성
                gpt_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": scenario_input}]
                )

                if debug:
                    print(f"GPT Responce : {gpt_response}\n")

                if not gpt_response.choices or not gpt_response.choices[0].message.content:
                    logger.error(f"llm/views.py/post - error: 시나리오 설명 오류 발생. {user_id}")
                    scenario_description = "시나리오 설명 오류 발생."
                else:
                    scenario_description = gpt_response.choices[0].message.content

                if debug:
                    print(f"시나리오 설명 : {scenario_description}\n")


                """
                # DALL-E 시나리오 이미지 생성
                image_prompt = (
                    f"Generate an image for a deduction game using the image generation tool. "
                    f"The image should depict a crime scene that fits the following scenario described in Korean.\n\n"
                    f"Event type: {event_type}\n"
                    f"Scenario: {scenario_description}\n"
                    f"Time of incident: {year}-{month}-{day} {hour}:{minute}\n"
                    f"Location of the incident: {location}\n\n"
                    f"Ensure the image meets the following conditions:\n"
                    f"1. The perpetrator is a single human with no accomplices.\n"
                    f"2. If the event is a homicide, show the victim's state of death.\n"
                    f"3. If it's a theft, show the perpetrator escaping with the stolen item.\n"
                    f"4. If it's arson, show the victim's belongings being burned and destroyed.\n"
                    f"5. Depict the perpetrator without revealing their identity. Use shadows, silhouettes, or darkness to obscure the perpetrator's face and body. "
                    f"The person should be dressed in black with all facial features hidden.\n"
                    f"6. All people in the image should appear to be Korean.\n\n"
                    f"Now, create the image."
                )
    
                image_response = client.images.generate(
                    model="dall-e-3",
                    prompt=truncate_prompt(image_prompt),
                    n=1,
                    size="1024x1024"
                )
                scenario_image_url = image_response.data[0].url
    
                if debug:
                    print(f"사건 이미지 주소 : {scenario_image_url}\n")
                """

                # Scenario 저장
                scenario = Scenario.objects.create(
                    user_id=user_id,
                    name=f"{location} {event_type}",
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
                evidence_name_last = []
                for i in range(int(data.get("evidence_count", 2))):

                    if debug:
                        print(f"evidence_name_last : {evidence_name_last}\n")

                    evidence_prompt = (
                        f"Generate a piece of evidence for a deduction game. "
                        f"Create one piece of evidence ({i + 1}) that matches the following event type and scenario. The output should be in Korean.\n\n"
                        f"Event type: {event_type}\n"
                        f"Scenario: {scenario_description}\n\n"
                        f"The evidence must adhere to the following characteristics:\n"
                        f"1. It should be relevant to the incident described.\n"
                        f"2. The evidence name should be concise, with a maximum length of 16 characters (VARCHAR(16)).\n"
                        f"3. Provide a brief description of the evidence.\n"
                        f"4. All output must be in Korean.\n")

                    if i == 0:
                        evidence_prompt += f"5. Use the following format for the output:\n"
                    else:
                        for j in evidence_name_last:
                            evidence_prompt += (f"5. Do not generate evidence such as the following: {j}\n"
                                                f"6. CCTV, closed-circuit cameras, and on-site video recordings are not evidence."
                                                f"7. Use the following format for the output:\n")

                    evidence_prompt += (
                        f"Name:\n"
                        f"Description:\n"
                        f"Image URL:\n\n"
                        f"Generate the evidence now."
                    )

                    evidence_response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": evidence_prompt}]
                    )

                    if debug:
                        print(f"Evidence Responce : {evidence_response}\n")

                    evidence_content = evidence_response.choices[0].message.content
                    lines = evidence_content.split("\n")

                    evidence_name = lines[0].split(": ")[1].strip()  # 'Name:' 뒤의 값 추출
                    evidence_description = lines[1].split(": ")[1].strip()  # 'Description:' 뒤의 값 추출

                    if debug:
                        print(f"증거 이름 {i + 1}번 : {evidence_name}\n")
                        print(f"증거 설명 {i + 1}번 : {evidence_description}\n")

                    evidence_image_prompt = (
                        f"Generate an evidence image for a deduction game. "
                        f"Use the image generation tool to create an image of the evidence ({i + 1}) based on the following scenario, event type, and evidence description, all provided in Korean.\n\n"
                        f"Event type: {event_type}\n"
                        f"Scenario: {scenario_description}\n"
                        f"Evidence description: {evidence_description}\n\n"
                        f"Create an image that visually represents the evidence described. "
                        f"Ensure the image reflects the event type, the scenario's context, and the details given in the evidence description. "
                        f"Output the generated image."
                    )

                    evidence_image_response = client.images.generate(
                        model="dall-e-3",
                        prompt=truncate_prompt(evidence_image_prompt),
                        n=1,
                        size="1024x1024"
                    )
                    generate_image_url = evidence_image_response.data[0].url
                    image_data = requests.get(generate_image_url).content

                    # S3에 이미지 업로드
                    uploaded_image_url = upload_to_s3(f"user_{user_id}_scenario_{scenario.id}_evidence_{i + 1}.png", image_data, "image/png")

                    evidence_image_url = uploaded_image_url if uploaded_image_url else "test.jpg"

                    if debug:
                        print(f"사건 이미지 주소 : {evidence_image_url}")

                    evidence_name_last.append(evidence_name)

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
                        "image":evidence_image_url
                    })

                # Suspect 생성
                suspect_list = []
                genders = [0, 0, 1]  # 0: 남성, 1: 여성
                criminal_index = [0, 0, 1]  # 0: 무고인, 1: 범인
                shuffle(genders)  # 남성 2명, 여성 1명으로 섞음
                shuffle(criminal_index) # 범인과 무고인을 섞음

                for i in range(3):
                    criminal_select = criminal_index[i]
                    gender_select = genders[i]
                    suspect_prompt = (
                        f"You have created a fictional deduction game scenario and need to generate a suspect for it. "
                        f"Create one suspect ({i + 1}) based on the following event type and scenario, provided in Korean.\n\n"
                        f"Event type: {event_type}\n"
                        f"Scenario: {scenario_description}\n\n"
                        f"Follow these constraints when generating the suspect:\n"
                        f"1. Each suspect must have a name, job, and a description of their relationship to this scenario.\n"
                        f"2. If 'variable' = 0 is provided next, name it masculine; if 'variable' = 1, name it feminine. "
                        f"'variable' = {gender_select}\n"
                        f"3. All suspects should be Korean and speak Korean.\n"
                        f"4. The suspect's name must be a three-character Korean name.\n"
                        f"5. The job must be a real occupation, limited to 16 characters (VARCHAR(16)).\n"
                        f"6. The description should be based on their relationship to the victim and the incident.\n"
                        f"7. Generate an initial statement from the suspect based on the description of the suspect you created.\n"
                        f"8. There is only one true culprit, with no accomplices.\n"
                        f"9. Use the following format for the output:\n"
                        f"Name:\n"
                        f"Job:\n"
                        f"description:\n"
                        f"initial_statement:\n"
                        f"Image URL:\n\n"
                        f"All output must be in Korean.\n\n"
                        f"Generate the suspect now."
                    )
                    suspect_response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": suspect_prompt}]
                    )

                    if debug:
                        print(f"suspect response : {suspect_response}\n")

                    if not suspect_response.choices or not suspect_response.choices[0].message.content:
                        suspect_data = ["이름: 기본 이름", "성별: 남성", "나이: 30", "직업: 기본 직업", "성격: 기본 성격"]
                    else:
                        suspect_data = suspect_response.choices[0].message.content.split("\n")

                    if debug:
                        print(f"suspect data : {suspect_data}\n")
                        print(f"suspect data_type : {type(suspect_data)}\n")

                    try:

                        suspect_name = suspect_data[0].split(":")[1].strip()   # 이름 추출

                        if gender_select == 0: # 남성
                            suspect_gender = False
                            suspect_image_url = male_image_urls.pop(0)
                        elif gender_select == 1: #여성
                            suspect_gender = True
                            suspect_image_url = female_image_url

                        suspect_age = random.randint(20, 39) #나이 선택

                        suspect_job = suspect_data[1].split(":")[1].strip()  # 직업 추출
                        suspect_description = suspect_data[2].split(":")[1].strip()  # 성격 추출
                        suspect_initial_statement = suspect_data[3].split(":")[1].strip()  #초기 진술 추출

                        if criminal_select == 0: #진범 유/무
                            is_theif = False
                        elif criminal_select == 1:
                            is_theif = True

                    except (IndexError, ValueError) as e:
                        if debug:
                            print(f"e : {e}\n")

                        suspect_name = f"기본 이름 {i + 1}"
                        suspect_gender = False
                        suspect_job = "기본 직업"
                        suspect_age = random.randint(20, 39)  # 기본 나이
                        suspect_description = "기본 설명"
                        is_theif = False

                    if debug:
                        print(f"용의자 이름 : {suspect_name}")
                        print(f"용의자 성별 : {suspect_gender}")
                        print(f"용의자 나이 : {suspect_age}")
                        print(f"용의자 직업 : {suspect_job}")
                        print(f"용의자 성격 : {suspect_description}")
                        print(f"용의자 초기 진술 : {suspect_initial_statement}")
                        print(f"범인 여부 : {is_theif}\n")

                    """
                    suspect_image_prompt = (
                        f"Generate an image of a suspect for a fictional deduction game scenario. "
                        f"Use the image generation tool to create {i + 1} image(s) of the suspect based on the following details, all provided in Korean.\n\n"
                        f"Suspect characteristics:\n"
                        f"Name: {suspect_name}\n"
                        f"Gender: {suspect_gender}\n"
                        f"Age: {suspect_age}\n"
                        f"Job: {suspect_job}\n"
                        f"description: {suspect_description}\n\n"
                        f"Create an image that visually represents the suspect based on these characteristics. "
                        f"Ensure that the image accurately reflects the suspect's gender, age, job, and description. "
                        f"The suspect should appear to be Korean. "
                        f"Only one person's face should appear in the image, and only one face should be visible. "
                        f"Generate the image now."
                    )
                    suspect_image_response = client.images.generate(
                        model="dall-e-3",
                        prompt=truncate_prompt(suspect_image_prompt),
                        n=1,
                        size="1024x1024"
                    )
                    suspect_image_url = suspect_image_response.data[0].url
    
                    if debug:
                        print(f"사건 이미지 주소 : {suspect_image_url}")
                    """

                    suspect = Suspect.objects.create(
                        scenario=scenario,
                        name=suspect_name,
                        gender=suspect_gender,
                        age=suspect_age,
                        job=suspect_job,
                        description= suspect_description,
                        init_chat= suspect_initial_statement,
                        is_theif=is_theif,
                        image= suspect_image_url
                    )

                    suspect_list.append({
                        "id": suspect.id,
                        "name": suspect.name,
                        "gender": suspect_gender,
                        "age": suspect.age,
                        "job": suspect.job,
                        "description" : suspect_description,
                        "init_chat" : suspect_initial_statement,
                        "is_theif": is_theif,
                        "image": suspect_image_url
                    })

                logger.info(f"llm/views.py/post - 시나리오 생성 완료: {scenario_id}")
                return JsonResponse({
                    "scenario_id": scenario_id,
                    "scenario_description": scenario_description,
                    "scenario_image": scenario_image_url,
                    "evidence": evidence_list,
                    "suspects": suspect_list
                }, status=201)

            except Exception as e:
                logger.exception(f"llm/views.py/post - 예외 발생 : {e}")
                return JsonResponse({"error": str(e)}, status=500)

        logger.error(f"llm/views.py/post - error : Invalid request method")
        return JsonResponse({"error": "Invalid request method"}, status=502)
