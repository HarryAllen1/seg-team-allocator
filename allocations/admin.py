from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Team, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = list(UserAdmin.fieldsets or ()) + [
        ('Allocation profile', {'fields': ('gender', 'ethnicity', 'c_score', 'committed', 'workload')}),
    ]
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Allocation profile', {'fields': ('gender', 'ethnicity', 'c_score', 'committed', 'workload')}),
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('members',)
