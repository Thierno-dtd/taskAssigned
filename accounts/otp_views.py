import random
import string
from datetime import datetime

from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .throttles import OtpRateThrottle
from .sms import envoyer_sms, SmsSendError

User = get_user_model()

# Configuration OTP
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3


def generate_otp():
    """Génère un code OTP à 6 chiffres."""
    return ''.join(random.choices(string.digits, k=6))


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OtpRateThrottle])
def request_otp(request):
    """
    Demande un code OTP par SMS.
    Body: { "phone": "+24106123456" }
    """
    phone = request.data.get('phone')

    if not phone:
        return Response(
            {'error': 'Numéro de téléphone requis'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Vérifier si l'utilisateur existe
    try:
        user = User.objects.get(phone=phone, role='agent')
    except User.DoesNotExist:
        return Response(
            {'error': 'Aucun agent trouvé avec ce numéro'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Vérifier le rate limiting
    cache_key_attempts = f"otp_attempts_{phone}"
    attempts = cache.get(cache_key_attempts, 0)
    if attempts >= MAX_OTP_ATTEMPTS:
        return Response(
            {
                'error': 'Trop de tentatives. '
                         'Veuillez réessayer dans 15 minutes.'
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    # Générer et stocker l'OTP
    otp_code = generate_otp()
    cache_key = f"otp_{phone}"
    cache.set(cache_key, {
        'code': otp_code,
        'user_id': user.id,
        'created_at': datetime.now().isoformat()
    }, timeout=60 * OTP_EXPIRY_MINUTES)

    # Incrémenter les tentatives
    cache.set(cache_key_attempts, attempts + 1, timeout=900)  # 15 min

    # Envoi du SMS (réel si un fournisseur est configuré, simulé sinon)
    try:
        envoyer_sms(phone, f"Votre code SEEG : {otp_code} (valable {OTP_EXPIRY_MINUTES} min)")
    except SmsSendError:
        # On ne bloque pas l'utilisateur pour une raison qui ne dépend pas
        # de lui, mais on l'informe que le SMS n'est peut-être pas arrivé.
        return Response(
            {'error': "Le service SMS est momentanément indisponible. Réessayez dans quelques instants."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return Response({
        'message': 'Code OTP envoyé avec succès',
        'phone': phone,
        'expires_in': f"{OTP_EXPIRY_MINUTES} minutes"
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OtpRateThrottle])
def verify_otp(request):
    """
    Vérifie le code OTP et retourne les tokens JWT.
    Body: { "phone": "+24106123456", "otp": "123456" }
    """
    phone = request.data.get('phone')
    otp_code = request.data.get('otp')

    if not phone or not otp_code:
        return Response(
            {'error': 'Numéro de téléphone et code OTP requis'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Récupérer l'OTP stocké
    cache_key = f"otp_{phone}"
    otp_data = cache.get(cache_key)

    if not otp_data:
        return Response(
            {'error': 'Code OTP expiré ou invalide'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Vérifier le code
    if otp_data['code'] != otp_code:
        return Response(
            {'error': 'Code OTP incorrect'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Récupérer l'utilisateur
    try:
        user = User.objects.get(id=otp_data['user_id'])
    except User.DoesNotExist:
        return Response(
            {'error': 'Utilisateur non trouvé'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Supprimer l'OTP utilisé
    cache.delete(cache_key)
    cache.delete(f"otp_attempts_{phone}")

    # Générer les tokens JWT
    refresh = RefreshToken.for_user(user)

    return Response({
        'message': 'Authentification réussie',
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
        'user': {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'phone': user.phone
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([OtpRateThrottle])
def resend_otp(request):
    """
    Renvoie un nouveau code OTP.
    """
    user = request.user

    if not user.phone:
        return Response(
            {'error': 'Utilisateur sans numéro de téléphone'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Réinitialiser les tentatives
    cache.delete(f"otp_attempts_{user.phone}")

    # Appeler la fonction request_otp avec le phone de l'utilisateur
    request.data['phone'] = user.phone
    return request_otp(request)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([OtpRateThrottle])
def verify_otp_and_login(request):
    """
    Vérifie OTP et met à jour le statut de l'agent.
    """
    response = verify_otp(request)

    if response.status_code == 200:
        # Marquer l'agent comme actif
        user_id = response.data['user']['id']
        User.objects.filter(id=user_id).update(is_active_agent=True)

    return response