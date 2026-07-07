from django.db.models import Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tasks.models import Tache, SousTache, Semaine
from reports.models import RapportExecution


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistiques_generales(request):
    """Statistiques globales pour le dashboard admin."""
    user = request.user

    # Filtre selon le rôle
    tache_qs = Tache.objects.all()
    if user.role == 'agent':
        tache_qs = tache_qs.filter(assigne_a=user)

    total_taches = tache_qs.count()
    taches_terminees = tache_qs.filter(status='completed').count()
    taches_non_executees = tache_qs.filter(status='not_done').count()
    taches_en_cours = tache_qs.filter(status='in_progress').count()
    taches_en_attente = tache_qs.filter(status='pending').count()

    # Calcul des taux
    taux_execution = (
        (taches_terminees / total_taches * 100) if total_taches > 0 else 0
    )
    taux_non_execution = (
        (taches_non_executees / total_taches * 100) if total_taches > 0 else 0
    )

    # Sous-tâches
    sous_tache_qs = SousTache.objects.all()
    if user.role == 'agent':
        sous_tache_qs = sous_tache_qs.filter(
            tache__assigne_a=user
        )

    total_sous_taches = sous_tache_qs.count()
    sous_taches_terminees = sous_tache_qs.filter(status='completed').count()

    return Response({
        'total_taches': total_taches,
        'taches_terminees': taches_terminees,
        'taches_non_executees': taches_non_executees,
        'taches_en_cours': taches_en_cours,
        'taches_en_attente': taches_en_attente,
        'taux_execution': round(taux_execution, 2),
        'taux_non_execution': round(taux_non_execution, 2),
        'total_sous_taches': total_sous_taches,
        'sous_taches_terminees': sous_taches_terminees,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistiques_par_semaine(request, semaine_id=None):
    """Statistiques filtrées par semaine."""
    user = request.user

    if semaine_id:
        taches = Tache.objects.filter(semaine_id=semaine_id)
    else:
        # Semaine en cours
        semaine_actuelle = Semaine.objects.filter(is_active=True).first()
        if semaine_actuelle:
            taches = Tache.objects.filter(semaine=semaine_actuelle)
        else:
            taches = Tache.objects.none()

    if user.role == 'agent':
        taches = taches.filter(assigne_a=user)

    par_status = taches.values('status').annotate(count=Count('id'))

    return Response({
        'semaine_id': semaine_id,
        'total': taches.count(),
        'par_status': list(par_status)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def statistiques_par_agent(request):
    """Statistiques par agent (admin seulement)."""
    if request.user.role == 'agent':
        return Response({'error': 'Accès non autorisé'}, status=403)

    stats = Tache.objects.values(
        'assigne_a__username',
        'assigne_a__first_name',
        'assigne_a__last_name'
    ).annotate(
        total=Count('id'),
        terminees=Count('id', filter=Q(status='completed')),
        non_executees=Count('id', filter=Q(status='not_done'))
    )

    return Response(list(stats))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def raisons_non_execution(request):
    """Raisons des non-exécutions pour analyse."""
    if request.user.role == 'agent':
        rapports = RapportExecution.objects.filter(agent=request.user)
    else:
        rapports = RapportExecution.objects.all()

    raisons = rapports.filter(type_rapport='non_execution').values(
        'categorie_raison'
    ).annotate(count=Count('id'))

    return Response(list(raisons))

