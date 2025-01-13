from django.shortcuts import render

def test_chat_view(request):
    """
    WebSocket 테스트용 HTML 템플릿 렌더링.
    """
    return render(request, 'test.html')