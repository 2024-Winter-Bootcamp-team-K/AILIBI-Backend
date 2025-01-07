from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=16)
    password_check = serializers.CharField(write_only=True, max_length=16)

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'password_check']

    def validate(self, data):
        if data['password'] != data['password_check']:
            raise serializers.ValidationError({"password_check": "비밀번호가 일치하지 않습니다."})
        return data

    def create(self, validated_data):
        validated_data.pop('password_check')
        return User.objects.create(**validated_data)
