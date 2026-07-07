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
        read_only_fields = ['id', 'date_joined']


class AgentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AgentProfile
        fields = [
            'id', 'user', 'matricule',
            'zone_intervention', 'date_embauche'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password',
            'first_name', 'last_name', 'role', 'phone'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
