from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.academic.models import (
    Niveau,
    Progression,
    Arriere,
    AnneeUniversitaire,
)

from apps.academic.services.academic_service import (
    calculer_credits_annee,
    get_matieres_non_validees,
    peut_passer_niveau,
    peut_obtenir_licence,
    peut_obtenir_master,
)

from apps.grades.services.grade_service import (
    obtenir_moyenne_finale_retenue,
)


def verifier_passage(student):
    """
    Vérifie si l'étudiant peut passer au niveau suivant.

    Cette fonction ne modifie aucune donnée.
    Elle retourne uniquement la situation du passage.
    """

    niveau_actuel = student.niveau

    if niveau_actuel is None:
        raise ValidationError(
            "L'étudiant n'a aucun niveau associé."
        )

    code = niveau_actuel.code

    progression = {
        'L1': 'L2',
        'L2': 'L3',
        'M1': 'M2',
    }

    if code not in progression:
        return {
            'autorise': False,
            'message': "Ce niveau ne possède pas de passage automatique."
        }

    code_suivant = progression[code]

    niveau_suivant = Niveau.objects.filter(
        code=code_suivant
    ).first()

    if niveau_suivant is None:
        raise ValidationError(
            f"Le niveau {code_suivant} n'existe pas."
        )

    credits = calculer_credits_annee(
        student,
        niveau_actuel
    )

    autorise = peut_passer_niveau(
        student,
        niveau_actuel
    )

    arrieres = get_matieres_non_validees(
        student,
        niveau_actuel
    )

    return {
        'autorise': autorise,
        'niveau_actuel': niveau_actuel,
        'niveau_suivant': niveau_suivant,
        'credits': credits,
        'arrieres': arrieres,
    }


@transaction.atomic
def effectuer_passage(student):
    """
    Effectue réellement le passage de l'étudiant.

    Le système :

    1. Vérifie que le passage est autorisé.
    2. Récupère les crédits obtenus.
    3. Récupère les éventuels arriérés.
    4. Enregistre la progression.
    5. Enregistre chaque matière en arriéré.
    6. Change le niveau de l'étudiant.

    Les notes des évaluations ne sont jamais supprimées
    lors du passage.

    Toutes les opérations sont effectuées dans
    une transaction.
    """

    resultat = verifier_passage(student)

    if not resultat['autorise']:
        raise ValidationError(
            "L'étudiant ne remplit pas les conditions "
            "pour passer au niveau suivant."
        )

    niveau_actuel = resultat['niveau_actuel']
    niveau_suivant = resultat['niveau_suivant']

    credits_obtenus = resultat['credits']
    arrieres = resultat['arrieres']

    annee_universitaire = AnneeUniversitaire.objects.filter(
        active=True
    ).first()

    if annee_universitaire is None:
        raise ValidationError(
            "Aucune année universitaire active n'est définie."
        )

    progression_existante = Progression.objects.filter(
        student=student,
        ancien_niveau=niveau_actuel,
        nouveau_niveau=niveau_suivant,
        annee_universitaire=annee_universitaire
    ).first()

    if progression_existante is not None:
        raise ValidationError(
            "Le passage de cet étudiant est déjà enregistré "
            "pour cette année universitaire."
        )

    progression = Progression.objects.create(
        student=student,
        ancien_niveau=niveau_actuel,
        nouveau_niveau=niveau_suivant,
        annee_universitaire=annee_universitaire,
        credits_obtenus=credits_obtenus,
        credits_maximum=60,
        passage_avec_arrieres=len(arrieres) > 0,
    )

    for subject in arrieres:

        if subject.credits is None:
            raise ValidationError(
                f"La matière '{subject.nom}' n'a pas de crédit défini."
            )

        # Éviter de créer deux fois le même arriéré
        arriere_existant = Arriere.objects.filter(
            progression=progression,
            subject=subject
        ).first()

        if arriere_existant is None:
            Arriere.objects.create(
                progression=progression,
                subject=subject,
                credits=subject.credits,
                statut='non_valide'
            )

    student.niveau = niveau_suivant

    student.save(
        update_fields=['niveau']
    )

    return progression


def obtenir_arrieres_etudiant(student):
    """
    Retourne tous les arriérés enregistrés
    pour un étudiant.

    Les arriérés validés et non validés sont retournés.
    """

    return Arriere.objects.filter(
        progression__student=student
    ).select_related(
        'subject',
        'progression',
        'progression__ancien_niveau',
        'progression__nouveau_niveau'
    ).order_by(
        'progression__date_passage',
        'subject__nom'
    )


