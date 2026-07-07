from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
import io
import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile

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


class GpsViewsTest(APITestCase):
    """
    Tests de non-régression pour les endpoints GPS/carte.
    Ces vues n'étaient couvertes par aucun test, ce qui a permis à un bug
    critique (champs GPS absents du modèle) de passer inaperçu.
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_gps', password='pass1234', role='admin'
        )
        self.agent = User.objects.create_user(
            username='agent_gps', password='pass1234', role='agent'
        )
        self.semaine = Semaine.objects.create(
            numero=1, annee=2026,
            date_debut='2026-01-05', date_fin='2026-01-11'
        )
        self.tache = Tache.objects.create(
            titre='Tâche avec GPS',
            semaine=self.semaine,
            assigne_a=self.agent,
            created_by=self.admin,
            gps_latitude='0.416200',
            gps_longitude='9.467300',
            adresse_complet='Libreville centre'
        )
        self.tache_sans_gps = Tache.objects.create(
            titre='Tâche sans GPS',
            semaine=self.semaine,
            assigne_a=self.agent,
            created_by=self.admin,
        )

    def test_map_tasks_data(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('map_tasks'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Seule la tâche avec coordonnées doit apparaître
        self.assertEqual(response.data['statistics']['total'], 1)

    def test_update_task_location(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.post(
            reverse('update_location', kwargs={'task_id': self.tache_sans_gps.pk}),
            {'latitude': 0.39, 'longitude': 9.45, 'address': 'Akanda'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tache_sans_gps.refresh_from_db()
        self.assertIsNotNone(self.tache_sans_gps.gps_latitude)

    def test_nearby_tasks(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            reverse('nearby_tasks'),
            {'lat': 0.4162, 'lng': 9.4673, 'radius_km': 10}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_agent_tracking_forbidden_for_agent(self):
        self.client.force_authenticate(user=self.agent)
        response = self.client.get(reverse('agent_tracking'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_agent_tracking_as_admin(self):
        self.tache.date_realisation = '2026-01-06T10:00:00Z'
        self.tache.save()
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('agent_tracking'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ImportExcelDynamiqueTest(APITestCase):
    """
    Tests du flux d'import Excel en 2 temps (analyse -> confirmation)
    avec colonnes libres, mapping choisi par le superviseur, et
    filtrage des champs visibles côté agent.
    """

    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager1', password='pass1234', role='manager'
        )
        self.agent = User.objects.create_user(
            username='ag_jean', password='pass1234', role='agent',
            first_name='Jean', last_name='Ndong'
        )
        self.semaine = Semaine.objects.create(
            numero=10, annee=2026,
            date_debut='2026-03-02', date_fin='2026-03-08'
        )

    def _fichier_excel(self, rows):
        df = pd.DataFrame(rows)
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        buf.seek(0)
        return SimpleUploadedFile(
            'import.xlsx', buf.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_analyser_puis_confirmer_import(self):
        self.client.force_authenticate(user=self.manager)

        fichier = self._fichier_excel([
            {'Nom Agent': 'Jean Ndong', 'Adresse client': 'Nkembo', 'Compteur': 'CPT-01', 'Zone': 'Nord'},
        ])

        # Étape 1 : analyse
        response = self.client.post(
            reverse('import_excel_analyser'), {'file': fichier}, format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Nom Agent', response.data['colonnes'])
        import_id = response.data['import_id']

        # Étape 2 : confirmation avec mapping + colonnes visibles mobile
        payload = {
            'import_id': import_id,
            'semaine_id': self.semaine.id,
            'mapping': {'agent': 'Nom Agent'},
            'colonnes_obligatoires': ['Nom Agent', 'Adresse client'],
            'colonnes_visibles_mobile': ['Adresse client', 'Zone'],
        }
        response2 = self.client.post(
            reverse('import_excel_confirmer'), payload, format='json'
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['created'], 1)
        self.assertEqual(Tache.objects.filter(semaine=self.semaine).count(), 1)

        tache = Tache.objects.get(semaine=self.semaine)
        self.assertEqual(tache.assigne_a, self.agent)
        # Toutes les colonnes du fichier sont conservées en base
        self.assertEqual(tache.donnees_excel['Compteur'], 'CPT-01')

    def test_agent_introuvable_ne_bloque_pas_le_reste(self):
        self.client.force_authenticate(user=self.manager)
        fichier = self._fichier_excel([
            {'Nom Agent': 'Jean Ndong', 'Adresse client': 'Nkembo'},
            {'Nom Agent': 'Personne Inconnue', 'Adresse client': 'Ailleurs'},
        ])
        response = self.client.post(
            reverse('import_excel_analyser'), {'file': fichier}, format='multipart'
        )
        import_id = response.data['import_id']

        payload = {
            'import_id': import_id,
            'semaine_id': self.semaine.id,
            'mapping': {'agent': 'Nom Agent'},
            'colonnes_obligatoires': ['Nom Agent'],
            'colonnes_visibles_mobile': ['Adresse client'],
        }
        response2 = self.client.post(
            reverse('import_excel_confirmer'), payload, format='json'
        )
        self.assertEqual(response2.data['created'], 1)
        self.assertEqual(len(response2.data['errors']), 1)

    def test_colonnes_visibles_filtrees_pour_agent_mais_pas_pour_manager(self):
        self.client.force_authenticate(user=self.manager)
        fichier = self._fichier_excel([
            {'Nom Agent': 'Jean Ndong', 'Adresse client': 'Nkembo', 'Compteur': 'CPT-01'},
        ])
        response = self.client.post(
            reverse('import_excel_analyser'), {'file': fichier}, format='multipart'
        )
        import_id = response.data['import_id']
        payload = {
            'import_id': import_id,
            'semaine_id': self.semaine.id,
            'mapping': {'agent': 'Nom Agent'},
            'colonnes_obligatoires': ['Nom Agent'],
            'colonnes_visibles_mobile': ['Adresse client'],  # 'Compteur' volontairement absent
        }
        self.client.post(reverse('import_excel_confirmer'), payload, format='json')

        # Vue manager : doit voir toutes les colonnes
        response_manager = self.client.get(reverse('tache_list'))
        tache_data = response_manager.data['results'][0]
        self.assertIn('Compteur', tache_data['donnees_visibles'])

        # Vue agent : ne doit voir que 'Adresse client'
        self.client.force_authenticate(user=self.agent)
        response_agent = self.client.get(reverse('mes_taches'))
        tache_agent = response_agent.data[0]
        self.assertNotIn('Compteur', tache_agent['donnees_visibles'])
        self.assertIn('Adresse client', tache_agent['donnees_visibles'])

    def test_import_id_invalide_a_la_confirmation(self):
        self.client.force_authenticate(user=self.manager)
        payload = {
            'import_id': 'inexistant',
            'semaine_id': self.semaine.id,
            'mapping': {'agent': 'Nom Agent'},
        }
        response = self.client.post(
            reverse('import_excel_confirmer'), payload, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_agent_ne_peut_pas_importer(self):
        self.client.force_authenticate(user=self.agent)
        fichier = self._fichier_excel([{'Nom Agent': 'Jean Ndong'}])
        response = self.client.post(
            reverse('import_excel_analyser'), {'file': fichier}, format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_historique_des_imports(self):
        self.client.force_authenticate(user=self.manager)
        fichier = self._fichier_excel([{'Nom Agent': 'Jean Ndong', 'Adresse client': 'Nkembo'}])
        response = self.client.post(
            reverse('import_excel_analyser'), {'file': fichier}, format='multipart'
        )
        import_id = response.data['import_id']
        payload = {
            'import_id': import_id,
            'semaine_id': self.semaine.id,
            'mapping': {'agent': 'Nom Agent'},
            'colonnes_obligatoires': ['Nom Agent'],
            'colonnes_visibles_mobile': ['Adresse client'],
        }
        self.client.post(reverse('import_excel_confirmer'), payload, format='json')

        response_hist = self.client.get(reverse('import_lot_list'))
        self.assertEqual(response_hist.status_code, status.HTTP_200_OK)
        self.assertEqual(response_hist.data['count'], 1)
        self.assertEqual(response_hist.data['results'][0]['nombre_taches_creees'], 1)
        self.assertEqual(response_hist.data['results'][0]['taux_reussite'], 100.0)

        # Un agent ne doit pas voir l'historique des imports
        self.client.force_authenticate(user=self.agent)
        response_forbidden = self.client.get(reverse('import_lot_list'))
        self.assertEqual(response_forbidden.status_code, status.HTTP_403_FORBIDDEN)