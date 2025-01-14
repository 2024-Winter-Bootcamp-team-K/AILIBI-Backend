from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User
from scenario.models import Scenario
from chat.models import Chat
from suspect.models import Suspect
from evidence.models import Evidence

from .serializers import His_ScenarioSerializer, His_SuspectSerializer, ScenarioSerializer, SuspectSerializer, EvidenceSerializer

import logging

logger = logging.getLogger(__name__)

# /histories?user_id={userId}, /histories?scenario_id={scenarioId}, /histories?suspect_id={suspectId}
class HistoriesView(APIView):


    @swagger_auto_schema(
        operation_id="모든 플레이 기록 불러오기/선택한 플레이 기록 불러오기/선택한 플레이의 용의자와 심문 내용 불러오기",
        operation_description="user_id = 모든 플레이 기록 불러오기\n"
                              "scenario_id = 선택한 플레이 기록 불러오기\n"
                              "suspect_id = 선택한 플레이의 용의자와 심문 내용 불러오기\n",
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description="User ID to filter histories"),
            openapi.Parameter('scenario_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description="Scenario ID to filter histories"),
            openapi.Parameter('suspect_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description="Suspect ID to filter chat histories"),
        ],
        responses={
            200: openapi.Response(
                description="Successfully retrieved histories",
            ),
            404: openapi.Response(description="Scenario or suspect not found"),
            400: openapi.Response(description="Invalid request parameters")
        }
    )

    def get(self, request):
        user_id = request.query_params.get('user_id')           #모든 플레이 기록 불러오기
        scenario_id = request.query_params.get('scenario_id')   #선택한 플레이 기록 불러오기
        suspect_id = request.query_params.get('suspect_id')     # 선택한 용의자와 심문 내용 불러오기

        if user_id:
            user = get_object_or_404(User, id=user_id)
            scenarios = Scenario.objects.filter(user_id=user.id)
            serializer = His_ScenarioSerializer(scenarios, many=True)
            logger.info(f"scenario/views.py/HistoriesView - error: Invalid JSON data")
            return Response({"scenarios": serializer.data}, status=status.HTTP_200_OK)

        elif scenario_id:

            # Scenario 정보 가져오기
            scenario = Scenario.objects.filter(id=scenario_id).first()

            if not scenario:
                logger.error(f"scenario/views.py/HistoriesView - error: Scenario not found")
                return Response({"error": "Scenario not found"}, status=status.HTTP_404_NOT_FOUND)

            # Suspects 정보 가져오기
            suspects = Suspect.objects.filter(scenario_id=scenario_id)

            # Evidence 정보 가져오기
            evidences = Evidence.objects.filter(scenario_id=scenario_id)


            suspects_data = His_SuspectSerializer(suspects, many=True).data

            # 각 용의자에 대해 init_chat 가져오기
            for suspect_data in suspects_data:
                chat = Chat.objects.filter(suspect_id=suspect_data['id']).first()

                suspect_data['init_chat'] = chat.init_chat if chat else ''

            # Scenario, Suspects, Evidence 직렬화
            scenario_data = ScenarioSerializer(scenario).data
            evidence_data = EvidenceSerializer(evidences, many=True).data

            # 최종 응답 데이터 구성
            response_data = {
                "scenarios": [scenario_data],
                "suspects": suspects_data,
                "evidences": evidence_data
            }

            logger.info(f"user/views.py/HistoriesView - resopnce_ok: {response_data}")
            return Response(response_data, status=status.HTTP_200_OK)

        elif suspect_id:
            chat = get_object_or_404(Chat, suspect_id=suspect_id)

            # Split messages by "/CHANGE "
            user_chat_messages = chat.user_chat.split('/CHANGE ')
            suspect_chat_messages = chat.suspect_chat.split('/CHANGE ')

            # Remove empty strings in case "/CHANGE " is at the start or end
            user_chat_messages = [msg for msg in user_chat_messages if msg]
            suspect_chat_messages = [msg for msg in suspect_chat_messages if msg]

            # Structure the response as specified
            response_data = {
                "user_chat": [
                    {"message": user_chat_messages}
                ],
                "suspect_chat": [
                    {"message": suspect_chat_messages}
                ]
            }

            logger.info(f"user/views.py/HistoriesView - resopnce_ok: {response_data}")
            return Response(response_data, status=status.HTTP_200_OK)

        else:
            return Response({'error': '잘못된 요청'}, status=status.HTTP_400_BAD_REQUEST)



    @swagger_auto_schema(
        operation_id="선택한 플레이 기록 삭제하기",
        operation_description="{scenario_id}로 시나리오 (논리적)삭제 하기",
        manual_parameters=[
            openapi.Parameter('scenario_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True,
                              description="Scenario ID to delete")
        ],
        responses={
            200: openapi.Response(description="Scenario deleted successfully"),
            400: openapi.Response(description="scenario_id is required for deletion")
        }
    )

    def delete(self, request):
        scenario_id = request.query_params.get('scenario_id')

        if scenario_id:
            suspect_ids = Suspect.objects.filter(scenario_id=scenario_id).first()

            Scenario.objects.filter(id=scenario_id).update(is_deleted=True)
            Evidence.objects.filter(scenario_id=scenario_id).update(is_deleted=True)
            Suspect.objects.filter(scenario_id=scenario_id).update(is_deleted=True)
            Chat.objects.filter(suspect_id=suspect_ids).update(is_deleted=True)

            logger.info(f"user/views.py/HistoriesView - Delete Scenario: {scenario_id}")
            return Response({'message': '삭제 되었습니다.'},
                            status=status.HTTP_200_OK)

        logger.error(f"user/views.py/HistoriesView - error: scenario_id is required for deletion")
        return Response({'error': 'scenario_id is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)


class ScenariosView(APIView):



    @swagger_auto_schema(
        operation_id="시나리오 불러오기",
        operation_description="{scenario_id}로 시나리오 불러오기",
        responses={
            200: openapi.Response(
                description="Scenario details retrieved successfully",
            ),
            404: openapi.Response(description="Scenario not found")
        }
    )

    def get(self, request, scenario_id):
        try:
            scenario = Scenario.objects.get(id=scenario_id)
            suspects = Suspect.objects.filter(scenario_id=scenario_id)
            evidences = Evidence.objects.filter(scenario_id=scenario_id)

            scenario_data = ScenarioSerializer(scenario).data
            suspects_data = SuspectSerializer(suspects, many=True).data
            evidences_data = EvidenceSerializer(evidences, many=True).data

            # Add init_chat for each suspect
            for suspect_data, suspect in zip(suspects_data, suspects):
                chat = Chat.objects.filter(suspect_id=suspect.id).first()
                suspect_data['init_chat'] = chat.init_chat if chat else ''

            response_data = {
                'scenarios': [scenario_data],
                'suspects': suspects_data,
                'evidences': evidences_data
            }

            logger.info(f"user/views.py/ScenariosView - 200_OK : {response_data}")
            return Response(response_data, status=status.HTTP_200_OK)

        except Scenario.DoesNotExist:
            logger.error(f"user/views.py/HistoriesView - error: Scenario not found")
            return Response({"error": "Scenario not found"}, status=status.HTTP_404_NOT_FOUND)



    @swagger_auto_schema(
        operation_id="추리 노트 작성하기",
        operation_description="{scenario_id}로 추리노트 작성하기\n"
                              "추리노트의 추가된 부분만 전송하지 말고, 추리노트 전문을 전송할 것.\n",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'note': openapi.Schema(type=openapi.TYPE_STRING, description='Note to update')
            },
            required=['note']
        ),
        responses={
            200: openapi.Response(
                description="Scenario note updated successfully",
                examples={
                    "application/json":
                        {
                            "note": "Updated note"
                        }
                }
            ),
            404: openapi.Response(description="Scenario not found")
        }
    )

    def put(self, request, scenario_id):
        try:
            scenario = Scenario.objects.get(id=scenario_id)
        except Scenario.DoesNotExist:
            logger.error(f"user/views.py/HistoriesView - error: Scenario not found")
            return Response({"error": "Scenario not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update the note field with the provided note from the request
        scenario.note = request.data.get('note', scenario.note)
        scenario.updated_at = now()
        scenario.save()

        logger.info(f"user/views.py/ScenariosView - note : {scenario.note}")
        return Response({"note": scenario.note}, status=status.HTTP_200_OK)