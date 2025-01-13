from django.shortcuts import render

def websocket_test(request):
    """
    WebSocket 테스트 페이지를 렌더링합니다.
    """
    return render(request, "test.html")