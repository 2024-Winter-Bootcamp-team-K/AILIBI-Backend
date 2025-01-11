from rest_framework import serializers
from .models import Evidence

class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ['id', 'name', 'description', 'image']

class EvidenceChooseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ['name', 'description', 'image']