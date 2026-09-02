from datetime import date

from django.core.exceptions import ValidationError

from apps.grades.models import Grade, Evaluation
from apps.absences.models import Absence


def get_evaluations_continues(subject):
    """
    Retourne les évaluations de contrôle continu
    effectivement prévues pour une matière en session 1.

    CC1, CC2 et Devoir sont concernés.
    """

    return Evaluation.objects.filter(
        subject=subject,
        session=1,
        type_evaluation__in=['cc1', 'cc2', 'devoir']
    ).order_by('date')


def get_note_evaluation(student, evaluation):
    """
    Retourne la note d'un étudiant pour une évaluation.

    Cas possibles :
    - note normale → retourne la note
    - absence injustifiée → retourne 0
    - absence justifiée avec rattrapage effectué
      pendant la période du semestre → retourne la note du rattrapage
    - absence justifiée sans rattrapage alors que le semestre
      est encore en cours → retourne None
    - absence justifiée sans rattrapage après la fin du semestre
      → retourne 0
    """

    # Vérifier d'abord si une note normale existe
    try:
        grade = Grade.objects.get(
            student=student,
            evaluation=evaluation
        )

        return grade.note

    except Grade.DoesNotExist:
        pass

    # Vérifier ensuite s'il existe une absence
    try:
        absence = Absence.objects.get(
            student=student,
            evaluation=evaluation
        )

    except Absence.DoesNotExist:
        return None

    # Absence non justifiée → 0
    if not absence.justifiee:
        return 0

    # Absence justifiée + rattrapage effectué
    if (
        absence.rattrapage_effectue
        and absence.note_rattrapage is not None
    ):
        return absence.note_rattrapage

    # Récupérer le semestre de la matière
    semestre = evaluation.subject.semestre

    # Si la matière n'est associée à aucun semestre,
    # on ne peut pas déterminer la période du rattrapage.
    if semestre is None:
        return None

    # Si la date de fin du semestre n'est pas définie,
    # on ne peut pas déterminer si le délai est dépassé.
    if semestre.date_fin is None:
        return None

    # Si le semestre est terminé et que le rattrapage
    # n'a pas été effectué → 0
    if date.today() > semestre.date_fin:
        return 0

    # Le semestre est toujours en cours.
    # L'étudiant peut encore effectuer son rattrapage.
    return None


def calculer_continu(student, subject):
    """
    Calcule la moyenne de la composante continue.

    CC1, CC2 et Devoir représentent ensemble les 40 %.

    Si une seule de ces évaluations a été organisée,
    cette évaluation représente toute la composante des 40 %.

    Si plusieurs évaluations ont été organisées,
    leur moyenne représente la composante des 40 %.

    Si une note est encore en attente parce qu'un rattrapage
    peut encore être effectué, la moyenne n'est pas calculée.
    """

    evaluations = get_evaluations_continues(subject)

    if not evaluations.exists():
        raise ValidationError(
            "Aucune évaluation continue n'a été enregistrée."
        )

    notes = []

    for evaluation in evaluations:

        note = get_note_evaluation(
            student,
            evaluation
        )

        # Une note None signifie que la note est encore
        # en attente d'un rattrapage ou qu'elle ne peut
        # pas encore être déterminée.
        if note is None:
            return None

        notes.append(float(note))

    return sum(notes) / len(notes)


def calculer_composante_40(student, subject):
    """
    Transforme la moyenne du contrôle continu
    en composante représentant 40 % de la note finale.
    """

    moyenne_continu = calculer_continu(
        student,
        subject
    )

    if moyenne_continu is None:
        return None

    return moyenne_continu * 0.40


def get_examen(student, subject):
    """
    Retourne la note de l'examen final de la session 1.
    """

    try:
        evaluation = Evaluation.objects.get(
            subject=subject,
            session=1,
            type_evaluation='examen'
        )

    except Evaluation.DoesNotExist:
        raise ValidationError(
            "Aucun examen final n'a été enregistré pour cette matière."
        )

    note = get_note_evaluation(
        student,
        evaluation
    )

    return note


def calculer_composante_60(student, subject):
    """
    Calcule la composante examen qui représente 60 %.
    """

    note_examen = get_examen(
        student,
        subject
    )

    if note_examen is None:
        return None

    return float(note_examen) * 0.60


