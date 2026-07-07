from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Tache, SousTache

# Import channels optionnel (pour notifications WebSocket)
try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False
    get_channel_layer = None


@receiver(post_save, sender=Tache)
def notify_task_created_or_updated(sender, instance, created, **kwargs):
    """
    Envoie une notification quand une tâche est créée ou modifiée.
    """
    if not CHANNELS_AVAILABLE:
        return

    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    if created:
        message = {
            'type': 'task_notification',
            'message': f"Nouvelle tâche assignée: {instance.titre}",
            'task_id': instance.id,
            'agent_id': instance.assigne_a.id if instance.assigne_a else None,
            'priority': instance.priorite,
            'status': instance.status
        }
    else:
        message = {
            'type': 'task_notification',
            'message': f"Tâche mise à jour: {instance.titre}",
            'task_id': instance.id,
            'agent_id': instance.assigne_a.id if instance.assigne_a else None,
            'status': instance.status
        }

    # Envoyer au groupe de l'agent
    if instance.assigne_a:
        group_name = f"agent_{instance.assigne_a.id}"
        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'message': message
                }
            )
        except Exception:
            # Channel layer non configuré, ignorer silencieusement
            pass


@receiver(post_save, sender=SousTache)
def notify_subtask_updated(sender, instance, created, **kwargs):
    """
    Notifie quand une sous-tâche est mise à jour.
    """
    if not CHANNELS_AVAILABLE:
        return

    if instance.tache and instance.tache.assigne_a:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        message = {
            'type': 'subtask_notification',
            'message': f"Sous-tâche {instance.titre}: "
                       f"{instance.get_status_display()}",
            'subtask_id': instance.id,
            'task_id': instance.tache.id,
            'agent_id': instance.tache.assigne_a.id,
            'status': instance.status
        }

        group_name = f"agent_{instance.tache.assigne_a.id}"
        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'message': message
                }
            )
        except Exception:
            pass
