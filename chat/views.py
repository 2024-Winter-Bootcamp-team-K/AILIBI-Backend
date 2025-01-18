from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import redis
from .Serializers import WebSocketMessageSerializer, WebSocketConnectionSerializer

def websocket_test(request):
    """
    WebSocket 테스트 페이지를 렌더링합니다.
    """
    return render(request, "test.html")



class WebSocketConnectAPIView(APIView):
    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    """
    WebSocket 연결 초기화 API
    """
    @swagger_auto_schema(
        request_body=WebSocketConnectionSerializer,
        operation_id="WebSocket 연결 초기화",
        operation_description="WebSocket 연결을 초기화하고 용의자 ID를 등록합니다.",
        responses={
            202: openapi.Response(
                description="WebSocket 연결 초기화 성공",
                examples={
                    "application/json": {
                        "message": "WebSocket 연결이 성공적으로 초기화되었습니다.",
                        "suspect_id": 123
                    }
                },
            ),
            400: openapi.Response(description="잘못된 요청 데이터입니다."),
        },
    )
    def post(self, request):
        serializer = WebSocketConnectionSerializer(data=request.data)
        if serializer.is_valid():
            suspect_id = serializer.validated_data['suspect_id']

            # Redis에 연결 상태 저장 (예제)
            redis_conn = redis.Redis(host='localhost', port=6379, db=0)
            redis_conn.set(f"websocket:suspect:{suspect_id}", "connected")

            return Response(
                {
                    "message": f"WebSocket 연결이 성공적으로 초기화되었습니다.",
                    "suspect_id": suspect_id,
                },
                status=status.HTTP_202_ACCEPTED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        data = {"message": "Don't User Get Method"}
        return Response(data, status=status.HTTP_200_OK)
    
class WebSocketMessageAPIView(APIView):
    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    """
    WebSocket 메시지 전송 API
    """
    @swagger_auto_schema(
        request_body=WebSocketMessageSerializer,
        operation_id="WebSocket 메시지 전송",
        operation_description="WebSocket으로 메시지를 전송합니다.",
        responses={
            202: openapi.Response(
                description="메시지 전송 성공",
                examples={
                    "application/json": {
                        "message": "메시지가 성공적으로 WebSocket으로 전송되었습니다.",
                        "content": "안녕하세요!"
                    }
                },
            ),
            400: openapi.Response(description="잘못된 요청 데이터입니다."),
        },
    )
    def post(self, request):
        serializer = WebSocketMessageSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.validated_data['message']

            # 메시지 처리 로직 (예제: Redis에 저장)
            redis_conn = redis.Redis(host='localhost', port=6379, db=0)
            redis_conn.rpush("websocket:messages", message)

            return Response(
                {
                    "message": "메시지가 성공적으로 WebSocket으로 전송되었습니다.",
                    "content": message,
                },
                status=status.HTTP_202_ACCEPTED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        data = {"message": "Don't User Get Method"}
        return Response(data, status=status.HTTP_200_OK)

class WebSocketStatusAPIView(APIView):
    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    """
    WebSocket 상태 확인 API
    """
    @swagger_auto_schema(
        operation_id="WebSocket 상태 확인",
        operation_description="WebSocket 연결 상태를 확인합니다.",
        responses={
            200: openapi.Response(
                description="WebSocket 연결 상태 반환",
                examples={
                    "application/json": {
                        "status": "connected",
                        "suspect_id": 123
                    }
                },
            ),
        },
    )
    def get(self, request):
        # Redis에서 연결 상태 확인 (예제)
        redis_conn = redis.Redis(host='localhost', port=6379, db=0)
        suspect_ids = redis_conn.keys("websocket:suspect:*")
        status_list = [
            {
                "suspect_id": int(suspect_id.decode().split(":")[-1]),
                "status": redis_conn.get(suspect_id).decode(),
            }
            for suspect_id in suspect_ids
        ]

        return Response(status_list, status=status.HTTP_200_OK)