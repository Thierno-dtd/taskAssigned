from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Autorise uniquement le rôle 'admin'. Utilisé pour les opérations
    sensibles de gestion des comptes (création de managers, changement
    de rôle) qui ne doivent être faites que par l'administrateur de la
    plateforme.
    """
    message = "Seul un administrateur peut effectuer cette action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'admin'
        )


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Autorise les rôles 'manager' et 'admin'. Utilisé pour la création
    de comptes agent : il n'y a plus d'auto-inscription publique, seuls
    un manager ou un admin peuvent créer un compte agent.
    """
    message = "Seul un manager ou un administrateur peut effectuer cette action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) in ('manager', 'admin')
        )


class IsFullyVerified(permissions.IsAuthenticated):
    """
    Comme IsAuthenticated, mais bloque en plus l'accès à toute l'API
    tant que l'utilisateur n'a pas terminé sa procédure de première
    connexion :
    - vérification du numéro de téléphone par OTP (phone_verifie)
    - changement du mot de passe temporaire (must_change_password)

    Défini comme DEFAULT_PERMISSION_CLASSES dans settings.py. Les seuls
    endpoints qui restent accessibles dans cet état sont ceux qui
    déclarent explicitement permission_classes=[IsAuthenticated] pour
    court-circuiter ce blocage : ChangePasswordView, et les vues de
    vérification téléphone (request_phone_verification / verify_phone)
    — sinon l'utilisateur serait bloqué partout sans aucun moyen d'en
    sortir.
    """
    message = (
        "Vous devez vérifier votre numéro de téléphone et changer votre "
        "mot de passe temporaire avant de continuer."
    )

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        user = request.user
        return (not user.must_change_password) and user.phone_verifie