def calculer_moyenne_finale(student, subject):
    """
    Calcule la moyenne finale de la matière.

    40 % = contrôle continu
    60 % = examen final

    Si une des deux composantes est encore en attente,
    la moyenne finale n'est pas encore calculée.
    """

    composante_40 = calculer_composante_40(
        student,
        subject
    )

    composante_60 = calculer_composante_60(
        student,
        subject
    )

    if composante_40 is None or composante_60 is None:
        return None

    return composante_40 + composante_60


def matiere_validee(student, subject):

    moyenne = obtenir_moyenne_finale_retenue(
        student,
        subject
    )

    if moyenne is None:
        return False

    return moyenne >= 10


def doit_passer_session_2(student, subject):
    """
    La Session 2 est possible lorsque la moyenne
    finale de la matière est inférieure à 10/20.

    Si la moyenne n'est pas encore disponible,
    la Session 2 n'est pas encore déterminée.
    """

    moyenne = calculer_moyenne_finale(
        student,
        subject
    )

    if moyenne is None:
        return False

    return moyenne < 10



def get_examen_session_2(subject):
    """
    Retourne l'examen final de la Session 2
    pour une matière.
    """

    try:
        return Evaluation.objects.get(
            subject=subject,
            session=2,
            type_evaluation='examen'
        )

    except Evaluation.DoesNotExist:
        raise ValidationError(
            "Aucun examen de Session 2 n'a été enregistré "
            "pour cette matière."
        )


def get_note_examen_session_2(student, subject):
    """
    Retourne la note de l'examen de Session 2.

    La note de Session 1 n'est jamais modifiée.
    """

    evaluation = get_examen_session_2(subject)

    note = get_note_evaluation(
        student,
        evaluation
    )

    return note


def calculer_moyenne_session_2(student, subject):
    """
    Calcule la moyenne finale de Session 2.

    Le contrôle continu de Session 1 est conservé
    et représente toujours 40 %.

    Seul l'examen est repris et représente 60 %.
    """

    moyenne_continu = calculer_continu(
        student,
        subject
    )

    if moyenne_continu is None:
        return None

    note_examen = get_note_examen_session_2(
        student,
        subject
    )

    if note_examen is None:
        return None

    composante_40 = float(moyenne_continu) * 0.40
    composante_60 = float(note_examen) * 0.60

    return composante_40 + composante_60


def matiere_validee_session_2(student, subject):
    """
    Vérifie si la matière est validée en Session 2.

    La matière est validée si la moyenne Session 2
    est supérieure ou égale à 10/20.
    """

    moyenne = calculer_moyenne_session_2(
        student,
        subject
    )

    if moyenne is None:
        return False

    return moyenne >= 10


def doit_passer_session_2(student, subject):
    """
    Vérifie si l'étudiant doit passer la Session 2.

    La Session 2 est nécessaire lorsque la moyenne
    de Session 1 est inférieure à 10/20.
    """

    moyenne = calculer_moyenne_finale(
        student,
        subject
    )

    if moyenne is None:
        return False

    return moyenne < 10




def obtenir_moyenne_finale_retenue(student, subject):
    """
    Retourne la moyenne finale retenue pour une matière.

    Règles :

    - Si la Session 1 est >= 10/20 :
        la moyenne de Session 1 est retenue.

    - Si la Session 1 est < 10/20 :
        la Session 2 est nécessaire.

    - Si l'examen de Session 2 n'est pas encore disponible :
        retourne None.

    - Si l'examen de Session 2 est disponible :
        la moyenne Session 2 est retenue.

    Les anciennes notes restent conservées dans l'historique.
    """

    moyenne_session_1 = calculer_moyenne_finale(
        student,
        subject
    )

    if moyenne_session_1 is None:
        return None

    # La matière est déjà validée en Session 1.
    if moyenne_session_1 >= 10:
        return moyenne_session_1

    # Session 1 < 10 → on regarde la Session 2.
    try:
        moyenne_session_2 = calculer_moyenne_session_2(
            student,
            subject
        )

    except ValidationError:
        # Aucun examen Session 2 n'a encore été enregistré.
        return moyenne_session_1

    if moyenne_session_2 is None:
        return moyenne_session_1

    return moyenne_session_2