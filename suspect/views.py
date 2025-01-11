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