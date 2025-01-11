from django.urls import path
from .views import SuspectDetailView

urlpatterns = [
    path('', SuspectDetailView.as_view(), name='suspects-detail'),
]