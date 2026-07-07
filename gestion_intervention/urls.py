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


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/health/', health_check, name='health_check'),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(), name='docs'),

    # API Endpoints
    path('api/auth/', include('accounts.urls')),
    path('api/', include('tasks.urls')),
    path('api/', include('reports.urls')),
    path('api/', include('dashboard.urls')),
]

# Media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )