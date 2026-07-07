from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied

from .models import Semaine, Tache, SousTache, ImportLot, Notification
from .permissions import IsAdminOrManagerOrReadOnly, IsAdminOrManager
from .serializers import (
    SemaineSerializer, TacheListSerializer,
    TacheDetailSerializer, TacheCreateUpdateSerializer,
    SousTacheSerializer, ImportLotSerializer, NotificationSerializer
)


class SemaineListCreateView(generics.ListCreateAPIView):
    queryset = Semaine.objects.all()
    serializer_class = SemaineSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['annee', 'numero']


class SemaineDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Semaine.objects.all()
    serializer_class = SemaineSerializer
    permission_classes = [permissions.IsAuthenticated]


class TacheListCreateView(generics.ListCreateAPIView):
    queryset = Tache.objects.all()
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['semaine', 'assigne_a', 'status', 'priorite']
    search_fields = ['titre', 'description']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TacheCreateUpdateSerializer
        return TacheListSerializer

    def get_queryset(self):
        queryset = Tache.objects.all()
        user = self.request.user

        # Agents ne voient que leurs tâches
        if user.role == 'agent':
            queryset = queryset.filter(assigne_a=user)

        return queryset.select_related(
            'assigne_a', 'semaine'
        ).prefetch_related('sous_taches')


class TacheDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tache.objects.all()
    serializer_class = TacheDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Tache.objects.all()
        user = self.request.user

        if user.role == 'agent':
            queryset = queryset.filter(assigne_a=user)

        return queryset.select_related(
            'assigne_a', 'semaine'
        ).prefetch_related('sous_taches')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TacheCreateUpdateSerializer
        return TacheDetailSerializer


class SousTacheListCreateView(generics.ListCreateAPIView):
    serializer_class = SousTacheSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tache_id = self.kwargs.get('tache_id')
        return SousTache.objects.filter(tache_id=tache_id)

    def perform_create(self, serializer):
        tache_id = self.kwargs.get('tache_id')
        tache = get_object_or_404(Tache, id=tache_id)

        # Un agent ne peut découper en sous-tâches que SA propre tâche.
        # Admin/manager peuvent le faire sur n'importe quelle tâche.
        user = self.request.user
        if user.role == 'agent' and tache.assigne_a_id != user.id:
            raise PermissionDenied(
                "Vous ne pouvez ajouter des sous-tâches qu'à vos propres tâches."
            )

        serializer.save(tache=tache)


class SousTacheDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SousTache.objects.all()
    serializer_class = SousTacheSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mes_taches(request):
    """Endpoint pour que l'agent voie ses tâches assignées."""
    taches = Tache.objects.filter(assigne_a=request.user)
    serializer = TacheListSerializer(taches, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def taches_par_semaine(request, semaine_id):
    """Filtrer les tâches par semaine."""
    taches = Tache.objects.filter(semaine_id=semaine_id)

    if request.user.role == 'agent':
        taches = taches.filter(assigne_a=request.user)

    serializer = TacheListSerializer(taches, many=True, context={'request': request})
    return Response(serializer.data)



class ImportLotListView(generics.ListAPIView):
    """
    Historique des imports Excel (pour le superviseur/tableau de bord) :
    qui a importé quoi, quand, combien de tâches créées, combien d'erreurs.
    Filtre optionnel : ?semaine_id=3
    """
    serializer_class = ImportLotSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self):
        queryset = ImportLot.objects.all()
        semaine_id = self.request.query_params.get('semaine_id')
        if semaine_id:
            queryset = queryset.filter(semaine_id=semaine_id)
        return queryset


class ImportLotDetailView(generics.RetrieveAPIView):
    """Détail d'un import précis (config utilisée, résultats)."""
    queryset = ImportLot.objects.all()
    serializer_class = ImportLotSerializer
    permission_classes = [IsAdminOrManager]


class NotificationListView(generics.ListAPIView):
    """
    Notifications de l'utilisateur connecté (à consulter par polling
    depuis le front web/mobile, ex: toutes les 30s).
    Filtre optionnel : ?lu=false pour ne voir que les non-lues.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(destinataire=self.request.user)
        lu = self.request.query_params.get('lu')
        if lu is not None:
            queryset = queryset.filter(lu=(lu.lower() == 'true'))
        return queryset


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notifications_non_lues_count(request):
    """Nombre de notifications non lues (pour un badge dans le front)."""
    count = Notification.objects.filter(
        destinataire=request.user, lu=False
    ).count()
    return Response({'count': count})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def marquer_notification_lue(request, pk):
    notification = get_object_or_404(
        Notification, pk=pk, destinataire=request.user
    )
    notification.lu = True
    notification.save(update_fields=['lu'])
    return Response(NotificationSerializer(notification).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def marquer_toutes_notifications_lues(request):
    nb = Notification.objects.filter(
        destinataire=request.user, lu=False
    ).update(lu=True)
    return Response({'marquees_lues': nb})