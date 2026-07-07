from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Tache, Notification


@receiver(post_save, sender=Tache)
def notifier_tache(sender, instance, created, **kwargs):
    """
    Crée une notification en base pour l'agent assigné, à la création
    d'une tâche ou quand son statut change. Consultable via
    GET /api/notifications/ (voir tasks/views.py).
    """
    if not instance.assigne_a:
        return

    if created:
        Notification.objects.create(
            destinataire=instance.assigne_a,
            type_notification='tache_assignee',
            message=f"Nouvelle tâche assignée : {instance.titre}",
            tache=instance,
        )
    else:
        Notification.objects.create(
            destinataire=instance.assigne_a,
            type_notification='tache_modifiee',
            message=f"Tâche mise à jour : {instance.titre} "
                    f"({instance.get_status_display()})",
            tache=instance,
        )