"""
Envoi de SMS branchable.

En développement (aucun fournisseur configuré) : le SMS est simulé,
loggé et affiché en console — comportement inchangé par rapport à avant.

En production : configurer ces variables d'environnement pour activer
un vrai envoi via une API HTTP générique (Twilio, Africa's Talking,
Orange SMS API... tant qu'elles exposent un endpoint HTTP JSON) :

    SMS_PROVIDER_URL=https://api.mon-fournisseur.com/v1/send
    SMS_PROVIDER_API_KEY=xxxxx
    SMS_SENDER_ID=SEEG        (optionnel, défaut: "SEEG")

Si le format de requête de ton fournisseur diffère (ex: Twilio veut
un payload différent), adapte uniquement la fonction `envoyer_sms`
ci-dessous — le reste du code (otp_views.py) n'a pas à changer.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger('seeg')


class SmsSendError(Exception):
    """Levée quand l'envoi réel du SMS échoue (fournisseur en panne, etc.)."""
    pass


def envoyer_sms(phone_number, message):
    """
    Envoie un SMS. Retourne True si envoyé (ou simulé).
    Lève SmsSendError si un fournisseur est configuré mais que l'envoi échoue.
    """
    provider_url = getattr(settings, 'SMS_PROVIDER_URL', None)
    api_key = getattr(settings, 'SMS_PROVIDER_API_KEY', None)

    if not provider_url or not api_key:
        # Mode simulation (dev / pas encore de fournisseur configuré)
        logger.info(f"[SMS SIMULÉ] à {phone_number}: {message}")
        print(f"\n{'='*50}\n[SMS SIMULÉ] à {phone_number}\n{message}\n{'='*50}\n")
        return True

    try:
        response = requests.post(
            provider_url,
            json={
                'to': phone_number,
                'message': message,
                'sender': getattr(settings, 'SMS_SENDER_ID', 'SEEG'),
            },
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=10,
        )
        response.raise_for_status()
        logger.info(f"SMS envoyé à {phone_number} via {provider_url}")
        return True
    except requests.RequestException as e:
        logger.error(f"Échec envoi SMS à {phone_number} via {provider_url}: {e}")
        raise SmsSendError(str(e))