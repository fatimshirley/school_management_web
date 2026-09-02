from django.core.exceptions import ValidationError

from apps.academic.models import Semestre
from apps.subjects.models import Subject
from apps.grades.services.grade_service import (
    obtenir_moyenne_finale_retenue
)


def calculer_credits_semestre(student, semestre):
    """
    Calcule les crédits obtenus par un étudiant pour un semestre.

    Une matière validée avec une moyenne finale retenue
    >= 10/20 rapporte les crédits associés à cette matière.

    La moyenne finale retenue peut provenir :
    - de la Session 1 si la matière est validée ;
    - de la Session 2 si la Session 1 était insuffisante
      et que l'étudiant a passé la Session 2.
    """

    subjects = Subject.objects.filter(
        semestre=semestre
    )

    total_credits = 0

    for subject in subjects:

        moyenne = obtenir_moyenne_finale_retenue(
            student,
            subject
        )

        if moyenne is not None and moyenne >= 10:

            if subject.credits is not None:
                total_credits += subject.credits

    return total_credits


def verifier_credits_semestre(semestre):
    """
    Vérifie que les matières d'un semestre représentent
    exactement 30 crédits.

    Cette fonction vérifie la configuration pédagogique,
    pas les crédits obtenus par un étudiant.
    """

    subjects = Subject.objects.filter(
        semestre=semestre
    )

    total_credits = 0

    for subject in subjects:

        if subject.credits is None:
            raise ValidationError(
                f"La matière '{subject.nom}' n'a pas de crédit défini."
            )

        total_credits += subject.credits

    if total_credits != 30:
        raise ValidationError(
            f"Le semestre '{semestre.nom}' doit contenir "
            f"exactement 30 crédits. "
            f"Total actuel : {total_credits}."
        )

    return True


def semestre_valide(student, semestre):
    """
    Un semestre est validé lorsque l'étudiant
    obtient les 30 crédits du semestre.
    """

    verifier_credits_semestre(semestre)

    credits = calculer_credits_semestre(
        student,
        semestre
    )

    return credits == 30


def calculer_credits_annee(student, niveau):
    """
    Calcule les crédits obtenus par l'étudiant
    sur les deux semestres d'un niveau.

    Un niveau comporte deux semestres de 30 crédits,
    soit un maximum de 60 crédits.
    """

    semestres = Semestre.objects.filter(
        niveau=niveau
    ).order_by('nom')

    total_credits = 0

    for semestre in semestres:

        total_credits += calculer_credits_semestre(
            student,
            semestre
        )

    return total_credits


def verifier_structure_annee(niveau):
    """
    Vérifie qu'un niveau possède exactement deux semestres
    et que chaque semestre représente exactement 30 crédits.
    """

    semestres = Semestre.objects.filter(
        niveau=niveau
    ).order_by('nom')

    if semestres.count() != 2:
        raise ValidationError(
            f"Le niveau '{niveau.nom}' doit comporter "
            f"exactement deux semestres."
        )

    for semestre in semestres:
        verifier_credits_semestre(semestre)

    return True


def annee_validee(student, niveau):
    """
    Une année est complètement validée lorsque
    l'étudiant possède les 60 crédits du niveau.
    """

    verifier_structure_annee(niveau)

    credits = calculer_credits_annee(
        student,
        niveau
    )

    return credits == 60


def get_matieres_non_validees(student, niveau):
    """
    Retourne les matières du niveau que l'étudiant
    n'a finalement pas validées.

    La moyenne finale retenue est utilisée.

    Cela signifie que :

    - une matière validée en Session 1 est considérée
      comme validée ;

    - une matière échouée en Session 1 mais réussie
      en Session 2 est considérée comme validée ;

    - une matière échouée en Session 1 sans Session 2
      validée reste non validée ;

    - une moyenne encore indisponible est considérée
      comme non validée pour le calcul des arriérés.
    """

    matieres_non_validees = []

    semestres = Semestre.objects.filter(
        niveau=niveau
    ).order_by('nom')

    for semestre in semestres:

        subjects = Subject.objects.filter(
            semestre=semestre
        )

        for subject in subjects:

            moyenne = obtenir_moyenne_finale_retenue(
                student,
                subject
            )

            if moyenne is None or moyenne < 10:
                matieres_non_validees.append(subject)

    return matieres_non_validees


def get_arrieres(student, niveaux):
    """
    Retourne les matières non validées des anciens niveaux.

    Exemple :

    L1 non validé
    ↓
    matières L1 restantes = arriérés

    L2 non validé
    ↓
    matières L2 restantes = arriérés
    """

    arrieres = []

    for niveau in niveaux:

        matieres = get_matieres_non_validees(
            student,
            niveau
        )

        arrieres.extend(matieres)

    return arrieres


