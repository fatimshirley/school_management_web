from django import forms
from .models import Filiere, Niveau, Semestre, AnneeUniversitaire, Arriere

class FiliereForm(forms.ModelForm):
    class Meta:
        model = Filiere
        fields = ['code', 'nom', 'niveaux']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'grades-form-input', 'placeholder': 'Ex: IDA'}),
            'nom': forms.TextInput(attrs={'class': 'grades-form-input', 'placeholder': 'Ex: Informatique Développeur d\'Applications'}),
            'niveaux': forms.SelectMultiple(attrs={'class': 'grades-form-select'}),
        }

class NiveauForm(forms.ModelForm):
    class Meta:
        model = Niveau
        fields = ['code', 'nom']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'grades-form-input', 'placeholder': 'Ex: L1'}),
            'nom': forms.TextInput(attrs={'class': 'grades-form-input', 'placeholder': 'Ex: Licence 1'}),
        }

class SemestreForm(forms.ModelForm):
    class Meta:
        model = Semestre
        fields = ['nom', 'niveau', 'date_debut', 'date_fin']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'grades-form-input', 'placeholder': 'Ex: Semestre 1'}),
            'niveau': forms.Select(attrs={'class': 'grades-form-select'}),
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'grades-form-input'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'grades-form-input'}),
        }

class AnneeUniversitaireForm(forms.ModelForm):
    class Meta:
        model = AnneeUniversitaire
        fields = ['libelle', 'active']
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'grades-form-input', 'placeholder': 'Ex: 2025-2026'}),
            'active': forms.CheckboxInput(attrs={'class': 'grades-form-checkbox'}),
        }

class ArriereForm(forms.ModelForm):
    class Meta:
        model = Arriere
        fields = ['progression', 'subject', 'credits', 'statut', 'date_validation']
        widgets = {
            'progression': forms.Select(attrs={'class': 'grades-form-select'}),
            'subject': forms.Select(attrs={'class': 'grades-form-select'}),
            'credits': forms.NumberInput(attrs={'class': 'grades-form-input', 'min': 1}),
            'statut': forms.Select(attrs={'class': 'grades-form-select'}),
            'date_validation': forms.DateInput(attrs={'type': 'date', 'class': 'grades-form-input'}),
        }