from django.urls import path
from .views import ScenarioAPIView, GenerateEvidenceAPIView, GenerateSuspectAPIView

urlpatterns = [
    path('/create', ScenarioAPIView.as_view(), name='create_scenario'),
    path('/evidence/<int:scenario_id>', GenerateEvidenceAPIView.as_view(), name='generate_evidence'),
    path('/suspect/<int:scenario_id>', GenerateSuspectAPIView.as_view(), name='generate_suspect'),
]
