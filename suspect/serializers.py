from rest_framework import serializers
from .models import Suspect

class SuspectSerializer(serializers.ModelSerializer):
    task_id = serializers.SerializerMethodField()
    class Meta:
        model = Suspect
        fields = ('id', 'name', 'gender', 'age', 'job', 'image', 'init_chat', 'task_id')

    def get_task_id(self, obj):
        # task_id를 obj에서 동적으로 가져오기
        return getattr(obj, 'task_id', None)  # task_id가 존재하지 않을 경우 None 반환
