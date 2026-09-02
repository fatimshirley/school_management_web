from django.contrib import admin
from .models import Evaluation, Grade

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'type_evaluation', 'annee_universitaire', 'date')
    list_filter = ('annee_universitaire', 'subject')

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'evaluation', 'note')
    list_filter = ('evaluation__annee_universitaire', 'evaluation__subject')
    search_fields = ('student__nom', 'student__prenom', 'student__matricule')