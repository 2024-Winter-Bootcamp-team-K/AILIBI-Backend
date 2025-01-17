# your_app_name/routing.py
from django.urls import path
from chat.consumers import MyConsumer

websocket_urlpatterns = [
    path('ws/chat/<int:suspect_id>', MyConsumer.as_asgi()),
    ]