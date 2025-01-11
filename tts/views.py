import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.core.files.storage import default_storage
from celery.result import AsyncResult
from django.conf import settings
from .tasks import process_tts

class ChangeSoundView(APIView):
    """
    TTS 작업 생성 및 결과 반환 API
    - 3개의 고정된 task_id에 따라 voice_id를 설정하고 작업을 생성합니다.
    """

    def post(self, request):
        # 클라이언트 요청에서 sentence 가져오기
        sentence = request.data.get('sentence')

        # 클라이언트 요청에서 task_id 값 가져오기
        task_id = request.data.get('task_id')

        # 입력 검증
        if not sentence or not task_id:
            return Response({"error": "Sentence and task_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        # task_id가 고정된 값인지 확인
        if task_id not in settings.ELEVENLABS_VOICE_ID:
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

        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class GetAudioResultView(APIView):
    """
    TTS 작업 결과 API
    - 고정된 task_id를 기반으로 작업 상태를 확인하고, 작업 완료 시 결과 파일을 반환합니다.
    """

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
                return Response({"status": "SUCCESS", "audio_base64": audio_base64}, status=status.HTTP_200_OK)

            # 작업 실패
            return Response({"error": "Task failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 작업이 진행 중인 경우
        return Response({"status": "PENDING"}, status=status.HTTP_202_ACCEPTED)