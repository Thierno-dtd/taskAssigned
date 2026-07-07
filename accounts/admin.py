from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, AgentProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'first_name', 'last_name', 'role',
        'phone', 'is_active_agent', 'is_active', 'date_joined'
    )
    list_filter = ('role', 'is_active_agent', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'phone', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('Informations SEEG', {'fields': ('role', 'phone', 'is_active_agent')}),
    )


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'user', 'zone_intervention', 'date_embauche')
    search_fields = ('matricule', 'user__username', 'user__first_name', 'user__last_name')
    list_filter = ('zone_intervention',)
    autocomplete_fields = ('user',)