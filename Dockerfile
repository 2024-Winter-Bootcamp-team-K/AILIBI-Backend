# 베이스 이미지 설정
FROM python:3.11.9

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    gcc \
    && apt-get clean

# 작업 디렉토리 설정
WORKDIR /backend

# 의존성 설치
RUN pip install --upgrade pip
COPY requirements.txt /backend/
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . /backend

# 포트 설정 (필요에 따라 수정 가능)
EXPOSE 8000

# Celery Worker 실행 명령어 추가
CMD celery -A backend worker -l info

# 컨테이너 실행 명령
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
