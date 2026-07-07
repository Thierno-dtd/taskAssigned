from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import User, AgentProfile


class UserModelTest(TestCase):
    """Tests pour le modèle User"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='agent',
            phone='+241 06 12 34 56'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.role, 'agent')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_str(self):
        expected = f"{self.user.get_full_name()} (Agent terrain)"
        self.assertEqual(str(self.user), expected)

    def test_is_admin_property(self):
        self.assertFalse(self.user.is_admin)
        self.user.role = 'admin'
        self.user.save()
        self.assertTrue(self.user.is_admin)

    def test_is_agent_property(self):
        self.assertTrue(self.user.is_agent)
        self.user.role = 'manager'
        self.user.save()
        self.assertFalse(self.user.is_agent)


class AgentProfileModelTest(TestCase):
    """Tests pour le modèle AgentProfile"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='agentuser',
            password='testpass123',
            role='agent'
        )
        self.profile = AgentProfile.objects.create(
            user=self.user,
            matricule='AG001',
            zone_intervention='Libreville Nord',
            date_embauche='2020-01-15'
        )

    def test_profile_creation(self):
        self.assertEqual(self.profile.matricule, 'AG001')
        self.assertEqual(self.profile.user, self.user)

    def test_profile_str(self):
        expected = f"Profil Agent: {self.user.get_full_name()} - AG001"
        self.assertEqual(str(self.profile), expected)


class AuthenticationAPITest(APITestCase):
    """Tests pour l'API d'authentification"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='apipass123',
            role='agent'
        )
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.profile_url = reverse('profile')

    def test_user_registration(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'agent'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'newuser')

    def test_user_login(self):
        data = {
            'username': 'apiuser',
            'password': 'apipass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_user_login_invalid(self):
        data = {
            'username': 'apiuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_access_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'apiuser')

    def test_profile_access_unauthenticated(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_update(self):
        self.client.force_authenticate(user=self.user)
        data = {'first_name': 'Updated', 'phone': '+241 07 77 77 77'}
        response = self.client.put(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.phone, '+241 07 77 77 77')


class AgentListAPITest(APITestCase):
    """Tests pour la liste des agents"""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='adminuser',
            password='admin123',
            role='admin'
        )
        self.agent1 = User.objects.create_user(
            username='agent1',
            password='agent123',
            role='agent',
            first_name='Jean',
            last_name='Dupont'
        )
        self.agent2 = User.objects.create_user(
            username='agent2',
            password='agent123',
            role='agent',
            first_name='Marie',
            last_name='Martin'
        )
        self.agents_url = reverse('agent_list')

    def test_agent_list_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.agents_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_agent_list_as_agent(self):
        self.client.force_authenticate(user=self.agent1)
        response = self.client.get(self.agents_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_agent_list_unauthenticated(self):
        response = self.client.get(self.agents_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

