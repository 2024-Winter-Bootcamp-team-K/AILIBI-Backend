from rest_framework import serializers

from scenario.models import Scenario
from suspect.models import Suspect
from evidence.models import Evidence
#Suspect

class his_ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ['id', 'name', 'image', 'level', 'type', 'is_success']

class his_SelectedScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ['name', 'location', 'datetime', 'type', 'description', 'image', 'level', 'note', 'is_success', 'count']

class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ['name', 'location', 'datetime', 'type', 'description', 'image', 'level', 'note', 'is_success', 'count']

class SuspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suspect
        fields = ['name', 'gender', 'age', 'job', 'personality', 'image']

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