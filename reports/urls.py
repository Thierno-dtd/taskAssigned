from django.urls import path

from .views import (
    RapportListCreateView, RapportDetailView,
    soumettre_rapport, mes_rapports
)

urlpatterns = [
    path('rapports/', RapportListCreateView.as_view(), name='rapport_list'),
    path('rapports/<int:pk>/', RapportDetailView.as_view(),
         name='rapport_detail'),
    path('soumettre/', soumettre_rapport, name='soumettre_rapport'),
    path('mes-rapports/', mes_rapports, name='mes_rapports'),
]
