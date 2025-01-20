import base64
import json
import requests
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)

class STTProcessAPIView(APIView):
    @swagger_auto_schema(
        operation_id="STT 처리",
        operation_description="BASE64로 인코딩된 오디오 데이터를 받아 네이버 클로바 STT API를 호출하여 텍스트 변환 결과를 반환합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'audio': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="BASE64로 인코딩된 오디오 데이터"
                ),
            },
            required=['audio'],  # 필수 필드
        ),
        responses={
            200: openapi.Response(
                description="STT 변환 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'text': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="STT 변환 결과 텍스트"
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="잘못된 요청",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="에러 메시지"
                        ),
                    },
                ),
            ),
            500: openapi.Response(
                description="서버 내부 오류",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="예외 메시지"
                        ),
                    },
                ),
            ),
        },
    )
    def post(self, request):
        """
        POST 요청을 처리하여 STT 변환 결과를 반환합니다.
        """
        audio_file_path = None  # Ensure it's defined

        try:
            # 요청 본문에서 JSON 데이터 파싱
            data = request.data
            base64_audio_data = data.get('audio')

            if not base64_audio_data:
                logger.error("No audio data provided")
                return JsonResponse({'error': 'No audio data provided'}, status=400)

            # BASE64 데이터를 디코딩하여 임시 파일로 저장
            audio_data = base64.b64decode(base64_audio_data)
            audio_file_path = '/tmp/input_audio.wav'
            with open(audio_file_path, 'wb') as f:
                f.write(audio_data)

            # 네이버 클로바 STT API 호출
            url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt?lang=Kor"
            headers = {
                "Content-Type": "application/octet-stream",
                "X-NCP-APIGW-API-KEY-ID": settings.NAVER_CLIENT_ID,
                "X-NCP-APIGW-API-KEY": settings.NAVER_CLIENT_SECRET,
            }

            with open(audio_file_path, 'rb') as f:
                response = requests.post(url, headers=headers, data=f)

            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '')
                logger.info(f"STT result: {text}")
                return JsonResponse({'text': text}, json_dumps_params={'ensure_ascii': False})
            else:
                logger.error(f"Error from STT API: {response.text}")
                return JsonResponse({'error': response.text}, status=response.status_code)

        except json.JSONDecodeError:
            logger.error("Invalid JSON data")
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

        except base64.binascii.Error:
            logger.error("Invalid BASE64 data")
            return JsonResponse({'error': 'Invalid BASE64 data'}, status=400)

        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return JsonResponse({'error': str(e)}, status=500)

        finally:
            # 임시 파일 삭제
            if audio_file_path and os.path.exists(audio_file_path):
                os.remove(audio_file_path)


@csrf_exempt  # 이 함수에서는 CSRF 검사를 생략
def stt_process(request):
    """
    프론트엔드에서 BASE64로 인코딩된 오디오 데이터를 받아 네이버 클로바 STT API를 호출하여 텍스트를 반환하는 뷰 함수.
    주요 처리 단계:
    1. POST 요청에서 BASE64 데이터를 추출합니다.
    2. BASE64 데이터를 디코딩하여 로컬 임시 파일로 저장합니다.
    3. 네이버 클로바 STT API를 호출하여 텍스트 변환 결과를 받아옵니다.
    4. 결과를 JSON 형태로 반환합니다.
    """
    # 1. 요청이 POST인지 확인
    if request.method == 'POST':
        try:
            # 1-1. 요청 본문에서 JSON 데이터를 파싱
            data = json.loads(request.body)

            # 1-2. BASE64로 인코딩된 오디오 데이터 가져오기
            base64_audio_data = data.get('audio')

            if not base64_audio_data:
                # 오디오 데이터가 없으면 에러 메시지 반환
                logger.error("No audio data provided")
                return JsonResponse({'error': 'No audio data provided'}, status=400)

            # 2. BASE64 데이터를 디코딩하여 임시 오디오 파일로 저장
            audio_data = base64.b64decode(base64_audio_data)
            audio_file_path = '/tmp/input_audio.wav'
            with open(audio_file_path, 'wb') as f:
                f.write(audio_data)

            # 3. 네이버 클로바 STT API 호출
            url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt?lang=Kor"
            headers = {
                "Content-Type": "application/octet-stream",
                "X-NCP-APIGW-API-KEY-ID": settings.NAVER_CLIENT_ID,
                "X-NCP-APIGW-API-KEY": settings.NAVER_CLIENT_SECRET,
            }

            with open(audio_file_path, 'rb') as f:
                response = requests.post(url, headers=headers, data=f)

            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '')
                logger.info(f"STT result: {text}")
                return JsonResponse({'text': text}, json_dumps_params={'ensure_ascii': False})
            else:
                logger.error(f"Error from STT API: {response.text}")
                return JsonResponse({'error': response.text}, status=response.status_code)

        except json.JSONDecodeError:
            logger.error("Invalid JSON data")
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

        except base64.binascii.Error:
            logger.error("Invalid BASE64 data")
            return JsonResponse({'error': 'Invalid BASE64 data'}, status=400)

        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return JsonResponse({'error': str(e)}, status=500)

        finally:
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)

    # 8. POST 요청이 아닌 경우 처리
    logger.error("Invalid request method")
    return JsonResponse({'error': 'Invalid request method'}, status=405)
