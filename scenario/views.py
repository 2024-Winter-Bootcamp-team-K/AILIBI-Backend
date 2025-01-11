from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from .models import User
from scenario.models import Scenario
from chat.models import Chat
from suspect.models import Suspect
from evidence.models import Evidence

from .serializers import His_ScenarioSerializer, His_SuspectSerializer, ScenarioSerializer, SuspectSerializer, EvidenceSerializer

class HistoriesView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')           #모든 플레이 기록 불러오기
        scenario_id = request.query_params.get('scenario_id')   #선택한 플레이 기록 불러오기
        suspect_id = request.query_params.get('suspect_id')     # 선택한 용의자와 심문 내용 불러오기

        if user_id:
            user = get_object_or_404(User, id=user_id)
            scenarios = Scenario.objects.filter(user_id=user.id)
            serializer = His_ScenarioSerializer(scenarios, many=True)
            return Response({"scenarios": serializer.data}, status=status.HTTP_200_OK)

        elif scenario_id:

            # Scenario 정보 가져오기
            scenario = Scenario.objects.filter(id=scenario_id).first()

            if not scenario:
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

            return Response(response_data, status=status.HTTP_200_OK)

        else:
            return Response({'error': '잘못된 요청'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        scenario_id = request.query_params.get('scenario_id')

        if scenario_id:
            suspect_ids = Suspect.objects.filter(scenario_id=scenario_id).values_list('id', flat=True)

            Scenario.objects.filter(id=scenario_id).delete()
            Evidence.objects.filter(scenario_id=scenario_id).delete()
            Suspect.objects.filter(scenario_id=scenario_id).delete()
            Chat.objects.filter(suspect_id__in=suspect_ids).delete()

            return Response({'message': '삭제 되었습니다.'},
                            status=status.HTTP_200_OK)

        return Response({'error': 'scenario_id is required for deletion'}, status=status.HTTP_400_BAD_REQUEST)


class ScenariosView(APIView):
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

            return Response(response_data, status=status.HTTP_200_OK)

        except Scenario.DoesNotExist:
            return Response({"error": "Scenario not found"}, status=status.HTTP_404_NOT_FOUND)\


    def put(self, request, scenario_id):
        try:
            scenario = Scenario.objects.get(id=scenario_id)
        except Scenario.DoesNotExist:
            return Response({"error": "Scenario not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update the note field with the provided note from the request
        scenario.note = request.data.get('note', scenario.note)
        scenario.updated_at = now()
        scenario.save()

        return Response({"note": scenario.note}, status=status.HTTP_200_OK)