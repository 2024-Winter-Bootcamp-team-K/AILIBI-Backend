from django.urls import path
from .views import ChangeSoundView, GetAudioResultView

urlpatterns = [
    path('/change_sound', ChangeSoundView.as_view(), name='tts_create'),
    path('/<str:task_id>', GetAudioResultView.as_view(), name='tts_result'),
]