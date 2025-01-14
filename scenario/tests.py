from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from scenario.models import Scenario
from user.models import User
from chat.models import Chat
from suspect.models import Suspect
from evidence.models import Evidence


class ScenarioTestCase(APITestCase):

    def setUp(self):
        # 테스트용 데이터 설정
        self.user = User.objects.create(name="Test User", email="testuser@example.com", password="password")
        self.scenario = Scenario.objects.create(user=self.user, name="Test Scenario", location="Test location", type="Test type", datetime="Test datetime", description="Test description", image="Test image", level=1, note="Initial note", user_id=self.user.id)
        self.suspect = Suspect.objects.create(scenario=self.scenario, name="Test Suspect", gender=False, age=25, job="Test job", description="Test description", is_theif=False, image="Test image", scenario_id=self.scenario.id, init_chat="Test init_chat")
        self.evidence = Evidence.objects.create(scenario=self.scenario, name="Test Evidence", description="Test description", image="Test image", scenario_id=self.scenario.id)
        self.chat = Chat.objects.create(suspect=self.suspect, user_chat="Test User chat", suspect_chat="Test Suspect chat", suspect_id=self.suspect.id)

        # API 엔드포인트 URL 설정
        self.histories_url = reverse('histories')  # URL 이름을 실제 프로젝트에 맞게 수정
        self.scenario_url = reverse('scenarios', args=[self.scenario.id])  # URL 이름을 실제 프로젝트에 맞게 수정

    def test_get_histories_by_user_id(self):
        # user_id를 기준으로 플레이 기록 조회
        response = self.client.get(self.histories_url, {'user_id': self.user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('scenarios', response.data)

    def test_get_histories_by_scenario_id(self):
        # scenario_id를 기준으로 플레이 기록 조회
        response = self.client.get(self.histories_url, {'scenario_id': self.scenario.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('scenarios', response.data)
        self.assertIn('suspects', response.data)
        self.assertIn('evidences', response.data)

    def test_get_histories_by_suspect_id(self):
        # suspect_id를 기준으로 용의자와 심문 내용 조회
        response = self.client.get(self.histories_url, {'suspect_id': self.suspect.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user_chat', response.data)
        self.assertIn('suspect_chat', response.data)

    def test_get_histories_invalid_request(self):
        # 잘못된 요청에 대해 400 응답을 확인
        response = self.client.get(self.histories_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    """
    def test_delete_scenario(self):
        # 시나리오 삭제 테스트
        response = self.client.delete(self.histories_url, {'scenario_id': self.scenario.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DB에서 해당 시나리오와 관련된 항목들이 삭제되었는지 확인
        self.scenario.refresh_from_db()
        self.assertTrue(self.scenario.is_deleted)
    
    def test_delete_scenario_invalid(self):
        # scenario_id가 없는 경우
        response = self.client.delete(self.histories_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    """
    def test_get_scenario_detail(self):
        # 시나리오 상세 조회 테스트
        response = self.client.get(self.scenario_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('scenarios', response.data)
        self.assertIn('suspects', response.data)
        self.assertIn('evidences', response.data)

    def test_update_scenario_note(self):
        # 추리 노트 업데이트 테스트
        update_data = {'note': 'Updated note'}
        response = self.client.put(self.scenario_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.scenario.refresh_from_db()
        self.assertEqual(self.scenario.note, 'Updated note')

    def test_update_scenario_note_not_found(self):
        # 존재하지 않는 시나리오에 대한 업데이트 시나리오
        invalid_scenario_url = reverse('scenarios', args=[9999])  # 존재하지 않는 ID
        update_data = {'note': 'Updated note'}
        response = self.client.put(invalid_scenario_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)