def arrieres_soldes(student, niveaux):
    """
    Vérifie si tous les arriérés des niveaux indiqués
    ont été validés.
    """

    arrieres = get_arrieres(
        student,
        niveaux
    )

    return len(arrieres) == 0


def obtenir_niveau_suivant(niveau):
    """
    Retourne le niveau suivant selon le parcours LMD.

    L1 → L2
    L2 → L3
    M1 → M2

    L3 et M2 n'ont pas de niveau suivant
    dans le cadre de cette fonction.
    """

    progression = {
        'L1': 'L2',
        'L2': 'L3',
        'M1': 'M2',
    }

    code_suivant = progression.get(
        niveau.code
    )

    if code_suivant is None:
        return None

    try:
        niveau_suivant = niveau.__class__.objects.get(
            code=code_suivant
        )

    except niveau.__class__.DoesNotExist:
        raise ValidationError(
            f"Le niveau {code_suivant} n'existe pas encore."
        )

    return niveau_suivant


def peut_passer_niveau(student, niveau):
    """
    Détermine si un étudiant peut passer au niveau suivant.

    Règles :

    L1 → L2 :
        minimum 48 crédits sur 60.

    L2 → L3 :
        minimum 48 crédits sur 60 pour le niveau L2
        ET les arriérés de L1 doivent être soldés.

    M1 → M2 :
        minimum 48 crédits sur 60.

    Les 60 crédits restent nécessaires pour considérer
    complètement l'année comme validée.

    Cette fonction ne modifie pas le niveau de l'étudiant.
    Elle indique uniquement si le passage est autorisé.
    """

    if niveau.code not in ['L1', 'L2', 'M1']:
        return False

    verifier_structure_annee(niveau)

    credits = calculer_credits_annee(
        student,
        niveau
    )

    if credits < 48:
        return False

    if niveau.code == 'L2':

        niveau_l1 = niveau.__class__.objects.filter(
            code='L1'
        ).first()

        if niveau_l1 is None:
            raise ValidationError(
                "Le niveau L1 n'existe pas."
            )

        if not arrieres_soldes(
            student,
            [niveau_l1]
        ):
            return False

    return True


def peut_obtenir_licence(student):
    """
    Vérifie si l'étudiant peut obtenir la Licence.

    Conditions :

    - L1 + L2 + L3 = 180 crédits
    - aucun arriéré de L1
    - aucun arriéré de L2
    - aucun arriéré de L3

    Les crédits obtenus en Session 2 sont pris en compte
    grâce à obtenir_moyenne_finale_retenue().
    """

    if student.niveau is None:
        raise ValidationError(
            "L'étudiant n'a aucun niveau associé."
        )

    niveaux = student.niveau.__class__

    l1 = niveaux.objects.filter(
        code='L1'
    ).first()

    l2 = niveaux.objects.filter(
        code='L2'
    ).first()

    l3 = niveaux.objects.filter(
        code='L3'
    ).first()

    if l1 is None or l2 is None or l3 is None:
        raise ValidationError(
            "Les niveaux L1, L2 et L3 doivent exister."
        )

    credits_total = (
        calculer_credits_annee(student, l1)
        + calculer_credits_annee(student, l2)
        + calculer_credits_annee(student, l3)
    )

    if credits_total != 180:
        return False

    if not arrieres_soldes(
        student,
        [l1, l2, l3]
    ):
        return False

    return True


def peut_obtenir_master(student):
    """
    Vérifie si l'étudiant peut obtenir le Master.

    Conditions :

    - M1 + M2 = 120 crédits
    - aucun arriéré de M1
    - aucun arriéré de M2

    Les crédits obtenus en Session 2 sont pris en compte
    grâce à obtenir_moyenne_finale_retenue().
    """

    if student.niveau is None:
        raise ValidationError(
            "L'étudiant n'a aucun niveau associé."
        )

    niveaux = student.niveau.__class__

    m1 = niveaux.objects.filter(
        code='M1'
    ).first()

    m2 = niveaux.objects.filter(
        code='M2'
    ).first()

    if m1 is None or m2 is None:
        raise ValidationError(
            "Les niveaux M1 et M2 doivent exister."
        )

    credits_total = (
        calculer_credits_annee(student, m1)
        + calculer_credits_annee(student, m2)
    )

    if credits_total != 120:
        return False

    if not arrieres_soldes(
        student,
        [m1, m2]
    ):
        return False

    return True