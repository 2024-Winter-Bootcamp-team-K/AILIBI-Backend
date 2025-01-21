from django.urls import path
from .views import websocket_test, WebSocketConnectAPIView, WebSocketMessageAPIView, WebSocketStatusAPIView

urlpatterns = [
    # WebSocket 테스트용 URL
    path("/test-websocket", websocket_test, name="websocket_test"),
    path('/websocket/connect', WebSocketConnectAPIView.as_view(), name='websocket_connect'),
    path('/<int:suspects_id>', WebSocketMessageAPIView.as_view(), name='websocket_message'),
    path('/websocket/status', WebSocketStatusAPIView.as_view(), name='websocket_status'),
]