def obtenir_arrieres_non_valides(student):
    """
    Retourne uniquement les arriérés
    qui ne sont pas encore validés.
    """

    return obtenir_arrieres_etudiant(
        student
    ).filter(
        statut='non_valide'
    )


def arrieres_historique(student):
    """
    Retourne l'historique complet des arriérés
    de l'étudiant.

    Les arriérés validés restent dans l'historique.
    """

    return list(
        obtenir_arrieres_etudiant(
            student
        )
    )


@transaction.atomic
def valider_arriere(arriere):
    """
    Valide un arriéré uniquement si la matière concernée
    est réellement validée.

    La validation peut provenir :

    - de la Session 1 ;
    - de la Session 2.

    La Session 2 utilise :
    - le contrôle continu conservé à 40 % ;
    - le nouvel examen à 60 %.

    Les anciennes notes restent intégralement conservées
    dans l'historique des Grade.
    """

    if arriere.statut == 'valide':
        return arriere

    student = arriere.progression.student
    subject = arriere.subject

    moyenne = obtenir_moyenne_finale_retenue(
        student,
        subject
    )

    if moyenne is None:
        raise ValidationError(
            f"La matière '{subject.nom}' ne peut pas encore "
            "être validée car sa moyenne finale n'est pas disponible."
        )

    if moyenne < 10:
        raise ValidationError(
            f"La matière '{subject.nom}' n'est pas validée. "
            f"Moyenne finale retenue : {moyenne:.2f}/20."
        )

    arriere.statut = 'valide'
    arriere.date_validation = date.today()

    arriere.save(
        update_fields=[
            'statut',
            'date_validation'
        ]
    )

    return arriere


def solder_arrieres_valides(student):
    """
    Recherche les arriérés non validés de l'étudiant
    et valide automatiquement ceux dont la matière
    est désormais réussie.

    Cette fonction est particulièrement utile après
    la publication des résultats de Session 2.

    Les notes historiques ne sont jamais supprimées.
    """

    arrieres = obtenir_arrieres_non_valides(
        student
    )

    arrieres_soldes = []

    for arriere in arrieres:

        try:
            arriere = valider_arriere(
                arriere
            )

            arrieres_soldes.append(
                arriere
            )

        except ValidationError:
            # La matière n'est pas encore validée.
            # On conserve l'arriéré comme non validé.
            continue

    return arrieres_soldes


def verifier_arrieres_niveau(student, niveau):
    """
    Vérifie si tous les arriérés provenant
    d'un niveau sont soldés.

    Avant la vérification, le système tente automatiquement
    de solder les arriérés dont les matières sont désormais
    validées.
    """

    solder_arrieres_valides(
        student
    )

    arrieres = obtenir_arrieres_non_valides(
        student
    ).filter(
        progression__ancien_niveau=niveau
    )

    return not arrieres.exists()


def obtenir_situation_academique(student):
    """
    Retourne la situation académique complète
    de l'étudiant.

    La fonction tente d'abord de solder automatiquement
    les arriérés dont les matières ont été validées,
    notamment après une Session 2.
    """

    niveau = student.niveau

    if niveau is None:
        raise ValidationError(
            "L'étudiant n'a aucun niveau associé."
        )

    # Mise à jour automatique des arriérés
    solder_arrieres_valides(
        student
    )

    credits = calculer_credits_annee(
        student,
        niveau
    )

    matieres_non_validees = get_matieres_non_validees(
        student,
        niveau
    )

    passage = verifier_passage(
        student
    )

    arrieres = obtenir_arrieres_non_valides(
        student
    )

    situation = {
        'niveau': niveau,
        'credits': credits,
        'matieres_non_validees': matieres_non_validees,
        'passage_autorise': passage['autorise'],
        'niveau_suivant': passage.get('niveau_suivant'),
        'arrieres': arrieres,
        'licence_obtenue': False,
        'master_obtenu': False,
    }

    if niveau.code == 'L3':
        situation['licence_obtenue'] = peut_obtenir_licence(
            student
        )

    if niveau.code == 'M2':
        situation['master_obtenu'] = peut_obtenir_master(
            student
        )

    return situation