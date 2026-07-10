from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, CustomTokenObtainPairView,
    UserProfileView, AgentListView, AgentDetailView,
    ManagerCreateView, ChangeUserRoleView, ChangePasswordView
)
from .otp_views import (
    request_otp, verify_otp, resend_otp, verify_otp_and_login,
    request_phone_verification, verify_phone
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('agents/', AgentListView.as_view(), name='agent_list'),
    path('agents/<int:pk>/', AgentDetailView.as_view(), name='agent_detail'),

    # Gestion des rôles — réservé à l'admin
    path('admin/managers/', ManagerCreateView.as_view(), name='create_manager'),
    path('admin/users/<int:pk>/role/', ChangeUserRoleView.as_view(), name='change_user_role'),

    # OTP Authentication (connexion alternative par téléphone)
    path('otp/request/', request_otp, name='otp_request'),
    path('otp/verify/', verify_otp, name='otp_verify'),
    path('otp/resend/', resend_otp, name='otp_resend'),
    path('otp/login/', verify_otp_and_login, name='otp_login'),

    # Vérification du téléphone à la première connexion (utilisateur déjà authentifié)
    path('phone/verifier/', verify_phone, name='phone_verify'),
    path('phone/renvoyer/', request_phone_verification, name='phone_verify_resend'),
]