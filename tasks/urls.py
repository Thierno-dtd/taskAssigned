from django.urls import path

from .views import (
    SemaineListCreateView, SemaineDetailView,
    TacheListCreateView, TacheDetailView,
    SousTacheListCreateView, SousTacheDetailView,
    mes_taches, taches_par_semaine,
    ImportLotListView, ImportLotDetailView,
    NotificationListView, notifications_non_lues_count,
    marquer_notification_lue, marquer_toutes_notifications_lues
)
from .excel_views import (
    export_tasks_excel, export_agents_excel, import_tasks_excel,
    analyser_fichier_excel, confirmer_import_excel
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
    path('import/excel/analyser/', analyser_fichier_excel, name='import_excel_analyser'),
    path('import/excel/confirmer/', confirmer_import_excel, name='import_excel_confirmer'),
    path('import/lots/', ImportLotListView.as_view(), name='import_lot_list'),
    path('import/lots/<int:pk>/', ImportLotDetailView.as_view(), name='import_lot_detail'),
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/non-lues/count/', notifications_non_lues_count, name='notifications_count'),
    path('notifications/<int:pk>/marquer-lue/', marquer_notification_lue, name='notification_marquer_lue'),
    path('notifications/tout-marquer-lu/', marquer_toutes_notifications_lues, name='notifications_tout_marquer_lu'),

    # Carte GPS
    path('map/taches/', map_tasks_data, name='map_tasks'),
    path('map/proches/', nearby_tasks, name='nearby_tasks'),
    path('agents/tracking/', agent_tracking_data, name='agent_tracking'),
    path('taches/<int:task_id>/localisation/', update_task_location, name='update_location'),
]