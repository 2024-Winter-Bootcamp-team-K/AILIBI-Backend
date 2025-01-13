from django.urls import path
from .views import SuspectsView, SuspectsChooseView

urlpatterns = [
    path('', SuspectsView.as_view(), name='suspects'),
    path('choose', SuspectsChooseView.as_view(), name='suspect-choose'),
]