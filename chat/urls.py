from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    # 테스트용 HTML 파일을 보여주는 뷰 연결
    path('chat/', TemplateView.as_view(template_name="test.html"), name='chat'),
]