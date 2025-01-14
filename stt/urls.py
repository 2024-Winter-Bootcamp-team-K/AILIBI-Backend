from django.urls import path
from . import views

urlpatterns = [
    path('', views.stt_process, name="stt_process"),
]