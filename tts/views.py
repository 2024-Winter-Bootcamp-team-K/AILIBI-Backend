import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.core.files.storage import default_storage
from celery.result import AsyncResult
from django.conf import settings
from .tasks import process_tts

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import logging

logger = logging.getLogger(__name__)

class ChangeSoundView(APIView):
    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    """
    TTS 작업 생성 및 결과 반환 API
    - 3개의 고정된 task_id에 따라 voice_id를 설정하고 작업을 생성합니다.
    """

    @swagger_auto_schema(
        operation_id="TTS 작업 생성 및 결과 반환 API",
        operation_description="3개의 고정된 task_id에 따라 voice_id를 설정하고 작업을 생성합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'sentence': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='TTS 변환 할 문장',
                    example='K팀 화이팅'),
                'task_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='TTS 변환 할 목소리 선택',
                    example='1'),
            },
            required=['sentence', 'task_id']
        ),
        responses={
            202: openapi.Response(
                description="TTS 변환 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'task_id': openapi.Schema(
                            type=openapi.TYPE_STRING,\
                            description='만들어진 TTS의 task_id',
                            example='1'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request due to missing or invalid parameters.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message.',
                            example='문장과 task_id를 입력하세요.'
                        )
                    }
                )
            ),
        }
    )
    def get(self, request):
        data = {"message": "Don't User Get Method"}
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        # 클라이언트 요청에서 sentence 가져오기
        sentence = request.data.get('sentence')

        # 클라이언트 요청에서 task_id 값 가져오기
        task_id = request.data.get('task_id')

        # 입력 검증
        if not sentence or not task_id:
            logger.warning(f"tts/views.py/ChangeSoundView - Sentence and task_id are required")
            return Response({"error": "Sentence and task_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        # task_id가 고정된 값인지 확인
        if task_id not in settings.ELEVENLABS_VOICE_ID:
            logger.warning(f"tts/views.py/ChangeSoundView - Invalid task_id. Allowed task_ids: {list(settings.ELEVENLABS_VOICE_ID.keys())}")
            return Response({"error": f"Invalid task_id. Allowed task_ids: {list(settings.ELEVENLABS_VOICE_ID.keys())}"},
                            status=status.HTTP_400_BAD_REQUEST)

        # 기존 작업 상태 초기화
        existing_task = AsyncResult(task_id)
        if existing_task.state != "PENDING":
            existing_task.forget()

        # voice_id 매핑
        voice_id = settings.ELEVENLABS_VOICE_ID[task_id]

        # Celery 작업 생성 (고정된 task_id 사용)
        task = process_tts.apply_async(args=[sentence, voice_id], task_id=task_id)

        logger.info(f"tts/views.py/ChangeSoundView - Allowed task_ids. {task_id}")
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class GetAudioResultView(APIView):
    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    """
    TTS 작업 결과 API
    - 고정된 task_id를 기반으로 작업 상태를 확인하고, 작업 완료 시 결과 파일을 반환합니다.
    """

    @swagger_auto_schema(
        operation_id="TTS 작업 결과 API",
        operation_description="고정된 task_id를 기반으로 작업 상태를 확인하고, 작업 완료 시 결과 파일을 반환합니다.",
        manual_parameters=[
            openapi.Parameter(
                'task_id', openapi.IN_PATH,
                description="작업 결과 가져올 ID",
                type=openapi.TYPE_STRING,
                required=True,
                example="1"
            )
        ],
        responses={
            200: openapi.Response(
                description="음성 변환 성공, 오디오 파일 반환",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='반환 상태',
                            example='성공'),
                        'audio_base64': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Base64 인코딩된 음성 파일',
                            example='<Base64 encoded audio data>'
                        )
                    }
                )
            ),
            202: openapi.Response(
                description="이미 오디오 데티어 반환 중 입니다.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='반환 상태',
                            example='진행 중'),
                    }
                )
            ),
            500: openapi.Response(
                description="서버 에러 발생",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Error message.',
                            example='서버 에러 발생가 발생하였습니다.'
                        )
                    }
                )
            ),
        }
    )

    def get(self, request, task_id, *args, **kwargs):
        """
        TTS 작업 상태 확인 및 Base64 오디오 데이터 반환.
        """
        # Celery 작업 상태 확인
        result = AsyncResult(task_id)

        if result.ready():
            if result.successful():
                # 작업 성공: Base64 데이터 반환
                audio_base64 = result.result
                logger.info(f"tts/views.py/GetAudioResultView - status:SUCCESS / audio_base64:{audio_base64}")
                return Response({"status": "SUCCESS", "audio_base64": audio_base64}, status=status.HTTP_200_OK)

            # 작업 실패
            logger.warning(f"tts/views.py/GetAudioResultView - error : Task Failed.")
            return Response({"error": "Task failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 작업이 진행 중인 경우
        logger.warning(f"tts/views.py/GetAudioResultView - status : PENDING")
        return Response({"status": "PENDING"}, status=status.HTTP_202_ACCEPTED)