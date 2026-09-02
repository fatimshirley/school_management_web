from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'matricule',
        'nom',
        'prenom',
        'age',
        'niveau',
    )

    search_fields = (
        'matricule',
        'nom',
        'prenom',
    )

    list_filter = (
        'niveau',
    )