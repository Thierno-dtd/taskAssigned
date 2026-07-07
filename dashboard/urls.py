from django.urls import path

from .views import (
    statistiques_generales,
    statistiques_par_semaine,
    statistiques_par_agent,
    raisons_non_execution
)

urlpatterns = [
    path('stats/', statistiques_generales, name='stats_generales'),
    path('stats/semaine/<int:semaine_id>/',
         statistiques_par_semaine, name='stats_semaine'),
    path('stats/semaine/',
         statistiques_par_semaine, name='stats_semaine_current'),
    path('stats/agents/', statistiques_par_agent, name='stats_agents'),
    path('stats/raisons/', raisons_non_execution, name='stats_raisons'),
]
