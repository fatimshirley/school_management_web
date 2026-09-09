from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.students.models import Student
from apps.subjects.models import Subject


class Absence(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='absences'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='absences'
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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'student',
                    'subject',
                    'date_absence',
                ],
                name='unique_student_subject_absence_date'
            )
        ]

    def __str__(self):
        statut = (
            "Justifiée"
            if self.justifiee
            else "Non justifiée"
        )

        return (
            f"{self.student.matricule} - "
            f"{self.subject.nom} - "
            f"{self.date_absence} - "
            f"{statut}"
        )