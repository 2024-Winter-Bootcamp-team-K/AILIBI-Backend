from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, LoginSerializer
from .models import User

#회원 가입
class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "name": serializer.validated_data["name"],
                "email": serializer.validated_data["email"]
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#로그인
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)  # 로그인 성공 시 사용자 정보
            return Response({
                "name": user.name,
                "email": user.email
            }, status=status.HTTP_201_CREATED)

        return Response({"Error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)