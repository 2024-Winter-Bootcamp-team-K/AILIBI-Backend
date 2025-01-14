from rest_framework import serializers
from .models import Suspect

class SuspectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suspect
        fields = ('name', 'gender', 'age', 'job', 'image')
