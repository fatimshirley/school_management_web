from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.students.models import Student
from apps.subjects.models import Subject
from apps.academic.models import AnneeUniversitaire


class Evaluation(models.Model):

    TYPE_CHOICES = [
        ('cc1', 'Contrôle continu 1'),
        ('cc2', 'Contrôle continu 2'),
        ('devoir', 'Devoir'),
        ('examen', 'Examen final'),
    ]

    SESSION_CHOICES = [
        (1, 'Session 1'),
        (2, 'Session 2'),
    ]

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='evaluations'
    )

    annee_universitaire = models.ForeignKey(
        AnneeUniversitaire,
        on_delete=models.PROTECT,
        related_name='evaluations'
    )

    type_evaluation = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    session = models.PositiveSmallIntegerField(
        choices=SESSION_CHOICES,
        default=1
    )

    date = models.DateField()

    def __str__(self):
        return (
            f"{self.subject.nom} - "
            f"{self.get_type_evaluation_display()} - "
            f"Session {self.session}"
        )


class Grade(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='grades'
    )

    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name='grades'
    )

    note = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(20)
        ]
    )

    def __str__(self):
        return (
            f"{self.student.matricule} - "
            f"{self.evaluation} - "
            f"{self.note}/20"
        )