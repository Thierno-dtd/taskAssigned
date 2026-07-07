from django.urls import path

from .views import (
    SemaineListCreateView, SemaineDetailView,
    TacheListCreateView, TacheDetailView,
    SousTacheListCreateView, SousTacheDetailView,
    mes_taches, taches_par_semaine
)
from .excel_views import (
    export_tasks_excel, export_agents_excel, import_tasks_excel
)
from .gps_views import (
    map_tasks_data, agent_tracking_data, update_task_location, nearby_tasks
)

urlpatterns = [
    # Semaines
    path('semaines/', SemaineListCreateView.as_view(),
         name='semaine_list'),
    path('semaines/<int:pk>/', SemaineDetailView.as_view(),
         name='semaine_detail'),

    # Tâches
    path('taches/', TacheListCreateView.as_view(), name='tache_list'),
    path('taches/<int:pk>/', TacheDetailView.as_view(), name='tache_detail'),
    path('mes-taches/', mes_taches, name='mes_taches'),
    path('semaines/<int:semaine_id>/taches/',
         taches_par_semaine, name='taches_par_semaine'),

    # Sous-tâches
    path('taches/<int:tache_id>/sous-taches/',
         SousTacheListCreateView.as_view(), name='sous_tache_list'),
    path('sous-taches/<int:pk>/',
         SousTacheDetailView.as_view(), name='sous_tache_detail'),

    # Export/Import Excel
    path('export/taches/', export_tasks_excel, name='export_tasks'),
    path('export/agents/', export_agents_excel, name='export_agents'),
    path('import/taches/', import_tasks_excel, name='import_tasks'),

    # Carte GPS
    path('map/taches/', map_tasks_data, name='map_tasks'),
    path('map/proches/', nearby_tasks, name='nearby_tasks'),
    path('agents/tracking/', agent_tracking_data, name='agent_tracking'),
    path('taches/<int:task_id>/localisation/', update_task_location, name='update_location'),
]
