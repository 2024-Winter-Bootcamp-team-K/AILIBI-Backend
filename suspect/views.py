from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from chat.models import Chat


class HistoriesView(APIView):
    def get(self, request):
        suspect_id = request.query_params.get('suspect_id')  # 선택한 용의자와 심문 내용 불러오기

        if suspect_id:
            chats = Chat.objects.filter(suspect_id=suspect_id).values('user_chat', 'suspect_chat').first()

            if not chats:
                return Response({'error': 'No chat data found for this suspect'}, status=status.HTTP_404_NOT_FOUND)

            user_chat_messages = chats['user_chat'].split('/CHANGE ')

            suspect_chat_messages = chats['suspect_chat'].split('/CHANGE ')

            response_data = {

                "user_chat": [{"message": message.strip()} for message in user_chat_messages if message.strip()],

                "suspect_chat": [{"message": message.strip()} for message in suspect_chat_messages if message.strip()]

            }

            return Response(response_data, status=status.HTTP_200_OK)

        return Response({'error': 'suspect_id is required'}, status=status.HTTP_400_BAD_REQUEST)
