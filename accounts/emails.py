import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def envoyer_identifiants_par_email(user, mot_de_passe_temporaire):
    """
    Envoie les identifiants de connexion par email à un utilisateur dont
    le compte vient d'être créé par un manager ou un admin, avec un mot
    de passe temporaire.

    N'échoue jamais bruyamment : si l'envoi échoue (mauvaise config SMTP,
    email invalide, etc.), on logge l'erreur mais on ne bloque pas la
    création du compte — le mot de passe temporaire est de toute façon
    renvoyé une fois dans la réponse API à la personne qui a créé le
    compte, en secours si l'email n'arrive jamais.

    Retourne True si l'envoi a réussi, False sinon.
    """
    if not user.email:
        logger.warning(
            "Pas d'email renseigné pour '%s', identifiants non envoyés par mail.",
            user.username
        )
        return False

    sujet = "Votre compte SEEG Intervention a été créé"
    message = (
        f"Bonjour {user.get_full_name() or user.username},\n\n"
        f"Un compte vient d'être créé pour vous sur l'application "
        f"SEEG Intervention.\n\n"
        f"Identifiant : {user.username}\n"
        f"Mot de passe temporaire : {mot_de_passe_temporaire}\n\n"
        f"À votre première connexion sur l'application mobile, il vous "
        f"sera demandé de :\n"
        f"1. Vérifier votre numéro de téléphone par code SMS\n"
        f"2. Changer ce mot de passe temporaire\n\n"
        f"— L'équipe SEEG"
    )

    try:
        send_mail(
            sujet,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@seeg.ga'),
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception(
            "Échec de l'envoi de l'email d'identifiants à '%s' (%s)",
            user.username, user.email
        )
        return False