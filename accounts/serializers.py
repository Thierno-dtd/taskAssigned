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
            'date_joined'
        ]
        # 'role' en lecture seule ici : ce serializer est utilisé pour
        # l'auto-édition du profil (UserProfileView.put) et l'affichage.
        # Le rôle ne doit JAMAIS être modifiable par ce biais — seul un
        # admin peut le changer, via ChangeUserRoleView (voir plus bas).
        read_only_fields = ['id', 'date_joined', 'role']


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
    Utilisé pour la création de compte. 'role' est volontairement absent
    des champs éditables : un utilisateur ne doit jamais pouvoir
    s'attribuer lui-même un rôle (admin/manager) à l'inscription.
    Le rôle est forcé côté serveur (voir create()) ou fixé séparément
    par un admin via un endpoint dédié et protégé.
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password',
            'first_name', 'last_name', 'phone'
        ]

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.role = 'agent'  # rôle forcé, jamais fourni par le client
        user.set_password(password)
        user.save()
        return user


class ManagerCreateSerializer(serializers.ModelSerializer):
    """
    Création d'un compte manager. Réservé à l'admin (voir
    ManagerCreateView / permission IsAdmin). Le rôle est forcé à
    'manager' côté serveur, jamais fourni par le client.
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password',
            'first_name', 'last_name', 'phone'
        ]

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.role = 'manager'
        user.set_password(password)
        user.save()
        return user


class RoleChangeSerializer(serializers.Serializer):
    """
    Change le rôle d'un utilisateur existant entre 'agent' et 'manager'
    uniquement. Le rôle 'admin' ne peut jamais être attribué ni retiré
    via cet endpoint : il n'y a qu'un seul admin, fixé à la création
    de son compte (createsuperuser), et il n'est pas censé changer.
    """
    role = serializers.ChoiceField(choices=['agent', 'manager'])


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()