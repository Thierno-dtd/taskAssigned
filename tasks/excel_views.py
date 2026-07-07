"""
Vues pour l'import/export Excel des tâches et agents.
"""
import io
import os
import re
import uuid
import unicodedata
from datetime import datetime

import pandas as pd
from django.conf import settings as django_settings
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User, AgentProfile
from tasks.models import Semaine, Tache, SousTache, ImportLot


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_tasks_excel(request):
    """
    Exporte les tâches vers Excel.
    Filtres optionnels: ?semaine_id=1&agent_id=2&status=pending
    """
    queryset = Tache.objects.all()

    # Filtres
    semaine_id = request.query_params.get('semaine_id')
    agent_id = request.query_params.get('agent_id')
    status_filter = request.query_params.get('status')

    if semaine_id:
        queryset = queryset.filter(semaine_id=semaine_id)
    if agent_id:
        queryset = queryset.filter(assigne_a_id=agent_id)
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Agents ne voient que leurs tâches
    if request.user.role == 'agent':
        queryset = queryset.filter(assigne_a=request.user)

    data = []
    for tache in queryset.select_related('semaine', 'assigne_a').prefetch_related('sous_taches'):
        agent_name = ""
        if tache.assigne_a:
            agent_name = f"{tache.assigne_a.first_name} {tache.assigne_a.last_name}"

        sous_taches_count = tache.sous_taches.count()
        sous_taches_done = tache.sous_taches.filter(status='completed').count()

        data.append({
            'ID': tache.id,
            'Titre': tache.titre,
            'Description': tache.description,
            'Semaine': str(tache.semaine) if tache.semaine else '',
            'Agent': agent_name,
            'Priorité': tache.get_priorite_display(),
            'Statut': tache.get_status_display(),
            'Date début prévue': tache.date_debut_prevue,
            'Date fin prévue': tache.date_fin_prevue,
            'Date réalisation': tache.date_realisation,
            'Sous-tâches': f"{sous_taches_done}/{sous_taches_count}",
            'GPS Latitude': float(tache.gps_latitude) if tache.gps_latitude else None,
            'GPS Longitude': float(tache.gps_longitude) if tache.gps_longitude else None,
        })

    df = pd.DataFrame(data)

    # Créer le fichier Excel en mémoire
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Taches', index=False)

        # Ajuster largeurs colonnes
        worksheet = writer.sheets['Taches']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)

    filename = f"taches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_agents_excel(request):
    """
    Exporte les agents vers Excel (admin/manager uniquement).
    """
    if request.user.role not in ['admin', 'manager']:
        return Response(
            {'error': 'Permission refusée'},
            status=status.HTTP_403_FORBIDDEN
        )

    agents = AgentProfile.objects.select_related('user').all()

    data = []
    for agent in agents:
        data.append({
            'ID': agent.id,
            'Matricule': agent.matricule,
            'Nom': agent.user.last_name,
            'Prénom': agent.user.first_name,
            'Username': agent.user.username,
            'Email': agent.user.email,
            'Téléphone': agent.user.phone,
            'Zone': agent.zone_intervention,
            'Date embauche': agent.date_embauche,
            'Actif': 'Oui' if agent.is_active else 'Non',
            'Dernière connexion': agent.user.last_login,
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Agents', index=False)

        worksheet = writer.sheets['Agents']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)

    filename = f"agents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_tasks_excel(request):
    """
    Importe des tâches depuis Excel.
    Fichier Excel attendu avec colonnes:
    - Titre, Description, Semaine_ID, Agent_Username, Priorité, Date_debut_prevue, Date_fin_prevue
    """
    if request.user.role not in ['admin', 'manager']:
        return Response(
            {'error': 'Permission refusée'},
            status=status.HTTP_403_FORBIDDEN
        )

    if 'file' not in request.FILES:
        return Response(
            {'error': 'Fichier Excel requis'},
            status=status.HTTP_400_BAD_REQUEST
        )

    excel_file = request.FILES['file']

    try:
        df = pd.read_excel(excel_file)

        required_columns = ['Titre', 'Semaine_ID', 'Agent_Username']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return Response(
                {'error': f'Colonnes manquantes: {missing}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                titre = str(row['Titre'])
                if not titre:
                    errors.append(f"Ligne {index+2}: Titre vide")
                    continue

                # Récupérer la semaine
                semaine_id = row['Semaine_ID']
                try:
                    semaine = Semaine.objects.get(id=int(semaine_id))
                except (Semaine.DoesNotExist, ValueError):
                    errors.append(f"Ligne {index+2}: Semaine {semaine_id} introuvable")
                    continue

                # Récupérer l'agent
                agent_username = str(row['Agent_Username'])
                try:
                    agent = User.objects.get(username=agent_username, role='agent')
                except User.DoesNotExist:
                    errors.append(f"Ligne {index+2}: Agent {agent_username} introuvable")
                    continue

                # Options
                priorite = str(row.get('Priorité', 'medium')).lower()
                if priorite not in ['low', 'medium', 'high', 'urgent']:
                    priorite = 'medium'

                description = str(row.get('Description', ''))

                # Dates
                date_debut = row.get('Date_debut_prevue')
                date_fin = row.get('Date_fin_prevue')

                # Créer la tâche
                Tache.objects.create(
                    semaine=semaine,
                    titre=titre,
                    description=description,
                    assigne_a=agent,
                    priorite=priorite,
                    status='pending',
                    date_debut_prevue=date_debut if pd.notna(date_debut) else None,
                    date_fin_prevue=date_fin if pd.notna(date_fin) else None,
                )
                created_count += 1

            except Exception as e:
                errors.append(f"Ligne {index+2}: {str(e)}")

        return Response({
            'success': True,
            'created': created_count,
            'errors': errors,
            'total_rows': len(df)
        })

    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'import: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


# ---------------------------------------------------------------------------
# NOUVEAU FLUX D'IMPORT DYNAMIQUE (superviseur non-informaticien)
#
# Étape 1 (analyser_fichier_excel)  : on lit juste les en-têtes + un aperçu,
#   on stocke temporairement le fichier, on renvoie les colonnes trouvées
#   pour que le superviseur choisisse quoi en faire dans l'app.
# Étape 2 (confirmer_import_excel)  : le superviseur renvoie sa config
#   (mapping des colonnes, colonnes obligatoires, colonnes visibles côté
#   mobile) et on crée réellement les tâches.
# ---------------------------------------------------------------------------

IMPORT_TEMP_DIR = os.path.join(django_settings.MEDIA_ROOT, 'imports_temp')


def _normaliser(texte):
    """minuscule + sans accents + espaces compactés, pour comparer des noms"""
    if texte is None:
        return ''
    texte = str(texte).strip().lower()
    texte = unicodedata.normalize('NFKD', texte).encode('ascii', 'ignore').decode()
    texte = re.sub(r'\s+', ' ', texte)
    return texte


def _valeur_json_safe(valeur):
    """Convertit une cellule pandas (NaN, Timestamp, numpy...) en valeur JSON-safe."""
    if valeur is None or (isinstance(valeur, float) and pd.isna(valeur)):
        return None
    if pd.isna(valeur):
        return None
    if isinstance(valeur, (pd.Timestamp, datetime)):
        return valeur.isoformat()
    if hasattr(valeur, 'item'):  # types numpy (int64, float64...)
        return valeur.item()
    return str(valeur) if not isinstance(valeur, (int, float, bool)) else valeur


def _deviner_colonne(colonnes, mots_cles):
    """Essaie de deviner quelle colonne correspond à un champ (ex: 'agent')."""
    for col in colonnes:
        col_norm = _normaliser(col)
        for mot in mots_cles:
            if mot in col_norm:
                return col
    return None


def _trouver_agent(valeur_brute):
    """
    Retrouve un agent à partir d'une cellule Excel qui peut contenir :
    le username, le matricule, ou le nom complet (dans un ordre ou l'autre).
    Retourne (agent, erreur). agent=None si non trouvé ou ambigu.
    """
    if valeur_brute is None or str(valeur_brute).strip() == '':
        return None, "valeur agent vide"

    valeur = str(valeur_brute).strip()
    valeur_norm = _normaliser(valeur)

    # 1. Correspondance exacte sur le username
    agent = User.objects.filter(
        role='agent', username__iexact=valeur
    ).first()
    if agent:
        return agent, None

    # 2. Correspondance sur le matricule
    profil = AgentProfile.objects.filter(matricule__iexact=valeur).first()
    if profil:
        return profil.user, None

    # 3. Correspondance sur le nom complet (dans les deux sens)
    candidats = []
    for u in User.objects.filter(role='agent'):
        nom_complet = _normaliser(f"{u.first_name} {u.last_name}")
        nom_inverse = _normaliser(f"{u.last_name} {u.first_name}")
        if valeur_norm in (nom_complet, nom_inverse) and valeur_norm:
            candidats.append(u)

    if len(candidats) == 1:
        return candidats[0], None
    if len(candidats) > 1:
        return None, f"plusieurs agents correspondent à '{valeur}', préciser (username/matricule)"

    return None, f"aucun agent trouvé pour '{valeur}'"


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyser_fichier_excel(request):
    """
    Étape 1 : le superviseur envoie juste le fichier Excel.
    On lit les en-têtes + un aperçu des premières lignes, on stocke le
    fichier temporairement, et on renvoie tout ça pour que l'app affiche
    les colonnes et laisse le superviseur choisir sa configuration.
    """
    if request.user.role not in ['admin', 'manager']:
        return Response({'error': 'Permission refusée'}, status=status.HTTP_403_FORBIDDEN)

    if 'file' not in request.FILES:
        return Response({'error': 'Fichier Excel requis'}, status=status.HTTP_400_BAD_REQUEST)

    excel_file = request.FILES['file']
    if not excel_file.name.lower().endswith(('.xlsx', '.xls')):
        return Response(
            {'error': 'Seuls les fichiers .xlsx ou .xls sont acceptés'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        return Response(
            {'error': f"Impossible de lire le fichier Excel : {e}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if df.empty or len(df.columns) == 0:
        return Response(
            {'error': "Le fichier semble vide ou sans en-têtes de colonnes."},
            status=status.HTTP_400_BAD_REQUEST
        )

    colonnes = [str(c) for c in df.columns]

    # Stockage temporaire du fichier pour l'étape de confirmation
    os.makedirs(IMPORT_TEMP_DIR, exist_ok=True)
    import_id = uuid.uuid4().hex
    chemin_temp = os.path.join(IMPORT_TEMP_DIR, f"{import_id}.xlsx")
    excel_file.seek(0)
    with open(chemin_temp, 'wb') as f:
        for chunk in excel_file.chunks():
            f.write(chunk)

    apercu = []
    for _, row in df.head(5).iterrows():
        apercu.append({col: _valeur_json_safe(row[col]) for col in colonnes})

    suggestions = {
        'agent': _deviner_colonne(colonnes, ['agent', 'technicien', 'nom agent', 'employe', 'nom']),
        'titre': _deviner_colonne(colonnes, ['titre', 'tache', 'intitule', 'designation', 'objet']),
        'description': _deviner_colonne(colonnes, ['description', 'detail', 'commentaire']),
        'priorite': _deviner_colonne(colonnes, ['priorite', 'priority']),
        'date_debut_prevue': _deviner_colonne(colonnes, ['date debut', 'debut prevu']),
        'date_fin_prevue': _deviner_colonne(colonnes, ['date fin', 'fin prevue', 'echeance']),
    }

    return Response({
        'import_id': import_id,
        'nom_fichier': excel_file.name,
        'colonnes': colonnes,
        'total_lignes': len(df),
        'apercu': apercu,
        'suggestions': suggestions,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirmer_import_excel(request):
    """
    Étape 2 : le superviseur confirme sa configuration :
    {
        "import_id": "...",
        "semaine_id": 3,
        "mapping": {
            "agent": "Nom de l'agent",   # obligatoire
            "titre": "Intitulé",         # optionnel
            "description": "Détail",     # optionnel
            "priorite": "Priorité",      # optionnel
            "date_debut_prevue": "Début",# optionnel
            "date_fin_prevue": "Fin"     # optionnel
        },
        "colonnes_obligatoires": ["Nom de l'agent", "Adresse"],
        "colonnes_visibles_mobile": ["Adresse", "Compteur", "Zone"]
    }
    Toutes les colonnes du fichier sont conservées dans chaque tâche
    (donnees_excel), mais seules celles listées dans
    colonnes_visibles_mobile seront montrées à l'agent dans l'app mobile.
    Les identifiants de tâche sont générés automatiquement, le superviseur
    n'a jamais à les fournir.
    """
    if request.user.role not in ['admin', 'manager']:
        return Response({'error': 'Permission refusée'}, status=status.HTTP_403_FORBIDDEN)

    import_id = request.data.get('import_id')
    semaine_id = request.data.get('semaine_id')
    mapping = request.data.get('mapping') or {}
    colonnes_obligatoires = request.data.get('colonnes_obligatoires') or []
    colonnes_visibles_mobile = request.data.get('colonnes_visibles_mobile') or []

    if not import_id:
        return Response({'error': "import_id manquant"}, status=status.HTTP_400_BAD_REQUEST)
    if not semaine_id:
        return Response({'error': "semaine_id manquant"}, status=status.HTTP_400_BAD_REQUEST)
    if 'agent' not in mapping or not mapping['agent']:
        return Response(
            {'error': "Le mapping doit indiquer quelle colonne identifie l'agent (mapping['agent'])"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        semaine = Semaine.objects.get(id=semaine_id)
    except Semaine.DoesNotExist:
        return Response({'error': f"Semaine {semaine_id} introuvable"}, status=status.HTTP_400_BAD_REQUEST)

    chemin_temp = os.path.join(IMPORT_TEMP_DIR, f"{import_id}.xlsx")
    if not os.path.exists(chemin_temp):
        return Response(
            {'error': "Session d'import expirée ou introuvable, merci de réimporter le fichier."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        df = pd.read_excel(chemin_temp)
    except Exception as e:
        return Response({'error': f"Impossible de relire le fichier : {e}"}, status=status.HTTP_400_BAD_REQUEST)

    colonnes_fichier = [str(c) for c in df.columns]

    # Vérifier que les colonnes mappées et obligatoires existent bien dans le fichier
    colonnes_attendues = set(mapping.values()) | set(colonnes_obligatoires) | set(colonnes_visibles_mobile)
    colonnes_manquantes = [c for c in colonnes_attendues if c and c not in colonnes_fichier]
    if colonnes_manquantes:
        return Response(
            {'error': f"Colonnes introuvables dans le fichier : {colonnes_manquantes}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    lot = ImportLot.objects.create(
        nom_fichier=os.path.basename(chemin_temp),
        semaine=semaine,
        importe_par=request.user,
        toutes_colonnes=colonnes_fichier,
        colonnes_obligatoires=colonnes_obligatoires,
        colonnes_visibles_mobile=colonnes_visibles_mobile,
        mapping=mapping,
    )

    created_count = 0
    erreurs = []

    for index, row in df.iterrows():
        ligne_num = index + 2  # +1 pour l'en-tête, +1 pour l'index 0-based

        # Colonnes obligatoires : toutes doivent être renseignées sur cette ligne
        manquantes = [
            col for col in colonnes_obligatoires
            if pd.isna(row.get(col)) or str(row.get(col)).strip() == ''
        ]
        if manquantes:
            erreurs.append(f"Ligne {ligne_num}: colonnes obligatoires vides {manquantes}")
            continue

        # Résolution de l'agent (username, matricule, ou nom complet)
        agent, err = _trouver_agent(row.get(mapping['agent']))
        if err:
            erreurs.append(f"Ligne {ligne_num}: {err}")
            continue

        # Titre : colonne mappée si fournie, sinon généré automatiquement
        colonne_titre = mapping.get('titre')
        if colonne_titre and pd.notna(row.get(colonne_titre)) and str(row.get(colonne_titre)).strip():
            titre = str(row.get(colonne_titre)).strip()
        else:
            titre = f"Tâche {agent.get_full_name() or agent.username} - Semaine {semaine.numero}"

        description = ''
        colonne_desc = mapping.get('description')
        if colonne_desc and pd.notna(row.get(colonne_desc)):
            description = str(row.get(colonne_desc))

        priorite = 'medium'
        colonne_priorite = mapping.get('priorite')
        if colonne_priorite and pd.notna(row.get(colonne_priorite)):
            val = _normaliser(row.get(colonne_priorite))
            correspondance = {
                'basse': 'low', 'low': 'low',
                'moyenne': 'medium', 'medium': 'medium',
                'haute': 'high', 'high': 'high',
                'urgente': 'urgent', 'urgent': 'urgent',
            }
            priorite = correspondance.get(val, 'medium')

        date_debut_prevue = None
        colonne_deb = mapping.get('date_debut_prevue')
        if colonne_deb and pd.notna(row.get(colonne_deb)):
            try:
                date_debut_prevue = pd.to_datetime(row.get(colonne_deb))
            except Exception:
                date_debut_prevue = None

        date_fin_prevue = None
        colonne_fin = mapping.get('date_fin_prevue')
        if colonne_fin and pd.notna(row.get(colonne_fin)):
            try:
                date_fin_prevue = pd.to_datetime(row.get(colonne_fin))
            except Exception:
                date_fin_prevue = None

        # Toutes les colonnes du fichier sont conservées (audit + dashboard),
        # seul le sous-ensemble "colonnes_visibles_mobile" sera montré à l'agent
        # (voir TacheDetailSerializer/TacheListSerializer).
        donnees_excel = {col: _valeur_json_safe(row.get(col)) for col in colonnes_fichier}

        try:
            Tache.objects.create(
                titre=titre,
                description=description,
                semaine=semaine,
                assigne_a=agent,
                created_by=request.user,
                priorite=priorite,
                status='pending',
                date_debut_prevue=date_debut_prevue,
                date_fin_prevue=date_fin_prevue,
                lot_import=lot,
                donnees_excel=donnees_excel,
            )
            created_count += 1
        except Exception as e:
            erreurs.append(f"Ligne {ligne_num}: {e}")

    lot.nombre_taches_creees = created_count
    lot.nombre_erreurs = len(erreurs)
    lot.save(update_fields=['nombre_taches_creees', 'nombre_erreurs'])

    # Nettoyage du fichier temporaire, plus besoin après confirmation
    try:
        os.remove(chemin_temp)
    except OSError:
        pass

    return Response({
        'success': True,
        'lot_import_id': lot.id,
        'created': created_count,
        'total_rows': len(df),
        'errors': erreurs,
    })