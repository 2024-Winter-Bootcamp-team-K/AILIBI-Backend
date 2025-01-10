from django.urls import path
from . import views

urlpatterns = [
    path('<int:scenario_id>', views.ScenariosView.as_view(), name='scenarios'),
]