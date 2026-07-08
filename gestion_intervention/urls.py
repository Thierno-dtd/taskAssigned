"""
URL configuration for gestion_intervention project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.db import connection
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health_check(request):
    """
    Endpoint de santé : vérifie que l'API répond et que la base de données
    est joignable. Utile pour le monitoring et pour que le front web
    (React) puisse détecter si le backend est indisponible.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        db_ok = True
    except Exception:
        db_ok = False

    status_code = 200 if db_ok else 503
    return JsonResponse(
        {'status': 'ok' if db_ok else 'degraded', 'database': db_ok},
        status=status_code
    )


api_endpoints = [
    path('auth/', include('accounts.urls')),
    path('', include('tasks.urls')),
    path('', include('reports.urls')),
    path('', include('dashboard.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/health/', health_check, name='health_check'),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(), name='docs'),

    # API versionnée (canonique) : c'est CE préfixe que le web React et
    # l'app Android doivent utiliser (le mobile a déjà API_VERSION="v1"
    # dans son build.gradle.kts, il ne restait qu'à l'exposer côté Django).
    path('api/v1/', include(api_endpoints)),

    # Alias non versionné, conservé pour compatibilité avec les scripts/
    # exemples existants (README, API_GUIDE). À retirer une fois que tout
    # le monde consomme /api/v1/.
    #path('api/', include(api_endpoints)),
]

# Media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )