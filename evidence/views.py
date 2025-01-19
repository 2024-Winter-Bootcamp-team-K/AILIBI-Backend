from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Evidence
from .serializers import EvidenceSerializer, EvidenceChooseSerializer

import logging

logger = logging.getLogger(__name__)

class EvidenceView(APIView):
    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    @swagger_auto_schema(
        operation_id= "시나리오 ID로 증거 목록 조회",
        operation_description="{scenario_id}에 속한 모든 증거 불러오기",
        method="GET",
        manual_parameters=[
            openapi.Parameter(
                'scenario_id', openapi.IN_QUERY,
                description="ID of the scenario",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="List of evidences",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'evidences': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT
                            )
                        )
                    }
                )
            ),
            400: "scenario_id is required"
        }
    )
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
    def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    @swagger_auto_schema(
        operation_id= "증거 ID로 선택한 증거 조회",
        operation_description="선택한 {evidence_id} 불러오기",
        method="GET",
        responses={
            200: openapi.Response(
                description="Evidence details",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Evidence ID"
                        ),
                        'name': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Name of the evidence"
                        ),
                        'description': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Description of the evidence"
                        )
                    }
                )
            ),
            404: "Evidence not found"
        }
    )
    def get(self, request, evidences_id):
        try:
            evidence = Evidence.objects.get(id=evidences_id)
            serializer = EvidenceChooseSerializer(evidence)

            logger.info(f"evidence/views/EvidenceChooseView/ 200_OK : {serializer.data}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Evidence.DoesNotExist:
            logger.error(f"evidence/views/EvidenceChooseView/ error : Evidence not found")
            return Response({'error': 'Evidence not found'}, status=status.HTTP_404_NOT_FOUND)
