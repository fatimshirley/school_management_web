from django.db import models
from apps.teachers.models import Teacher
from apps.academic.models import Semestre


class Subject(models.Model):

    nom = models.CharField(
        max_length=100,
        unique=True
    )

    credits = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    semestre = models.ForeignKey(
        Semestre,
        on_delete=models.CASCADE,
        related_name='subjects',
        null=True,
        blank=True
    )

    teachers = models.ManyToManyField(
        Teacher,
        blank=True,
        related_name='subjects'
    )

    def __str__(self):
        return self.nom