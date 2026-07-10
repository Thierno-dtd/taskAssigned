from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import AgentProfile
from .permissions import IsAdmin, IsManagerOrAdmin
from .emails import envoyer_identifiants_par_email
from .serializers import (
    UserSerializer, AgentProfileSerializer,
    UserCreateSerializer, ManagerCreateSerializer,
    RoleChangeSerializer, ChangePasswordSerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    Création d'un compte agent. RÉSERVÉ à un manager ou un admin
    authentifié (IsManagerOrAdmin) — il n'y a plus d'auto-inscription
    publique : c'est le manager qui crée les comptes de ses agents.

    Le mot de passe est généré automatiquement et envoyé par email à
    l'agent. Aucun token n'est renvoyé ici (ce n'est pas l'agent qui
    fait la requête, mais le manager qui le crée) — l'agent se
    connectera lui-même ensuite via /login/ avec le mot de passe reçu
    par email, puis devra vérifier son téléphone (OTP) et changer ce
    mot de passe.
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsManagerOrAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        mot_de_passe_temporaire = user._mot_de_passe_temporaire
        email_envoye = envoyer_identifiants_par_email(user, mot_de_passe_temporaire)

        reponse = UserSerializer(user).data
        reponse['email_envoye'] = email_envoye
        # Filet de sécurité si l'email n'a pas pu être envoyé (SMTP en
        # échec, email invalide...) : sans ça, personne ne connaîtrait
        # le mot de passe de ce nouvel agent.
        if not email_envoye:
            reponse['mot_de_passe_temporaire'] = mot_de_passe_temporaire

        return Response(reponse, status=status.HTTP_201_CREATED)


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

        mot_de_passe_temporaire = user._mot_de_passe_temporaire
        email_envoye = envoyer_identifiants_par_email(user, mot_de_passe_temporaire)

        reponse = UserSerializer(user).data
        reponse['email_envoye'] = email_envoye
        if not email_envoye:
            reponse['mot_de_passe_temporaire'] = mot_de_passe_temporaire

        return Response(reponse, status=status.HTTP_201_CREATED)


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


class ChangePasswordView(APIView):
    """
    Changement de mot de passe. Volontairement en dehors du blocage
    global IsFullyVerified (voir settings.py) : déclare explicitement
    permission_classes=[IsAuthenticated] pour rester accessible même à
    un utilisateur dont must_change_password=True — sinon il serait
    bloqué partout sans pouvoir en sortir.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['ancien_mot_de_passe']):
            return Response(
                {'error': "Ancien mot de passe incorrect."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['nouveau_mot_de_passe'])
        user.must_change_password = False
        user.save(update_fields=['password', 'must_change_password'])

        return Response({'message': 'Mot de passe changé avec succès.'})