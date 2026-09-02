from django.contrib.auth.models import User
from django.db import models
from apps.academic.models import Niveau


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    matricule = models.CharField(
        max_length=20,
        unique=True
    )

    nom = models.CharField(
        max_length=100
    )

    prenom = models.CharField(
        max_length=100
    )

    age = models.PositiveIntegerField()

    niveau = models.ForeignKey(
        Niveau,
        on_delete=models.PROTECT,
        related_name='students',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenom}"