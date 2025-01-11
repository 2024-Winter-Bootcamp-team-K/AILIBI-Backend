from django.urls import path
from .views import create_scenario

urlpatterns = [
    path('', create_scenario, name='create_scenario'),
]
