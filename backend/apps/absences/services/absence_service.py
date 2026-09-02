from datetime import date

from django.core.exceptions import ValidationError

from apps.absences.models import Absence


def enregistrer_absence(
    student,
    evaluation,
    date_absence
):
    """
    Enregistre une absence à une évaluation.
    """

    absence, created = Absence.objects.get_or_create(
        student=student,
        evaluation=evaluation,
        defaults={
            'date_absence': date_absence
        }
    )

    if not created:
        raise ValidationError(
            "Cette absence est déjà enregistrée."
        )

    return absence


def justifier_absence(
    absence,
    justification,
    date_justification=None
):
    """
    Enregistre une justification d'absence.

    La justification doit être déposée pendant
    la période du semestre concerné.
    """

    if date_justification is None:
        date_justification = date.today()

    semestre = absence.evaluation.subject.semestre

    if semestre is None:
        raise ValidationError(
            "Cette matière n'est associée à aucun semestre."
        )

    if semestre.date_debut is None or semestre.date_fin is None:
        raise ValidationError(
            "Les dates du semestre doivent être renseignées."
        )

    if not (
        semestre.date_debut
        <= date_justification
        <= semestre.date_fin
    ):
        raise ValidationError(
            "Le délai de justification du semestre est dépassé."
        )

    absence.justifiee = True
    absence.justification = justification
    absence.date_justification = date_justification

    absence.save(
        update_fields=[
            'justifiee',
            'justification',
            'date_justification'
        ]
    )

    return absence


def enregistrer_rattrapage(
    absence,
    note,
    date_rattrapage=None
):
    """
    Enregistre la note obtenue au rattrapage
    d'une absence justifiée.

    Le rattrapage doit obligatoirement avoir lieu
    pendant la période du semestre.
    """

    if not absence.justifiee:
        raise ValidationError(
            "Un rattrapage n'est possible que pour une absence justifiée."
        )

    if date_rattrapage is None:
        date_rattrapage = date.today()

    if not 0 <= note <= 20:
        raise ValidationError(
            "La note doit être comprise entre 0 et 20."
        )

    semestre = absence.evaluation.subject.semestre

    if semestre is None:
        raise ValidationError(
            "Cette matière n'est associée à aucun semestre."
        )

    if semestre.date_debut is None or semestre.date_fin is None:
        raise ValidationError(
            "Les dates du semestre doivent être renseignées."
        )

    if not (
        semestre.date_debut
        <= date_rattrapage
        <= semestre.date_fin
    ):
        raise ValidationError(
            "Le rattrapage doit être effectué pendant la période du semestre."
        )

    absence.rattrapage_effectue = True
    absence.note_rattrapage = note
    absence.date_rattrapage = date_rattrapage

    absence.save(
        update_fields=[
            'rattrapage_effectue',
            'note_rattrapage',
            'date_rattrapage'
        ]
    )

    return absence