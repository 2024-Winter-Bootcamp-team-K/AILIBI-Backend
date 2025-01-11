from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Evidence
from .serializers import EvidenceSerializer, EvidenceChooseSerializer

class EvidenceView(APIView):
    def get(self, request):
        scenario_id = request.GET.get('scenario_id')
        if scenario_id:
            evidences = Evidence.objects.filter(scenario_id=scenario_id)
            serializer = EvidenceSerializer(evidences, many=True)
            return Response({'evidences': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'scenario_id is required'}, status=status.HTTP_400_BAD_REQUEST)


class EvidenceChooseView(APIView):
    def get(self, request, evidences_id):
        try:
            evidence = Evidence.objects.get(id=evidences_id)
            serializer = EvidenceChooseSerializer(evidence)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Evidence.DoesNotExist:
            return Response({'error': 'Evidence not found'}, status=status.HTTP_404_NOT_FOUND)