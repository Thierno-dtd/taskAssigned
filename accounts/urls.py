from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, CustomTokenObtainPairView,
    UserProfileView, AgentListView, AgentDetailView
)
from .otp_views import (
    request_otp, verify_otp, resend_otp, verify_otp_and_login
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('agents/', AgentListView.as_view(), name='agent_list'),
    path('agents/<int:pk>/', AgentDetailView.as_view(), name='agent_detail'),
    # OTP Authentication
    path('otp/request/', request_otp, name='otp_request'),
    path('otp/verify/', verify_otp, name='otp_verify'),
    path('otp/resend/', resend_otp, name='otp_resend'),
    path('otp/login/', verify_otp_and_login, name='otp_login'),
]
