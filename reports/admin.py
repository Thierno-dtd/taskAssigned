from django.contrib import admin

from .models import RapportExecution


@admin.register(RapportExecution)
class RapportExecutionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'agent', 'tache', 'type_rapport',
        'categorie_raison', 'date_soumission'
    )
    list_filter = ('type_rapport', 'categorie_raison', 'date_soumission')
    search_fields = ('agent__username', 'agent__first_name', 'agent__last_name', 'tache__titre')
    autocomplete_fields = ('agent', 'tache', 'sous_tache')
    readonly_fields = ('date_soumission',)