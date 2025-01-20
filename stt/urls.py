from django.urls import path
from .views import STTProcessAPIView

urlpatterns = [
    path('', STTProcessAPIView.as_view(), name="stt_process"),  # APIView 등록
]