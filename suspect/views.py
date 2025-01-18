from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Suspect
from chat.models import Chat
from .serializers import SuspectSerializer

import logging

logger = logging.getLogger(__name__)

class SuspectsView(APIView):
    async def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    @swagger_auto_schema(
        operation_id= "시나리오 ID로 용의자 목록 조회",
        operation_description="{scenario_id}에 속한 모든 용의자 불러오기",
        manual_parameters=[
            openapi.Parameter(
                'scenario_id', openapi.IN_QUERY,
                description="scenario_id",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="용의자 목록",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'suspects': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT
                            )
                        )
                    }
                )
            ),
            400: "scenario_id가 필요합니다."
        }
    )
    async def get(self, request):
        scenario_id = request.GET.get('scenario_id')
        if not scenario_id:
            logger.error(f"suspect/views.py/SuspectsView - error : scenario_id is required")
            return Response({"error": "scenario_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        suspects = Suspect.objects.filter(scenario_id=scenario_id)
        suspect_data = []

        for suspect in suspects:
            chat = Chat.objects.filter(suspect_id=suspect.id).first()
            data = SuspectSerializer(suspect).data
            data['init_chat'] = chat.init_chat if chat else ""
            suspect_data.append(data)

        logger.info(f"suspect/views.py/SuspectsView - {scenario_id} : {suspect_data}")
        return Response({"suspects": suspect_data}, status=status.HTTP_200_OK)

class SuspectDetailView(APIView):
    async def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    @swagger_auto_schema(
        operation_id="용의자 ID로 선택한 용의자 조회",
        operation_description="선택한 {suspect_id} 불러오기",
        responses={
            200: openapi.Response(
                description="용의자 컬럼",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="Suspect ID"
                        ),
                        'init_chat': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Initial chat"
                        )
                    }
                )
            ),
            404: "Suspect or Chat not found"
        }
    )
    async def get(self, request, suspect_id):
        try:
            suspect = Suspect.objects.get(id=suspect_id)
            chats = Chat.objects.filter(suspect_id=suspect_id)
            init_chat = [chat.init_chat for chat in chats]
            suspect_data = SuspectSerializer(suspect).data
            suspect_data["init_chat"] = init_chat
            logger.info(f"suspect/views.py/SuspectsView - {suspect.id} : {suspect_data}")
            return Response(suspect_data, status=status.HTTP_200_OK)
        except Suspect.DoesNotExist:
            logger.error(f"suspect/views.py/SuspectDetailView - error : Suspect not found")
            return Response({"error": "Suspect not found"}, status=status.HTTP_404_NOT_FOUND)
        except Chat.DoesNotExist:
            logger.error(f"suspect/views.py/SuspectDetailView - error : Chat not found")
            return Response({"error": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)


class SuspectsChooseView(APIView):
    async def options(self, request, *args, **kwargs):
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    @swagger_auto_schema(
        operation_id="용의자 ID로 범인 지목",
        operation_description="범인 지목",
        manual_parameters=[
            openapi.Parameter(
                'suspect_id', openapi.IN_QUERY,
                description="ID of the suspect",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="범인 유무",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'is_theif': openapi.Schema(
                            type=openapi.TYPE_BOOLEAN,
                            description="Thief status"
                        )
                    }
                )
            ),
            400: "suspect_id is required",
            404: "Suspect not found"
        }
    )
    async def get(self, request):
        suspect_id = request.GET.get('suspect_id')

        if not suspect_id:
            logger.error(f"suspect/views.py/SuspectChooseView - error : suspect_id is required")
            return Response({"error": "suspect_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            suspect = Suspect.objects.get(id=suspect_id)
            is_theif_value = suspect.is_theif

            logger.info(f"suspect/views.py/SuspectChooseView - {suspect.id} : {is_theif_value}")
            return Response({"is_theif": is_theif_value}, status=status.HTTP_200_OK)

        except Suspect.DoesNotExist:
            logger.error(f"suspect/views.py/SuspectChooseView - error : Suspect not found")
            return Response({"error": "Suspect not found"}, status=status.HTTP_404_NOT_FOUND)
