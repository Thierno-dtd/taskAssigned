from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import AgentProfile
from .permissions import IsAdmin
from .serializers import (
    UserSerializer, AgentProfileSerializer,
    UserCreateSerializer, ManagerCreateSerializer,
    RoleChangeSerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data['username'])
            response.data['user'] = UserSerializer(user).data
        return response


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AgentListView(generics.ListAPIView):
    queryset = User.objects.filter(role='agent')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class AgentDetailView(generics.RetrieveAPIView):
    queryset = AgentProfile.objects.all()
    serializer_class = AgentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


class ManagerCreateView(generics.CreateAPIView):
    """
    Création d'un compte manager. Réservé à l'admin : c'est le seul
    rôle habilité à créer des managers (voir IsAdmin).
    """
    queryset = User.objects.all()
    serializer_class = ManagerCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class ChangeUserRoleView(APIView):
    """
    Change le rôle d'un utilisateur entre 'agent' et 'manager'.
    Réservé à l'admin. Fait office à la fois de "promotion" (agent ->
    manager) et de "révocation" (manager -> agent) : un seul endpoint,
    le rôle cible est passé dans le body.

    Le rôle 'admin' est intouchable ici : on ne peut ni le retirer à
    l'admin en poste, ni l'attribuer à quelqu'un d'autre par cette
    route (il n'y a qu'un seul admin, créé via createsuperuser).
    """
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        if user.role == 'admin':
            return Response(
                {'error': "Le rôle d'un compte admin ne peut pas être modifié via cette route."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RoleChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.role = serializer.validated_data['role']
        user.save(update_fields=['role'])

        return Response(UserSerializer(user).data)