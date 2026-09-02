from django.contrib.auth.models import User
from django.db import models


class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    identifiant = models.CharField(
        max_length=20,
        unique=True
    )

    nom = models.CharField(
        max_length=100
    )

    prenom = models.CharField(
       max_length=100,
       null=True,
       blank=True
    )

    def __str__(self):
        return f"{self.identifiant} - {self.nom} {self.prenom}"