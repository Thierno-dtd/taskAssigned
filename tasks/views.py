from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from .models import Semaine, Tache, SousTache
from .serializers import (
    SemaineSerializer, TacheListSerializer,
    TacheDetailSerializer, TacheCreateUpdateSerializer,
    SousTacheSerializer
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
    permission_classes = [permissions.IsAuthenticated]
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
        tache = Tache.objects.get(id=tache_id)
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
    serializer = TacheListSerializer(taches, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def taches_par_semaine(request, semaine_id):
    """Filtrer les tâches par semaine."""
    taches = Tache.objects.filter(semaine_id=semaine_id)

    if request.user.role == 'agent':
        taches = taches.filter(assigne_a=request.user)

    serializer = TacheListSerializer(taches, many=True)
    return Response(serializer.data)

