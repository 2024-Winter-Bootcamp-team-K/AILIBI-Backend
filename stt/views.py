import base64
import json
import requests
from io import BytesIO
from django.http import JsonResponse
from django.conf import settings
from rest_framework.views import APIView
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
            required=['audio'],
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
        try:
            # 요청 본문에서 JSON 데이터 파싱
            data = request.data
            base64_audio_data = data.get('audio')

            if not base64_audio_data:
                logger.error("No audio data provided")
                return JsonResponse({'error': 'No audio data provided'}, status=400)

            # BASE64 데이터를 디코딩하여 메모리 버퍼로 처리
            audio_data = base64.b64decode(base64_audio_data)
            audio_buffer = BytesIO(audio_data)

            # 네이버 클로바 STT API 호출
            url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt?lang=Kor"
            headers = {
                "Content-Type": "application/octet-stream",
                "X-NCP-APIGW-API-KEY-ID": settings.NAVER_CLIENT_ID,
                "X-NCP-APIGW-API-KEY": settings.NAVER_CLIENT_SECRET,
            }

            response = requests.post(url, headers=headers, data=audio_buffer.getvalue())

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
