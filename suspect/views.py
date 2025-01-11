from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Suspect
from chat.models import Chat
from .serializers import SuspectSerializer


class SuspectsView(APIView):
    def get(self, request):
        scenario_id = request.GET.get('scenario_id')
        if not scenario_id:
            return Response({"error": "scenario_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        suspects = Suspect.objects.filter(scenario_id=scenario_id)
        suspect_data = []

        for suspect in suspects:
            chat = Chat.objects.filter(suspect_id=suspect.id).first()
            data = SuspectSerializer(suspect).data
            data['init_chat'] = chat.init_chat if chat else ""
            suspect_data.append(data)

        return Response({"suspects": suspect_data}, status=status.HTTP_200_OK)

    def put(self, request):
        choose_theif = request.data.get("choose_theif")

        if not choose_theif:
            return Response({"error": "choose_theif is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Suspect 객체 조회
        suspect = Suspect.objects.filter(name=choose_theif).first()
        if not suspect:
            return Response({"error": "Suspect not found"}, status=status.HTTP_404_NOT_FOUND)

        # 'is_theif' 값을 DB에서 확인
        is_theif_value = suspect.is_theif

        # 응답: 'is_theif' 값에 따라 응답 반환
        return Response({"is_theif": is_theif_value}, status=status.HTTP_201_CREATED)


class SuspectDetailView(APIView):
    def get(self, request, suspect_id):
        try:
            suspect = Suspect.objects.get(id=suspect_id)
            init_chat = Chat.objects.get(suspect_id=suspect_id).init_chat
            suspect_data = SuspectSerializer(suspect).data
            suspect_data["init_chat"] = init_chat
            return Response(suspect_data, status=status.HTTP_200_OK)
        except Suspect.DoesNotExist:
            return Response({"error": "Suspect not found"}, status=status.HTTP_404_NOT_FOUND)
        except Chat.DoesNotExist:
            return Response({"error": "Chat not found"}, status=status.HTTP_404_NOT_FOUND)


class SuspectsChooseView(APIView):
    def get(self, request):
        # URL의 쿼리 파라미터에서 suspect_id를 받아옵니다.
        suspect_id = request.GET.get('suspect_id')

        if not suspect_id:
            return Response({"error": "suspect_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # suspect_id로 Suspect를 조회
            suspect = Suspect.objects.get(id=suspect_id)

            # Suspect의 is_theif 값을 가져옵니다.
            is_theif_value = suspect.is_theif

            # 성공적으로 가져온 값으로 응답을 반환합니다.
            return Response({"is_theif": is_theif_value}, status=status.HTTP_200_OK)

        except Suspect.DoesNotExist:
            return Response({"error": "Suspect not found"}, status=status.HTTP_404_NOT_FOUND)