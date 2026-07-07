from django.contrib import admin

from .models import Semaine, Tache, SousTache, ImportLot, Notification


class SousTacheInline(admin.TabularInline):
    model = SousTache
    extra = 0


@admin.register(Semaine)
class SemaineAdmin(admin.ModelAdmin):
    list_display = ('numero', 'annee', 'date_debut', 'date_fin', 'is_active')
    list_filter = ('annee', 'is_active')
    search_fields = ('numero', 'annee')
    ordering = ('-annee', '-numero')


@admin.register(Tache)
class TacheAdmin(admin.ModelAdmin):
    list_display = (
        'titre', 'assigne_a', 'semaine', 'status',
        'priorite', 'date_creation', 'lot_import'
    )
    list_filter = ('status', 'priorite', 'semaine')
    search_fields = ('titre', 'description', 'assigne_a__username', 'assigne_a__first_name', 'assigne_a__last_name')
    autocomplete_fields = ('assigne_a', 'created_by', 'semaine')
    inlines = [SousTacheInline]
    readonly_fields = ('date_creation', 'date_modification')


@admin.register(SousTache)
class SousTacheAdmin(admin.ModelAdmin):
    list_display = ('titre', 'tache', 'status', 'ordre')
    list_filter = ('status',)
    search_fields = ('titre', 'tache__titre')


@admin.register(ImportLot)
class ImportLotAdmin(admin.ModelAdmin):
    list_display = (
        'nom_fichier', 'semaine', 'importe_par',
        'date_import', 'nombre_taches_creees', 'nombre_erreurs'
    )
    list_filter = ('semaine',)
    readonly_fields = (
        'nom_fichier', 'semaine', 'importe_par', 'toutes_colonnes',
        'colonnes_obligatoires', 'colonnes_visibles_mobile', 'mapping',
        'date_import', 'nombre_taches_creees', 'nombre_erreurs'
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('destinataire', 'type_notification', 'message', 'lu', 'date_creation')
    list_filter = ('type_notification', 'lu')
    search_fields = ('destinataire__username', 'message')