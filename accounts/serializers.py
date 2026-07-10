from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AgentProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(
        source='get_role_display', read_only=True
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'phone', 'is_active_agent',
            'must_change_password', 'phone_verifie', 'date_joined'
        ]
        # 'role', 'must_change_password' et 'phone_verifie' en lecture
        # seule ici : ce serializer sert à l'auto-édition du profil
        # (UserProfileView.put) et à l'affichage. Aucun des trois ne
        # doit être modifiable par ce biais :
        # - role -> ChangeUserRoleView (admin uniquement)
        # - must_change_password -> ChangePasswordView (après vérif de
        #   l'ancien mot de passe)
        # - phone_verifie -> verify_phone (après vérif du code OTP)
        read_only_fields = [
            'id', 'date_joined', 'role',
            'must_change_password', 'phone_verifie'
        ]


class AgentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AgentProfile
        fields = [
            'id', 'user', 'matricule',
            'zone_intervention', 'date_embauche'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Création d'un compte agent PAR UN MANAGER OU UN ADMIN (voir
    permission IsManagerOrAdmin sur RegisterView) — il n'y a plus
    d'auto-inscription publique.

    Pas de champ 'password' : le mot de passe est généré
    automatiquement côté serveur et envoyé par email (voir
    RegisterView.create()). 'email' et 'phone' sont obligatoires : le
    premier pour recevoir le mot de passe temporaire, le second pour la
    vérification OTP à la première connexion.

    'role' est volontairement absent des champs éditables : forcé à
    'agent' côté serveur (voir create()).
    """
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name', 'phone'
        ]

    def create(self, validated_data):
        import secrets
        mot_de_passe_temporaire = secrets.token_urlsafe(8)

        user = User(**validated_data)
        user.role = 'agent'  # rôle forcé, jamais fourni par le client
        user.must_change_password = True
        user.phone_verifie = False
        user.set_password(mot_de_passe_temporaire)
        user.save()

        # Attaché temporairement à l'instance (pas en base) pour que la
        # vue puisse l'envoyer par email et, en secours, le renvoyer une
        # fois dans la réponse API si l'envoi échoue.
        user._mot_de_passe_temporaire = mot_de_passe_temporaire
        return user


class ManagerCreateSerializer(serializers.ModelSerializer):
    """
    Création d'un compte manager par l'admin (voir ManagerCreateView /
    permission IsAdmin). Même logique que UserCreateSerializer : pas de
    mot de passe saisi, généré et envoyé par email. Rôle forcé à
    'manager' côté serveur.
    """
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name', 'phone'
        ]

    def create(self, validated_data):
        import secrets
        mot_de_passe_temporaire = secrets.token_urlsafe(8)

        user = User(**validated_data)
        user.role = 'manager'
        user.must_change_password = True
        user.phone_verifie = False
        user.set_password(mot_de_passe_temporaire)
        user.save()

        user._mot_de_passe_temporaire = mot_de_passe_temporaire
        return user


class RoleChangeSerializer(serializers.Serializer):
    """
    Change le rôle d'un utilisateur existant entre 'agent' et 'manager'
    uniquement. Le rôle 'admin' ne peut jamais être attribué ni retiré
    via cet endpoint : il n'y a qu'un seul admin, fixé à la création
    de son compte (createsuperuser), et il n'est pas censé changer.
    """
    role = serializers.ChoiceField(choices=['agent', 'manager'])


class ChangePasswordSerializer(serializers.Serializer):
    """
    Changement de mot de passe. L'ancien mot de passe est toujours requis
    (même à la première connexion : l'utilisateur le connaît, c'est
    celui reçu par email), pour éviter qu'une session volée suffise à
    changer le mot de passe sans le connaître.
    """
    ancien_mot_de_passe = serializers.CharField(write_only=True)
    nouveau_mot_de_passe = serializers.CharField(write_only=True)

    def validate_nouveau_mot_de_passe(self, value):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()