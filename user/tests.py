from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import User


class UserAuthTestCase(APITestCase):

    def setUp(self):
        # 테스트용 사용자 데이터
        self.registration_url = reverse('user-register')
        self.login_url = reverse('user-login')
        self.user_data = {
            "name": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword",
            "password_check": "testpassword"
        }
        self.login_data = {
            "email": "testuser@example.com",
            "password": "testpassword"
        }

    def test_user_registration(self):
        # 회원가입 POST 요청
        response = self.client.post(self.registration_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # DB에 사용자 정보가 저장되었는지 확인
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.name, self.user_data['name'])
        self.assertEqual(user.email, self.user_data['email'])

    def test_user_registration_invalid(self):
        # 비밀번호 불일치로 회원가입 실패 시나리오
        invalid_data = self.user_data.copy()
        invalid_data['password_check'] = 'differentpassword'

        response = self.client.post(self.registration_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        # 회원가입 후 로그인 요청
        self.client.post(self.registration_url, self.user_data, format='json')  # 사용자 생성

        # 로그인 POST 요청
        response = self.client.post(self.login_url, self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 로그인된 사용자 정보가 제대로 반환되는지 확인
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(response.data['id'], user.id)
        self.assertEqual(response.data['name'], user.name)
        self.assertEqual(response.data['email'], user.email)

    def test_login_invalid(self):
        # 회원가입되지 않은 이메일로 로그인 시도
        invalid_login_data = {
            "email": "nonexistentuser@example.com",
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, invalid_login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Error', response.data)

