from django.contrib import admin
from .models import Filiere, Niveau, Semestre, AnneeUniversitaire


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom')
    search_fields = ('code', 'nom')


@admin.register(Niveau)
class NiveauAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    filter_horizontal = ('filieres',)
    search_fields = ('nom',)


@admin.register(Semestre)
class SemestreAdmin(admin.ModelAdmin):
    list_display = ('nom', 'niveau')
    list_filter = ('niveau',)


@admin.register(AnneeUniversitaire)
class AnneeUniversitaireAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'active')
    list_filter = ('active',)