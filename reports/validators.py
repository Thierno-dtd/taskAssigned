from django.core.exceptions import ValidationError

TAILLE_MAX_PHOTO_MO = 5


def valider_taille_photo(fichier):
    """Refuse les photos de plus de 5 Mo (évite qu'un agent upload un fichier énorme)."""
    limite_octets = TAILLE_MAX_PHOTO_MO * 1024 * 1024
    if fichier.size > limite_octets:
        raise ValidationError(
            f"La photo est trop volumineuse ({fichier.size / (1024*1024):.1f} Mo). "
            f"Taille maximum autorisée : {TAILLE_MAX_PHOTO_MO} Mo."
        )