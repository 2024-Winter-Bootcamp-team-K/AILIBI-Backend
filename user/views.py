from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer
from .models import User

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "name": serializer.validated_data["name"],
                "email": serializer.validated_data["email"]
            }, status=status.HTTP_201_CREATED)
        elif User.objects.filter(email=request.data.get('email')).exists():
            return Response({"Error": "이미 가입한 이메일입니다."}, status=status.HTTP_409_CONFLICT)
        return Response({"Error": "잘못된 형식입니다."}, status=status.HTTP_400_BAD_REQUEST)
