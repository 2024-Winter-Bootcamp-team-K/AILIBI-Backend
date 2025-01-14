from rest_framework import serializers

class WebSocketConnectionSerializer(serializers.Serializer):
    """
    WebSocket 연결 초기화용 Serializer
    """
    suspect_id = serializers.IntegerField(help_text="연결할 용의자의 ID")

class WebSocketMessageSerializer(serializers.Serializer):
    """
    WebSocket 메시지 전송용 Serializer
    """
    message = serializers.CharField(help_text="WebSocket으로 전송할 메시지 내용")
