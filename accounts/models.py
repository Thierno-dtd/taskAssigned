from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('agent', 'Agent terrain'),
        ('manager', 'Manager'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='agent')
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active_agent = models.BooleanField(default=True)
    must_change_password = models.BooleanField(
        default=False,
        help_text=(
            "True tant que l'utilisateur n'a pas changé le mot de passe "
            "temporaire généré à la création de son compte. Forcé à True "
            "explicitement uniquement dans RegisterView/ManagerCreateView/"
            "import Excel (comptes créés avec un mot de passe généré) — "
            "les comptes créés autrement (createsuperuser, seed_data, "
            "admin Django) restent à False, considérés déjà onboardés."
        )
    )
    phone_verifie = models.BooleanField(
        default=True,
        help_text=(
            "False uniquement pour les comptes créés avec un mot de passe "
            "temporaire (RegisterView/ManagerCreateView/import Excel), qui "
            "doivent vérifier leur téléphone à la première connexion. "
            "True par défaut pour tous les autres comptes (déjà onboardés)."
        )
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_agent(self):
        return self.role == 'agent'

    @property
    def is_manager(self):
        return self.role == 'manager'


class AgentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    matricule = models.CharField(max_length=50, unique=True)
    zone_intervention = models.CharField(max_length=100, blank=True, null=True)
    date_embauche = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return f"Profil Agent: {self.user.get_full_name()} - {self.matricule}"