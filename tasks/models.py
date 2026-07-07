from django.db import models
from django.conf import settings


class Semaine(models.Model):
    numero = models.PositiveIntegerField()
    annee = models.PositiveIntegerField()
    date_debut = models.DateField()
    date_fin = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['numero', 'annee']
        ordering = ['-annee', '-numero']

    def __str__(self):
        return f"Semaine {self.numero} - {self.annee}"


class Tache(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('not_done', 'Non effectuée'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('urgent', 'Urgente'),
    ]

    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    semaine = models.ForeignKey(
        Semaine, on_delete=models.CASCADE, related_name='taches'
    )
    assigne_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='taches_assignees',
        limit_choices_to={'role': 'agent'}
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    priorite = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default='medium'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_debut_prevue = models.DateTimeField(blank=True, null=True)
    date_fin_prevue = models.DateTimeField(blank=True, null=True)
    date_realisation = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='taches_creees'
    )

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.titre} - {self.get_status_display()}"


class SousTache(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('not_done', 'Non effectuée'),
    ]

    tache = models.ForeignKey(
        Tache, on_delete=models.CASCADE, related_name='sous_taches'
    )
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    ordre = models.PositiveIntegerField(default=0)
    date_realisation = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['ordre', 'id']

    def __str__(self):
        return f"{self.titre} ({self.tache.titre})"
