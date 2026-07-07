from django.db import models
from django.conf import settings
from tasks.models import Tache, SousTache


class RapportExecution(models.Model):
    TYPE_RAPPORT_CHOICES = [
        ('completion', 'Tâche terminée'),
        ('non_execution', 'Non exécutée'),
    ]

    tache = models.ForeignKey(
        Tache, on_delete=models.CASCADE,
        related_name='rapports', blank=True, null=True
    )
    sous_tache = models.ForeignKey(
        SousTache, on_delete=models.CASCADE,
        related_name='rapports', blank=True, null=True
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='rapports'
    )
    type_rapport = models.CharField(
        max_length=20, choices=TYPE_RAPPORT_CHOICES, default='completion'
    )

    # Pour les tâches terminées
    commentaire = models.TextField(blank=True, null=True)
    photo = models.ImageField(
        upload_to='rapports/photos/%Y/%m/', blank=True, null=True
    )

    # Pour les tâches non exécutées
    raison_non_execution = models.TextField(blank=True, null=True)
    categorie_raison = models.CharField(
        max_length=50, blank=True, null=True,
        choices=[
            ('absence', 'Absence client'),
            ('indisponibilite', 'Indisponibilité accès'),
            ('materiel', 'Problème matériel'),
            ('meteo', 'Conditions météo'),
            ('urgence', 'Urgence autre'),
            ('autre', 'Autre'),
        ]
    )

    date_soumission = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True
    )

    class Meta:
        ordering = ['-date_soumission']

    def __str__(self):
        target = self.sous_tache or self.tache
        return f"Rapport: {target} - {self.get_type_rapport_display()}"
