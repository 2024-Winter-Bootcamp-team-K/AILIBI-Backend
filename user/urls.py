from django.urls import path
from .views import UserRegistrationView, LoginView

urlpatterns = [
    path('/auth', UserRegistrationView.as_view(), name='user-register'),
    path('/auth/login/', LoginView.as_view(), name='user-login'),
]