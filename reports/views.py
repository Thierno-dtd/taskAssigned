from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import RapportExecution
from .serializers import RapportExecutionSerializer


class RapportListCreateView(generics.ListCreateAPIView):
    queryset = RapportExecution.objects.all()
    serializer_class = RapportExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tache', 'sous_tache', 'type_rapport', 'agent']
    ordering_fields = ['date_soumission']

    def get_queryset(self):
        queryset = RapportExecution.objects.all()
        user = self.request.user

        # Agents ne voient que leurs propres rapports
        if user.role == 'agent':
            queryset = queryset.filter(agent=user)

        return queryset.select_related('tache', 'sous_tache', 'agent')


class RapportDetailView(generics.RetrieveAPIView):
    queryset = RapportExecution.objects.all()
    serializer_class = RapportExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = RapportExecution.objects.all()
        user = self.request.user

        if user.role == 'agent':
            queryset = queryset.filter(agent=user)

        return queryset.select_related('tache', 'sous_tache', 'agent')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def soumettre_rapport(request):
    """Endpoint simplifié pour soumettre un rapport d'exécution."""
    serializer = RapportExecutionSerializer(
        data=request.data, context={'request': request}
    )
    if serializer.is_valid():
        rapport = serializer.save()
        return Response({
            'message': 'Rapport soumis avec succès',
            'rapport': RapportExecutionSerializer(rapport).data
        })
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def mes_rapports(request):
    """Rapports de l'agent connecté."""
    rapports = RapportExecution.objects.filter(agent=request.user)
    serializer = RapportExecutionSerializer(rapports, many=True)
    return Response(serializer.data)

