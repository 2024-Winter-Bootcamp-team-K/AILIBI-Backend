# your_app_name/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:suspect_id>/', consumers.MyConsumer.as_asgi()),
]
