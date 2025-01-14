from rest_framework import serializers

from scenario.models import Scenario
from suspect.models import Suspect
from evidence.models import Evidence

class His_ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ['id', 'name', 'image', 'level', 'type', 'is_success']

class His_SuspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suspect
        fields = ['id', 'name', 'gender', 'age', 'job', 'description', 'is_theif', 'image', 'init_chat']

class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ['name', 'location', 'datetime', 'type', 'description', 'image', 'level', 'note', 'is_success', 'count']

class SuspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suspect
        fields = ['name', 'gender', 'age', 'job', 'description', 'image']

class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ['name', 'description', 'image']

"""
class SuspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suspect
        fields = ['name', 'description', 'age']
"""