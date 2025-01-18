import logging
import bcrypt
from rest_framework import serializers
from .models import User

logger = logging.getLogger(__name__)

#비밀번호 해싱 및 솔트
async def hash_password(password):
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')  # DB에 저장하기 위해 문자열로 변환

#로그인 시 비밀번호 확인
async def check_password(password, hashed):
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

#회원가입
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=64)
    password_check = serializers.CharField(write_only=True, max_length=64)

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'password_check']
        extra_kwargs = {'password': {'write_only': True}}

    async def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            logger.warning(f"user/serializers.py/UserSerializer/validate_email - Email validation failed: {value} is already registered.")
            raise serializers.ValidationError("이미 가입한 이메일입니다.")
        return value

    async def validate(self, data):
        if data['password'] != data['password_check']:
            logger.warning("user/serializers.py/UserSerializer/validate - Password validation failed: passwords do not match.")
            raise serializers.ValidationError({"password_check": "비밀번호가 일치하지 않습니다."})
        return data

    async def create(self, validated_data):
        validated_data.pop('password_check', None)

        password = validated_data.pop('password')
        hashed_password = hash_password(password)
        validated_data['password'] = hashed_password

        return User.objects.create(**validated_data)

#로그인
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    async def validate(self, data):
        email = data['email']
        password = data['password']
        try:
            user = User.objects.get(email=email)
            if not check_password(password, user.password):
                logger.warning(f"user/serializers.py/LoginSerializer/validate -  Incorrect password : {email}")
                raise serializers.ValidationError("잘못된 비밀번호입니다.")
            if user.is_deleted:
                logger.warning(f"user/serializers.py/LoginSerializer/validate -  Deleted User : {email}")
                raise serializers.ValidationError("삭제된 사용자입니다.")
            return data
        except User.DoesNotExist:
            logger.warning(f"user/serializers.py/LoginSerializer/validate -  Incorrect User : {email}")
            raise serializers.ValidationError("존재하지 않는 아이디입니다.")
