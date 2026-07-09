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