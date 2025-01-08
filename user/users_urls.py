from django.urls import path
from .views import UserDetailView

urlpatterns = [
    path('<int:user_id>', UserDetailView.as_view(), name='user_detail')
]