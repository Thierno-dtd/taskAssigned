"""
Vues pour la carte GPS et la gestion des coordonnées.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Tache


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def map_tasks_data(request):
    """
    Récupère les tâches avec coordonnées GPS pour affichage sur carte.
    Filtres: ?semaine_id=1&agent_id=2&status=pending
    """
    queryset = Tache.objects.filter(
        gps_latitude__isnull=False,
        gps_longitude__isnull=False
    )

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

    tasks = []
    for tache in queryset.select_related('semaine', 'assigne_a'):
        agent_info = None
        if tache.assigne_a:
            agent_info = {
                'id': tache.assigne_a.id,
                'name': f"{tache.assigne_a.first_name} {tache.assigne_a.last_name}",
                'phone': tache.assigne_a.phone,
            }

        tasks.append({
            'id': tache.id,
            'title': tache.titre,
            'description': tache.description,
            'status': tache.status,
            'status_display': tache.get_status_display(),
            'priority': tache.priorite,
            'priority_display': tache.get_priorite_display(),
            'coordinates': {
                'latitude': float(tache.gps_latitude),
                'longitude': float(tache.gps_longitude),
            },
            'address': tache.adresse_complet or 'Adresse non spécifiée',
            'agent': agent_info,
            'week': str(tache.semaine) if tache.semaine else None,
        })

    # Statistiques
    stats = {
        'total': len(tasks),
        'by_status': {
            'pending': len([t for t in tasks if t['status'] == 'pending']),
            'in_progress': len([t for t in tasks if t['status'] == 'in_progress']),
            'completed': len([t for t in tasks if t['status'] == 'completed']),
            'not_done': len([t for t in tasks if t['status'] == 'not_done']),
        }
    }

    return Response({
        'tasks': tasks,
        'statistics': stats,
        'center': {
            'latitude': 0.4162,  # Libreville
            'longitude': 9.4673,
        },
        'zoom': 12,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_tracking_data(request):
    """
    Récupère la position actuelle des agents (dernière tâche mise à jour).
    Admin/Manager uniquement.
    """
    if request.user.role not in ['admin', 'manager']:
        return Response(
            {'error': 'Permission refusée'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Récupérer la dernière tâche de chaque agent avec coordonnées
    from accounts.models import User

    agents_data = []
    for agent in User.objects.filter(role='agent', is_active=True):
        last_task = Tache.objects.filter(
            assigne_a=agent,
            gps_latitude__isnull=False,
            gps_longitude__isnull=False
        ).order_by('-date_realisation').first()

        if last_task:
            agents_data.append({
                'agent': {
                    'id': agent.id,
                    'name': f"{agent.first_name} {agent.last_name}",
                    'phone': agent.phone,
                    'matricule': agent.agent_profile.matricule if hasattr(agent, 'agent_profile') else None,
                },
                'last_location': {
                    'latitude': float(last_task.gps_latitude),
                    'longitude': float(last_task.gps_longitude),
                    'address': last_task.adresse_complet,
                    'task_title': last_task.titre,
                    'timestamp': last_task.date_realisation,
                },
                'status': 'active' if agent.is_active else 'inactive',
            })

    return Response({
        'agents': agents_data,
        'count': len(agents_data),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_task_location(request, task_id):
    """
    Met à jour la position GPS d'une tâche (par l'agent).
    Body: {"latitude": 0.4162, "longitude": 9.4673, "address": "..."}
    """
    try:
        task = Tache.objects.get(id=task_id)
    except Tache.DoesNotExist:
        return Response(
            {'error': 'Tâche introuvable'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Vérifier que l'agent peut modifier cette tâche
    if request.user.role == 'agent' and task.assigne_a != request.user:
        return Response(
            {'error': 'Vous ne pouvez modifier que vos propres tâches'},
            status=status.HTTP_403_FORBIDDEN
        )

    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    address = request.data.get('address')

    if latitude is None or longitude is None:
        return Response(
            {'error': 'Latitude et longitude requises'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        task.gps_latitude = latitude
        task.gps_longitude = longitude
        if address:
            task.adresse_complet = address
        task.save()

        return Response({
            'success': True,
            'message': 'Position mise à jour',
            'task_id': task.id,
            'coordinates': {
                'latitude': float(task.gps_latitude),
                'longitude': float(task.gps_longitude),
            }
        })
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la mise à jour: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nearby_tasks(request):
    """
    Récupère les tâches proches d'une position GPS.
    Params: ?lat=0.4162&lng=9.4673&radius_km=5
    """
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')
    radius_km = float(request.query_params.get('radius_km', 5))

    if lat is None or lng is None:
        return Response(
            {'error': 'Paramètres lat et lng requis'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return Response(
            {'error': 'Coordonnées invalides'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Récupérer toutes les tâches avec coordonnées
    queryset = Tache.objects.filter(
        gps_latitude__isnull=False,
        gps_longitude__isnull=False
    )

    # Filtrer par agent si nécessaire
    if request.user.role == 'agent':
        queryset = queryset.filter(assigne_a=request.user)

    # Calculer distance approximative (formule de Haversine simplifiée)
    import math

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Rayon de la Terre en km
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    nearby = []
    for task in queryset.select_related('assigne_a'):
        try:
            task_lat = float(task.gps_latitude)
            task_lng = float(task.gps_longitude)
            distance = haversine(lat, lng, task_lat, task_lng)

            if distance <= radius_km:
                nearby.append({
                    'id': task.id,
                    'title': task.titre,
                    'status': task.status,
                    'distance_km': round(distance, 2),
                    'coordinates': {
                        'latitude': task_lat,
                        'longitude': task_lng,
                    },
                    'agent': task.assigne_a.username if task.assigne_a else None,
                })
        except (ValueError, TypeError):
            continue

    # Trier par distance
    nearby.sort(key=lambda x: x['distance_km'])

    return Response({
        'center': {'latitude': lat, 'longitude': lng},
        'radius_km': radius_km,
        'tasks': nearby,
        'count': len(nearby),
    })