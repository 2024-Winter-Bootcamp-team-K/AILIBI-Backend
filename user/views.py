from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, LoginSerializer
from .models import User

from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)


# 회원 가입
class UserRegistrationView(APIView):
    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    @swagger_auto_schema(
        operation_id="회원가입",
        operation_description="이름와 이메일은 구분된다.\n"
                              "아이디 == 이메일 이다.",
        request_body=UserSerializer,
        responses={
            201: openapi.Response(
                description="User created successfully",
                examples={
                    "application/json": {
                        "name": "test",
                        "email": "test@example.com",
                        "passw0rd": "test",
                        "passw0rd_check": "test"
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid input data",
                examples={
                    "application/json": {
                        "name": "test",
                        "email": "test@example.com",
                        "passw0rd": "test",
                        "passw0rd_check": "test"
                    }
                }
            )
        }
    )
    async def post(self, request):
        serializer = UserSerializer(data=request.data)
        is_valid = await sync_to_async(serializer.is_valid)()
        if is_valid:
            await sync_to_async(serializer.save)()
            logger.info(f"user/views.py/UserRegistrationView - User created successfully : {serializer.data['email']}")
            return Response({
                "name": serializer.validated_data["name"],
                "email": serializer.validated_data["email"]
            }, status=status.HTTP_201_CREATED)
        logger.warning(f"user/views.py/UserRegistrationView - User registration failed : {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 로그인
class LoginView(APIView):
    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    @swagger_auto_schema(
        operation_id="로그인",
        operation_description="email과 password가 필요",
        request_body=LoginSerializer,
        responses={
            201: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "email": "test0419@example.com",
                        "passw0rd": "test0419"
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid login credentials",
                examples={
                    "application/json": {
                        "Error": {
                            "email": ["This field is required."],
                            "passw0rd": ["This field is required."]
                        }
                    }
                }
            )
        }
    )
    async def post(self, request):
        serializer = LoginSerializer(data=request.data)
        is_valid = await sync_to_async(serializer.is_valid)()
        if is_valid:
            email = serializer.validated_data['email']
            user = await sync_to_async(User.objects.get)(email=email)  # 로그인 성공 시 사용자 정보
            logger.info(f"user/views.py/LoginView - Login successful : {user.id}")
            return Response({
                "id": user.id,
                "name": user.name,
                "email": user.email
            }, status=status.HTTP_201_CREATED)
        logger.warning(f"user/views.py/LoginView - Login attempt failed: {serializer.errors}")
        return Response({"Error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
