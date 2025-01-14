from django.urls import path
from . import views

urlpatterns = [
    path('', views.ScenarioAPIView.as_view(), name='create_scenario'),
]
