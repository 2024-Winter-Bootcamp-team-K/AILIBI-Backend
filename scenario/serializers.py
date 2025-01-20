from rest_framework import serializers

from scenario.models import Scenario
from suspect.models import Suspect
from evidence.models import Evidence

class His_ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ['id', 'name', 'location', 'type', 'datetime', 'image', 'level', 'note', 'is_success']

class His_SuspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suspect
        fields = ['id', 'name', 'gender', 'age', 'job', 'description', 'is_theif', 'image', 'init_chat']

"""
class His_EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ["id", "name", "description", "image"]
"""

class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ['name', 'location', 'datetime', 'type', 'description', 'image', 'level', 'note', 'is_success', 'count']

class SuspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suspect
        fields = ['name', 'gender', 'age', 'job', 'description', 'image', 'init_chat']

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