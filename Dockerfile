#Python 베이스 이미지 선택
FROM python:3.12

#작업 디렉토리 설정
WORKDIR /backend

#소스 코드 복사
COPY . /backend

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    gcc \
    && apt-get clean

#의존성 파일 복사 및 설치(캐시 삭제)
COPY requirements.txt /backend/
RUN pip install --no-cache-dir -r requirements.txt

# Dockerfile
RUN python manage.py collectstatic --noinput


#실행 명령어
CMD ["sh", "-c", "python manage.py collectstatic --noinput && \
    python manage.py migrate && \
    daphne -b 0.0.0.0 -p $PORT Backend.asgi:application"]
