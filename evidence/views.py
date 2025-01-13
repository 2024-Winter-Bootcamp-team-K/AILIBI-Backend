from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Evidence
from .serializers import EvidenceSerializer, EvidenceChooseSerializer

import logging

logger = logging.getLogger(__name__)

class EvidenceView(APIView):
    def get(self, request):
        scenario_id = request.GET.get('scenario_id')
        if scenario_id:
            evidences = Evidence.objects.filter(scenario_id=scenario_id)
            serializer = EvidenceSerializer(evidences, many=True)

            logger.info(f"evidence/views/EvidenceView/ 200_OK : {serializer.data}")
            return Response({'evidences': serializer.data}, status=status.HTTP_200_OK)
        else:
            logger.error(f"evidence/views/EvidenceView/ error : scenario_id is required")
            return Response({'error': 'scenario_id is required'}, status=status.HTTP_400_BAD_REQUEST)


class EvidenceChooseView(APIView):
    def get(self, request, evidences_id):
        try:
            evidence = Evidence.objects.get(id=evidences_id)
            serializer = EvidenceChooseSerializer(evidence)

            logger.info(f"evidence/views/EvidenceChooseView/ 200_OK : {serializer.data}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Evidence.DoesNotExist:
            logger.error(f"evidence/views/EvidenceChooseView/ error : vidence not found")
            return Response({'error': 'Evidence not found'}, status=status.HTTP_404_NOT_FOUND)