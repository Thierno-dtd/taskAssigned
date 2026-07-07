from rest_framework import permissions


class IsAdminOrManager(permissions.BasePermission):
    """
    Autorise uniquement les utilisateurs avec le rôle 'admin' ou 'manager'.
    Utilisé pour restreindre la création/assignation des tâches : un agent
    ne doit pas pouvoir créer ou assigner de tâches, seulement les exécuter.
    """
    message = "Seuls les administrateurs et managers peuvent effectuer cette action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) in ('admin', 'manager')
        )


class IsAdminOrManagerOrReadOnly(permissions.BasePermission):
    """
    Lecture libre pour tout utilisateur authentifié, écriture réservée
    aux admin/manager.
    """
    message = "Seuls les administrateurs et managers peuvent modifier cette ressource."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(request.user, 'role', None) in ('admin', 'manager')