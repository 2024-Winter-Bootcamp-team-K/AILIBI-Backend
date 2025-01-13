from django.urls import path
from .views import EvidenceView, EvidenceChooseView

urlpatterns = [
    path('', EvidenceView.as_view()),
    path('<int:evidences_id>', EvidenceChooseView.as_view(), name='evidence-choose'),
]