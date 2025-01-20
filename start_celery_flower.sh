#!/bin/sh

# Worker 실행 (concurrency는 작업 병렬 수 설정)
celery -A Backend worker --loglevel=info --concurrency=4 -n worker_1_@%h & # 워커 1번
celery -A Backend worker --loglevel=info --concurrency=4 -n worker_2_@%h & # 워커 2번

# Flower 실행 (모니터링 도구)
celery -A Backend flower --port=5555 --basic_auth=guest:guest --broker=$CELERY_BROKER_URL --broker_api=$CELERY_BROKER_API_URL