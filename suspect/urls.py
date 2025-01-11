from django.urls import path
from .views import SuspectsView

urlpatterns = [
    path('', SuspectsView.as_view(), name='suspects'),
]