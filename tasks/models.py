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


class ImportLot(models.Model):
    """
    Trace un import Excel réalisé par un superviseur : quel fichier,
    quelles colonnes existaient, lesquelles étaient obligatoires,
    lesquelles doivent être visibles côté mobile pour l'agent, et le
    mapping colonne -> champ choisi par le superviseur.
    """
    nom_fichier = models.CharField(max_length=255)
    semaine = models.ForeignKey(
        Semaine, on_delete=models.CASCADE, related_name='imports_excel'
    )
    importe_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='imports_excel'
    )
    toutes_colonnes = models.JSONField(default=list, blank=True)
    colonnes_obligatoires = models.JSONField(default=list, blank=True)
    colonnes_visibles_mobile = models.JSONField(default=list, blank=True)
    mapping = models.JSONField(
        default=dict, blank=True,
        help_text="Ex: {'agent': 'Nom Agent', 'titre': 'Intitulé tâche'}"
    )
    date_import = models.DateTimeField(auto_now_add=True)
    nombre_taches_creees = models.PositiveIntegerField(default=0)
    nombre_erreurs = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date_import']

    def __str__(self):
        return f"Import {self.nom_fichier} ({self.date_import:%d/%m/%Y %H:%M})"


class Notification(models.Model):
    """
    Notification simple stockée en base (consultable par polling depuis
    le front web/mobile). Remplace l'ancien squelette de notifications
    WebSocket (django `channels`) qui n'était jamais actif : pas
    d'infra supplémentaire nécessaire (pas de Redis/ASGI requis), le
    front peut simplement appeler GET /api/notifications/ périodiquement.
    """
    TYPE_CHOICES = [
        ('tache_assignee', 'Nouvelle tâche assignée'),
        ('tache_modifiee', 'Tâche modifiée'),
        ('rapport_soumis', 'Rapport soumis'),
    ]

    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications'
    )
    type_notification = models.CharField(max_length=30, choices=TYPE_CHOICES)
    message = models.CharField(max_length=255)
    tache = models.ForeignKey(
        'Tache', on_delete=models.CASCADE, null=True, blank=True,
        related_name='notifications'
    )
    lu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.get_type_notification_display()} -> {self.destinataire}"


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
    gps_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        help_text="Latitude du lieu d'intervention"
    )
    gps_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        help_text="Longitude du lieu d'intervention"
    )
    adresse_complet = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Adresse complète du lieu d'intervention"
    )
    lot_import = models.ForeignKey(
        ImportLot, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='taches'
    )
    donnees_excel = models.JSONField(
        default=dict, blank=True,
        help_text="Colonnes additionnelles issues du fichier Excel d'origine"
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