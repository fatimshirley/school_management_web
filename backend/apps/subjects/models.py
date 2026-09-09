from django.db import models

from apps.teachers.models import Teacher
from apps.academic.models import Semestre, Filiere


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


class Enseignement(models.Model):

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='enseignements'
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='enseignements'
    )

    semestre = models.ForeignKey(
        Semestre,
        on_delete=models.PROTECT,
        related_name='enseignements'
    )

    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.PROTECT,
        related_name='enseignements'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'subject',
                    'teacher',
                    'semestre',
                    'filiere',
                ],
                name='unique_subject_teacher_semestre_filiere'
            )
        ]

        ordering = [
            'subject__nom',
            'semestre__niveau__code',
            'filiere__code',
            'teacher__nom',
        ]

    def __str__(self):
        return (
            f"{self.subject.nom} — "
            f"{self.semestre.niveau.code} — "
            f"{self.filiere.code} — "
            f"{self.teacher.nom} {self.teacher.prenom}"
        )