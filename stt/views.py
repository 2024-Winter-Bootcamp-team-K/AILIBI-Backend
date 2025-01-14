import base64
import json
import requests
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import logging

logger = logging.getLogger(__name__)

@csrf_exempt  # 이 함수에서는 CSRF 검사를 생략
def stt_process(request):

#    프론트엔드에서 BASE64로 인코딩된 오디오 데이터를 받아 네이버 클로바 STT API를 호출하여 텍스트를 반환하는 뷰 함수.
#    주요 처리 단계:
#    1. POST 요청에서 BASE64 데이터를 추출합니다.
#    2. BASE64 데이터를 디코딩하여 로컬 임시 파일로 저장합니다.
#    3. 네이버 클로바 STT API를 호출하여 텍스트 변환 결과를 받아옵니다.
#    4. 결과를 JSON 형태로 반환합니다.


    # 1. 요청이 POST인지 확인
    if request.method == 'POST':
        try:
            # 1-1. 요청 본문에서 JSON 데이터를 파싱
            data = json.loads(request.body)

            # 1-2. BASE64로 인코딩된 오디오 데이터 가져오기
            base64_audio_data = data.get('audio')  # 'audio' 키의 값을 가져옴

            if not base64_audio_data:
                # 오디오 데이터가 없으면 에러 메시지 반환
                logger.error(f"user/views.py/stt_process - error: No audio data provided")
                return JsonResponse({'error': 'No audio data provided'}, status=400)

            # 2. BASE64 데이터를 디코딩하여 임시 오디오 파일로 저장
            # 2-1. BASE64 데이터를 디코딩
            audio_data = base64.b64decode(base64_audio_data)

            # 2-2. 임시 파일 경로 설정
            audio_file_path = '/tmp/input_audio.wav'

            # 2-3. 디코딩된 데이터를 파일로 저장
            with open(audio_file_path, 'wb') as f:
                f.write(audio_data)  # 디코딩된 데이터를 파일에 기록

            # 3. 네이버 클로바 STT API 호출
            # 3-1. API 엔드포인트와 헤더 설정
            url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt?lang=Kor"  # 네이버 클로바 STT API 엔드포인트
            headers = {
                "Content-Type": "application/octet-stream",  # 오디오 파일은 바이너리 형태로 전송
                "X-NCP-APIGW-API-KEY-ID": settings.NAVER_CLIENT_ID,  # API Client ID
                "X-NCP-APIGW-API-KEY": settings.NAVER_CLIENT_SECRET,  # API Secret Key
            }

            # 3-2. 파일을 바이너리로 읽어 API 요청
            with open(audio_file_path, 'rb') as f:
                response = requests.post(url, headers=headers, data=f)

                # 3-3. API 응답 처리
            if response.status_code == 200:
                # API 요청 성공 시 결과 반환
                result = response.json()  # JSON 응답을 파싱
                text = result.get('text', '')
                logger.info(f"user/views.py/stt_process - text:, {text}")
                return JsonResponse({'text': text}, json_dumps_params={'ensure_ascii': False})
                # 유니코드 이스케이프 문자열 대신 한글 텍스트로 반환.
            else:
                # API 요청 실패 시 오류 메시지 반환
                logger.error(f"user/views.py/stt_process - error: {response.text}")
                return JsonResponse({'error': response.text}, status=response.status_code)

        except json.JSONDecodeError:
            # 4. 요청 데이터가 JSON이 아닌 경우 처리
            logger.error(f"user/views.py/stt_process - error: Invalid JSON data")
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

        except base64.binascii.Error:
            # 5. BASE64 디코딩 실패 처리
            logger.error(f"user/views.py/stt_process - error: Invalid BASE64 data")
            return JsonResponse({'error': 'Invalid BASE64 data'}, status=400)

        except Exception as e:
            # 6. 기타 예상하지 못한 예외 처리
            logger.exception(f"user/views.py/stt_process - error: {e}")
            return JsonResponse({'error': str(e)}, status=500)

        finally:
            # 7. 임시 파일 삭제 (성공, 실패 여부에 상관없이 실행)
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)  # 파일 삭제

    # 8. POST 요청이 아닌 경우 처리
    logger.error(f"user/views.py/stt_process - error: Invalid request method")
    return JsonResponse({'error': 'Invalid request method'}, status=405)
