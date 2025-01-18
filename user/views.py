from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, LoginSerializer
from .models import User

import logging

logger = logging.getLogger(__name__)


#회원 가입
class UserRegistrationView(APIView):
    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
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
                        "name": "test0419",
                        "email": "test0419@example.com",
                        "passw0rd": "test0419",
                        "passw0rd_check": "test0419"
                    }
                }
            ),
            400: openapi.Response(
                description="Invalid input data",
                examples={
                    "application/json": {
                        "name": "test4019",
                        "email": "test4019@example.com",
                        "passw0rd": "test4019",
                        "passw0rd_check": "test4019"
                    }
                }
            )
        }
    )
    def get(self, request):
        data = {"message": "Don't User Get Method"}
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"user/views.py/UserRegistrationView - User created successfully : {serializer.data['email']}")
            return Response({
                "name": serializer.validated_data["name"],
                "email": serializer.validated_data["email"]
            }, status=status.HTTP_201_CREATED)
        logger.warning(f"user/views.py/UserRegistrationView - User registration failed : {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#로그인
class LoginView(APIView):
    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
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
    def get(self, request):
        data = {"message": "Don't User Get Method"}
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)  # 로그인 성공 시 사용자 정보
            logger.info(f"user/views.py/LoginView - Login successful : {user.id}")
            return Response({
                "id" : user.id,
                "name": user.name,
                "email": user.email
            }, status=status.HTTP_201_CREATED)
        logger.warning(f"user/views.py/LoginView - Login attempt failed:, {serializer.errors}")
        return Response({"Error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

"""
class UserDetailView(APIView):
    def get(self, request, user_id):
        try:
            # user_id로 사용자 조회
            user = User.objects.get(id=user_id, is_deleted=False)  # 삭제되지 않은 사용자만 조회
            logger.info(f"user/views.py/UserDetailView - User detail requested: {user.id}")
            return Response({
                "name": user.name,
                "email": user.email
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # 사용자가 존재하지 않거나 삭제된 경우
            logger.error(f"user/views.py/UserDetailView - User not found: {user_id}")
            return Response({"Error": "서버로부터 잘못된 요청이 전송 되었습니다."}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            # 기타 예외 처리
            logger.exception(f"user/views.py/UserDetailView - Unexpected error: {e}")
            return Response({"Error": "서버에 에러가 발생하였습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
"""