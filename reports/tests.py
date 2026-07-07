from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal

from tasks.models import Semaine, Tache
from .models import RapportExecution

User = get_user_model()


class RapportExecutionModelTest(TestCase):
    """Tests pour le modèle RapportExecution"""

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
            titre='Tache test',
            semaine=self.semaine,
            assigne_a=self.agent,
            created_by=self.agent
        )
        self.rapport = RapportExecution.objects.create(
            tache=self.tache,
            agent=self.agent,
            type_rapport='completion',
            commentaire='Tâche effectuée avec succès',
            latitude=Decimal('0.416200'),
            longitude=Decimal('9.467300')
        )

    def test_rapport_creation(self):
        self.assertEqual(self.rapport.type_rapport, 'completion')
        self.assertEqual(self.rapport.agent, self.agent)
        self.assertEqual(self.rapport.tache, self.tache)

    def test_rapport_str(self):
        expected = f"Rapport: {self.tache} - Tâche terminée"
        self.assertEqual(str(self.rapport), expected)

    def test_non_execution_rapport(self):
        rapport = RapportExecution.objects.create(
            tache=self.tache,
            agent=self.agent,
            type_rapport='non_execution',
            raison_non_execution='Client absent',
            categorie_raison='absence'
        )
        self.assertEqual(rapport.categorie_raison, 'absence')


class RapportExecutionAPITest(APITestCase):
    """Tests pour l'API RapportExecution"""

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
            semaine=self.semaine,
            assigne_a=self.agent,
            created_by=self.admin
        )
        self.rapport = RapportExecution.objects.create(
            tache=self.tache,
            agent=self.agent,
            type_rapport='completion',
            commentaire='Test rapport'
        )
        self.rapport_list_url = reverse('rapport_list')
        self.soumettre_url = reverse('soumettre_rapport')
        self.mes_rapports_url = reverse('mes_rapports')

    def test_list_rapports_as_agent(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get(self.rapport_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Agent ne voit que ses rapports
        self.assertEqual(response.data['count'], 1)

    def test_list_rapports_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.rapport_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_soumettre_rapport_completion(self):
        self.client.force_authenticate(user=self.agent)
        data = {
            'tache': self.tache.pk,
            'type_rapport': 'completion',
            'commentaire': 'Tâche terminée',
            'latitude': '0.416200',
            'longitude': '9.467300'
        }
        response = self.client.post(
            self.soumettre_url,
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rapport', response.data)
        self.assertEqual(RapportExecution.objects.count(), 2)

    def test_soumettre_rapport_non_execution(self):
        self.client.force_authenticate(user=self.agent)
        data = {
            'tache': self.tache.pk,
            'type_rapport': 'non_execution',
            'raison_non_execution': 'Client absent',
            'categorie_raison': 'absence',
            'commentaire': 'Impossible d\'accéder'
        }
        response = self.client.post(
            self.soumettre_url,
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RapportExecution.objects.count(), 2)

    def test_soumettre_rapport_invalid(self):
        self.client.force_authenticate(user=self.agent)
        # Rapport sans tache ni sous_tache
        data = {
            'type_rapport': 'completion',
            'commentaire': 'Test'
        }
        response = self.client.post(
            self.soumettre_url,
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mes_rapports_endpoint(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get(self.mes_rapports_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_rapport_detail(self):
        self.client.force_authenticate(user=self.agent)
        detail_url = reverse(
            'rapport_detail',
            kwargs={'pk': self.rapport.pk}
        )
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tache_titre'], 'Tache test')

