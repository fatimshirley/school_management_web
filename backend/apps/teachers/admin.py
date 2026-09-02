from django.contrib import admin
from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        'identifiant',
        'nom',
        'prenom',
    )

    search_fields = (
        'identifiant',
        'nom',
        'prenom',
    )