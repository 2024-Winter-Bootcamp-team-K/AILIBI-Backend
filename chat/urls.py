from django.urls import path
from .views import websocket_test

urlpatterns = [
    # WebSocket 테스트용 URL
    path("test-websocket/", websocket_test, name="websocket_test"),
]