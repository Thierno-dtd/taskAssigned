import os
import time

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Supprime les fichiers Excel temporaires d'import (media/imports_temp/) "
        "abandonnés depuis plus de N minutes (import commencé mais jamais confirmé). "
        "À lancer périodiquement via cron, ex: toutes les heures."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes', type=int, default=60,
            help="Âge minimum en minutes avant suppression (défaut: 60)"
        )

    def handle(self, *args, **options):
        dossier = os.path.join(settings.MEDIA_ROOT, 'imports_temp')
        if not os.path.isdir(dossier):
            self.stdout.write("Aucun dossier imports_temp, rien à nettoyer.")
            return

        seuil = time.time() - (options['minutes'] * 60)
        supprimes = 0

        for nom_fichier in os.listdir(dossier):
            chemin = os.path.join(dossier, nom_fichier)
            if os.path.isfile(chemin) and os.path.getmtime(chemin) < seuil:
                os.remove(chemin)
                supprimes += 1

        self.stdout.write(
            self.style.SUCCESS(f"{supprimes} fichier(s) d'import temporaire(s) supprimé(s).")
        )