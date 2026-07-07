import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User, AgentProfile
from tasks.models import Semaine, Tache, SousTache
from reports.models import RapportExecution


class Command(BaseCommand):
    help = 'Génère des données de test complètes'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('>> Generation des donnees de test...'))

        # Créer les utilisateurs
        self.create_users()

        # Créer les semaines
        self.create_semaines()

        # Créer les tâches et sous-tâches
        self.create_tasks()

        # Créer les rapports
        self.create_reports()

        self.stdout.write(self.style.SUCCESS('OK Donnees de test creees avec succes!'))
        self.print_summary()

    def create_users(self):
        self.stdout.write('>> Creation des utilisateurs...')

        # Admin
        self.admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@seeg.ga',
                'first_name': 'Administrateur',
                'last_name': 'SEEG',
                'role': 'admin',
                'phone': '+241 01 12 34 56',
                'is_active_agent': True
            }
        )
        self.admin.set_password('admin123')
        self.admin.save()

        # Manager
        self.manager, _ = User.objects.get_or_create(
            username='manager1',
            defaults={
                'email': 'manager@seeg.ga',
                'first_name': 'Pierre',
                'last_name': 'Moussavou',
                'role': 'manager',
                'phone': '+241 02 23 45 67',
                'is_active_agent': True
            }
        )
        self.manager.set_password('manager123')
        self.manager.save()

        # Agents
        agents_data = [
            {'username': 'agent1', 'first_name': 'Jean', 'last_name': 'Dupont',
             'phone': '+241 06 12 34 56', 'matricule': 'AG001', 'zone': 'Libreville Nord'},
            {'username': 'agent2', 'first_name': 'Marie', 'last_name': 'Essono',
             'phone': '+241 06 23 45 67', 'matricule': 'AG002', 'zone': 'Libreville Centre'},
            {'username': 'agent3', 'first_name': 'Paul', 'last_name': 'Nkoghe',
             'phone': '+241 06 34 56 78', 'matricule': 'AG003', 'zone': 'Libreville Sud'},
            {'username': 'agent4', 'first_name': 'Sophie', 'last_name': 'Obame',
             'phone': '+241 06 45 67 89', 'matricule': 'AG004', 'zone': 'Akanda'},
            {'username': 'agent5', 'first_name': 'François', 'last_name': 'Mba',
             'phone': '+241 06 56 78 90', 'matricule': 'AG005', 'zone': 'Owendo'},
        ]

        self.agents = []
        for data in agents_data:
            agent, _ = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': f"{data['username']}@seeg.ga",
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': 'agent',
                    'phone': data['phone'],
                    'is_active_agent': True
                }
            )
            agent.set_password(f"{data['username']}123")
            agent.save()

            # Créer le profil agent
            AgentProfile.objects.get_or_create(
                user=agent,
                defaults={
                    'matricule': data['matricule'],
                    'zone_intervention': data['zone'],
                    'date_embauche': timezone.now().date() - timedelta(days=random.randint(365, 1825))
                }
            )
            self.agents.append(agent)

        self.stdout.write(f'   OK {len(self.agents)} agents crees')

    def create_semaines(self):
        self.stdout.write('>> Creation des semaines...')

        self.semaines = []
        current_date = timezone.now().date()

        # Créer 8 semaines (4 passées, 4 futures)
        for i in range(-4, 4):
            week_start = current_date + timedelta(weeks=i, days=-current_date.weekday())
            week_end = week_start + timedelta(days=6)

            semaine, _ = Semaine.objects.get_or_create(
                numero=week_start.isocalendar()[1],
                annee=week_start.year,
                defaults={
                    'date_debut': week_start,
                    'date_fin': week_end,
                    'is_active': i == 0  # Semaine courante active
                }
            )
            self.semaines.append(semaine)

        self.stdout.write(f'   OK {len(self.semaines)} semaines creees')

    def create_tasks(self):
        self.stdout.write('>> Creation des taches et sous-taches...')

        taches_types = [
            ('Réparation compteur', 'Remplacer compteur défectueux', 'high'),
            ('Installation compteur', 'Nouvelle installation client', 'medium'),
            ('Maintenance préventive', 'Vérification périodique', 'low'),
            ('Relevé index', 'Relevé mensuel des compteurs', 'medium'),
            ('Réclamation client', 'Traiter plainte client', 'urgent'),
            ('Déplacement commercial', 'Visite client potentiel', 'low'),
            ('Contrôle fraude', 'Inspection suspicion fraude', 'high'),
            ('Branchement électrique', 'Nouveau raccordement', 'medium'),
        ]

        status_choices = ['pending', 'in_progress', 'completed', 'not_done']
        status_weights = [0.2, 0.2, 0.5, 0.1]  # 50% completed, 10% not_done

        self.taches = []
        for semaine in self.semaines:
            # 15-25 tâches par semaine
            nb_taches = random.randint(15, 25)

            for i in range(nb_taches):
                tache_type = random.choice(taches_types)
                agent = random.choice(self.agents)

                # Date aléatoire dans la semaine
                day_offset = random.randint(0, 6)
                date_debut = datetime.combine(
                    semaine.date_debut + timedelta(days=day_offset),
                    datetime.min.time()
                ) + timedelta(hours=random.randint(7, 16))

                status = random.choices(status_choices, weights=status_weights)[0]

                # Date réalisation si terminée
                date_realisation = None
                if status == 'completed':
                    date_realisation = date_debut + timedelta(hours=random.randint(1, 4))

                tache = Tache.objects.create(
                    titre=f"{tache_type[0]} #{semaine.numero}-{i+1}",
                    description=tache_type[1],
                    semaine=semaine,
                    assigne_a=agent,
                    status=status,
                    priorite=tache_type[2],
                    date_creation=timezone.now() - timedelta(days=random.randint(1, 30)),
                    date_debut_prevue=date_debut,
                    date_fin_prevue=date_debut + timedelta(hours=4),
                    date_realisation=date_realisation,
                    created_by=random.choice([self.admin, self.manager])
                )
                self.taches.append(tache)

                # Créer 0-3 sous-tâches par tâche
                nb_soustaches = random.randint(0, 3)
                for j in range(nb_soustaches):
                    soustache_status = random.choice(status_choices)
                    date_st = None
                    if soustache_status == 'completed':
                        date_st = date_debut + timedelta(hours=j+1)

                    SousTache.objects.create(
                        tache=tache,
                        titre=f"Sous-tâche {j+1}: {tache_type[0]}",
                        description=f"Étape {j+1} de la procédure",
                        status=soustache_status,
                        ordre=j+1,
                        date_realisation=date_st
                    )

        self.stdout.write(f'   OK {len(self.taches)} taches creees')

    def create_reports(self):
        self.stdout.write('>> Creation des rapports d execution...')

        rapports_count = 0
        for tache in self.taches:
            if tache.status in ['completed', 'not_done']:
                # Coordonnées aléatoires autour de Libreville
                latitude = Decimal(str(random.uniform(0.30, 0.55)))
                longitude = Decimal(str(random.uniform(9.30, 9.70)))

                type_rapport = 'completion' if tache.status == 'completed' else 'non_execution'

                # Si non exécutée, ajouter une raison
                raison = None
                categorie = None
                if type_rapport == 'non_execution':
                    categories = ['absence', 'indisponibilite', 'materiel', 'meteo', 'autre']
                    raisons = {
                        'absence': 'Client absent malgré rendez-vous',
                        'indisponibilite': 'Accès impossible au compteur',
                        'materiel': 'Matériel manquant',
                        'meteo': 'Pluie torrentielle',
                        'autre': 'Autre raison'
                    }
                    categorie = random.choice(categories)
                    raison = raisons[categorie]

                RapportExecution.objects.create(
                    tache=tache,
                    agent=tache.assigne_a,
                    type_rapport=type_rapport,
                    commentaire='Tâche traitée' if type_rapport == 'completion' else raison,
                    raison_non_execution=raison,
                    categorie_raison=categorie,
                    date_soumission=tache.date_realisation or timezone.now(),
                    latitude=latitude,
                    longitude=longitude
                )
                rapports_count += 1

        self.stdout.write(f'   OK {rapports_count} rapports crees')

    def print_summary(self):
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('RESUME DES DONNEES'))
        self.stdout.write('='*50)
        self.stdout.write(f"Utilisateurs: {User.objects.count()}")
        self.stdout.write(f"   - Admins: {User.objects.filter(role='admin').count()}")
        self.stdout.write(f"   - Managers: {User.objects.filter(role='manager').count()}")
        self.stdout.write(f"   - Agents: {User.objects.filter(role='agent').count()}")
        self.stdout.write(f"Semaines: {Semaine.objects.count()}")
        self.stdout.write(f"Taches: {Tache.objects.count()}")
        self.stdout.write(f"   - En attente: {Tache.objects.filter(status='pending').count()}")
        self.stdout.write(f"   - En cours: {Tache.objects.filter(status='in_progress').count()}")
        self.stdout.write(f"   - Terminées: {Tache.objects.filter(status='completed').count()}")
        self.stdout.write(f"   - Non effectuées: {Tache.objects.filter(status='not_done').count()}")
        self.stdout.write(f"Sous-taches: {SousTache.objects.count()}")
        self.stdout.write(f"Rapports: {RapportExecution.objects.count()}")
        self.stdout.write('='*50)
        self.stdout.write('\nIdentifiants de test:')
        self.stdout.write('   admin / admin123')
        self.stdout.write('   manager1 / manager123')
        self.stdout.write('   agent1-5 / agentX123 (ex: agent1 / agent1123)')
