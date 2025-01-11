import requests
import base64
from django.conf import settings
from celery import shared_task


@shared_task
def process_tts(sentence, voice_id):
    """
    고정된 task_id와 voice_id에 따라 TTS 변환 작업을 수행합니다.

    Args:
        sentence (str): 변환할 텍스트
        voice_id (str): 음성 변환에 사용할 voice_id

    Returns:
        str: 저장된 음성 파일 경로
    """
    # ElevenLabs TTS API URL 구성
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    # 요청 페이로드 구성
    payload = {
        "text": sentence,
        "model_id": settings.ELEVENLABS_MODEL_ID,
        "voice_settings": {
            "stability": 0.35,
            "similarity_boost": 0.75,
            "style": 0.02,
            "use_speaker_boost": True
        }
    }

    # 요청 헤더 구성
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": settings.ELEVENLABS_API_KEY
    }

    # ElevenLabs API 요청
    response = requests.post(url, json=payload, headers=headers)

    # 요청 실패 시 예외 발생
    response.raise_for_status()

    # 음성 데이터(Base64로 변환)
    audio_data = response.content
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')

    # Base64 문자열 반환
    return audio_base64