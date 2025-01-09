from rest_framework import serializers
from .models import Scenario
#Suspect

class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ['id', 'name', 'image', 'level', 'type', 'is_success']

class SelectedScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ['name', 'location', 'datetime', 'type', 'description', 'image', 'level', 'note', 'is_success', 'count']

"""
class SuspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suspect
        fields = ['name', 'description', 'age']
"""