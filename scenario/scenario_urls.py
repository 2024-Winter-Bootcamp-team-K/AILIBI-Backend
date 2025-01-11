from django.urls import path
from . import views

urlpatterns = [
    path('', views.ScenariosView.as_view(), name='scenarios'),
]