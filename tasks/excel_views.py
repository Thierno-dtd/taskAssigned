"""
Vues pour l'import/export Excel des tâches et agents.
"""
import io
from datetime import datetime

import pandas as pd
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User, AgentProfile
from tasks.models import Semaine, Tache, SousTache


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
