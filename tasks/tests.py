from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import Semaine, Tache, SousTache

User = get_user_model()


class SemaineModelTest(TestCase):
    """Tests pour le modèle Semaine"""

    def setUp(self):
        self.semaine = Semaine.objects.create(
            numero=15,
            annee=2025,
            date_debut='2025-04-07',
            date_fin='2025-04-13',
            is_active=True
        )

    def test_semaine_creation(self):
        self.assertEqual(self.semaine.numero, 15)
        self.assertEqual(self.semaine.annee, 2025)
        self.assertTrue(self.semaine.is_active)

    def test_semaine_str(self):
        self.assertEqual(str(self.semaine), "Semaine 15 - 2025")

    def test_unique_together(self):
        # Tentative de créer une semaine dupliquée
        with self.assertRaises(Exception):
            Semaine.objects.create(
                numero=15,
                annee=2025,
                date_debut='2025-04-14',
                date_fin='2025-04-20'
            )


class TacheModelTest(TestCase):
    """Tests pour le modèle Tache"""

    def setUp(self):
        self.semaine = Semaine.objects.create(
            numero=15,
            annee=2025,
            date_debut='2025-04-07',
            date_fin='2025-04-13'
        )
        self.agent = User.objects.create_user(
            username='agenttest',
            password='test123',
            role='agent'
        )
        self.tache = Tache.objects.create(
            titre='Test Tache',
            description='Description test',
            semaine=self.semaine,
            assigne_a=self.agent,
            status='pending',
            priorite='high',
            created_by=self.agent
        )

    def test_tache_creation(self):
        self.assertEqual(self.tache.titre, 'Test Tache')
        self.assertEqual(self.tache.status, 'pending')
        self.assertEqual(self.tache.priorite, 'high')
        self.assertEqual(self.tache.assigne_a, self.agent)

    def test_tache_str(self):
        self.assertEqual(
            str(self.tache),
            "Test Tache - En attente"
        )

    def test_default_status(self):
        tache = Tache.objects.create(
            titre='Default Tache',
            semaine=self.semaine,
            assigne_a=self.agent,
            created_by=self.agent
        )
        self.assertEqual(tache.status, 'pending')
        self.assertEqual(tache.priorite, 'medium')


class SousTacheModelTest(TestCase):
    """Tests pour le modèle SousTache"""

    def setUp(self):
        self.semaine = Semaine.objects.create(
            numero=15,
            annee=2025,
            date_debut='2025-04-07',
            date_fin='2025-04-13'
        )
        self.agent = User.objects.create_user(
            username='agenttest',
            password='test123',
            role='agent'
        )
        self.tache = Tache.objects.create(
            titre='Tache Parent',
            semaine=self.semaine,
            assigne_a=self.agent,
            created_by=self.agent
        )
        self.soustache = SousTache.objects.create(
            tache=self.tache,
            titre='Sous-tache 1',
            description='Description',
            status='pending',
            ordre=1
        )

    def test_soustache_creation(self):
        self.assertEqual(self.soustache.titre, 'Sous-tache 1')
        self.assertEqual(self.soustache.tache, self.tache)
        self.assertEqual(self.soustache.ordre, 1)

    def test_soustache_str(self):
        self.assertEqual(
            str(self.soustache),
            "Sous-tache 1 (Tache Parent)"
        )


class SemaineAPITest(APITestCase):
    """Tests pour l'API Semaine"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            role='agent'
        )
        self.semaine = Semaine.objects.create(
            numero=15,
            annee=2025,
            date_debut='2025-04-07',
            date_fin='2025-04-13'
        )
        self.semaine_list_url = reverse('semaine_list')
        self.semaine_detail_url = reverse(
            'semaine_detail',
            kwargs={'pk': self.semaine.pk}
        )

    def test_list_semaines_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.semaine_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_semaines_unauthenticated(self):
        response = self.client.get(self.semaine_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_semaine(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'numero': 16,
            'annee': 2025,
            'date_debut': '2025-04-14',
            'date_fin': '2025-04-20',
            'is_active': True
        }
        response = self.client.post(
            self.semaine_list_url,
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Semaine.objects.count(), 2)


class TacheAPITest(APITestCase):
    """Tests pour l'API Tache"""

    def setUp(self):
        self.client = APIClient()
        self.agent = User.objects.create_user(
            username='agent1',
            password='agent123',
            role='agent'
        )
        self.admin = User.objects.create_user(
            username='admin1',
            password='admin123',
            role='admin'
        )
        self.semaine = Semaine.objects.create(
            numero=15,
            annee=2025,
            date_debut='2025-04-07',
            date_fin='2025-04-13'
        )
        self.tache = Tache.objects.create(
            titre='Tache test',
            description='Description',
            semaine=self.semaine,
            assigne_a=self.agent,
            status='pending',
            created_by=self.admin
        )
        self.tache_list_url = reverse('tache_list')
        self.mes_taches_url = reverse('mes_taches')

    def test_list_taches(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get(self.tache_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_agent_see_only_his_tasks(self):
        # Créer une tâche pour un autre agent
        other_agent = User.objects.create_user(
            username='agent2',
            password='agent123',
            role='agent'
        )
        Tache.objects.create(
            titre='Tache autre agent',
            semaine=self.semaine,
            assigne_a=other_agent,
            created_by=self.admin
        )

        self.client.force_authenticate(user=self.agent)
        response = self.client.get(self.tache_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # L'agent ne voit que sa tâche
        self.assertEqual(response.data['count'], 1)

    def test_mes_taches_endpoint(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get(self.mes_taches_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['titre'], 'Tache test')

    def test_create_tache(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            'titre': 'Nouvelle tache',
            'description': 'Nouvelle description',
            'semaine': self.semaine.pk,
            'assigne_a': self.agent.pk,
            'status': 'pending',
            'priorite': 'high'
        }
        response = self.client.post(
            self.tache_list_url,
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tache.objects.count(), 2)

    def test_filter_by_status(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get(f"{self.tache_list_url}?status=pending")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)


class SousTacheAPITest(APITestCase):
    """Tests pour l'API SousTache"""

    def setUp(self):
        self.client = APIClient()
        self.agent = User.objects.create_user(
            username='agent1',
            password='agent123',
            role='agent'
        )
        self.semaine = Semaine.objects.create(
            numero=15,
            annee=2025,
            date_debut='2025-04-07',
            date_fin='2025-04-13'
        )
        self.tache = Tache.objects.create(
            titre='Tache test',
            semaine=self.semaine,
            assigne_a=self.agent,
            created_by=self.agent
        )
        self.soustache = SousTache.objects.create(
            tache=self.tache,
            titre='Sous-tache test',
            status='pending',
            ordre=1
        )
        self.soustache_list_url = reverse(
            'sous_tache_list',
            kwargs={'tache_id': self.tache.pk}
        )

    def test_list_soustaches(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get(self.soustache_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_soustache(self):
        self.client.force_authenticate(user=self.agent)
        data = {
            'titre': 'Nouvelle sous-tache',
            'description': 'Description',
            'status': 'pending',
            'ordre': 2
        }
        response = self.client.post(
            self.soustache_list_url,
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SousTache.objects.count(), 2)

