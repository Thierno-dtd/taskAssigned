from django.urls import path

from .views import (
    statistiques_generales,
    statistiques_par_semaine,
    stats_evolution,
    statistiques_par_agent,
    stats_agent_evolution,
    raisons_non_execution,
    stats_priorites,
)

urlpatterns = [
    path('stats/', statistiques_generales, name='stats_generales'),
    path('stats/evolution/', stats_evolution, name='stats_evolution'),

    path('stats/semaine/<int:semaine_id>/',
         statistiques_par_semaine, name='stats_semaine'),
    path('stats/semaine/',
         statistiques_par_semaine, name='stats_semaine_current'),

    path('stats/agents/', statistiques_par_agent, name='stats_agents'),
    path('stats/agents/<int:agent_id>/evolution/',
         stats_agent_evolution, name='stats_agent_evolution'),

    path('stats/raisons/', raisons_non_execution, name='stats_raisons'),
    path('stats/priorites/', stats_priorites, name='stats_priorites'),
]