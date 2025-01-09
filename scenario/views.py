from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import User, Scenario
from .serializers import ScenarioSerializer, SelectedScenarioSerializer #, SuspectSerializer

class HistoriesView(APIView):
    def get(self, request):
        user_id = request.query_params.get('user_id')           #모든 플레이 기록 불러오기
        scenario_id = request.query_params.get('scenario_id')   #선택한 플레이 기록 불러오기
        #suspect_id = request.query_params.get('suspect_id')     #선택한 용의자와 심문 내용 불러오기

        if user_id:
            user = get_object_or_404(User, id=user_id)
            scenarios = Scenario.objects.filter(user_id=user.id)
            serializer = ScenarioSerializer(scenarios, many=True)
            return Response({"scenarios": serializer.data}, status=status.HTTP_200_OK)

        elif scenario_id:
            scenario = get_object_or_404(Scenario, id=scenario_id)
            serializer = SelectedScenarioSerializer(scenario)
            return Response({"scenarios" : serializer.data}, status=status.HTTP_200_OK)


        #elif suspect_id:
        #    suspect = get_object_or_404(Suspect, id=suspect_id)
        #    serializer = SuspectSerializer(suspect)
        #    return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({'error': '잘못된 요청'}, status=status.HTTP_400_BAD_REQUEST)