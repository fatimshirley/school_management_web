from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.students.models import Student
from apps.subjects.models import Subject  # Assurez-vous que le chemin d'import est correct selon votre projet


class Absence(models.Model):

    TYPE_EVALUATION_CHOICES = [
        ('cc1', 'Contrôle continu 1'),
        ('cc2', 'Contrôle continu 2'),
        ('devoir', 'Devoir'),
        ('examen', 'Examen final'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='absences'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='absences',
        null=True,
        blank=True
    )

    type_evaluation = models.CharField(
        max_length=50,
        choices=TYPE_EVALUATION_CHOICES,
        default='cc1'
    )

    date_absence = models.DateField()

    justifiee = models.BooleanField(
        default=False
    )

    justification = models.TextField(
        blank=True,
        null=True
    )

    date_justification = models.DateField(
        blank=True,
        null=True
    )

    rattrapage_effectue = models.BooleanField(
        default=False
    )

    note_rattrapage = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(20)
        ]
    )

    date_rattrapage = models.DateField(
        blank=True,
        null=True
    )

    def __str__(self):
        statut = "Justifiée" if self.justifiee else "Non justifiée"
        return f"{self.student.matricule} - {self.subject.nom} ({self.get_type_evaluation_display()}) - {statut}"