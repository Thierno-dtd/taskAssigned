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
