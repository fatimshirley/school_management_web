from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Filiere(models.Model):

    nom = models.CharField(
        max_length=100,
        unique=True
    )

    code = models.CharField(
        max_length=20,
        unique=True
    )

    def __str__(self):
        return f"{self.code} - {self.nom}"


class Niveau(models.Model):

    CODE_CHOICES = [
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
    ]

    nom = models.CharField(
        max_length=50
    )

    code = models.CharField(
        max_length=2,
        choices=CODE_CHOICES,
        unique=True,
        null=True,
        blank=True
    )

    filieres = models.ManyToManyField(
        Filiere,
        related_name='niveaux'
    )

    def __str__(self):
        return self.nom

class AnneeUniversitaire(models.Model):

    libelle = models.CharField(
        max_length=20,
        unique=True
    )

    date_debut = models.DateField(
        null=True,
        blank=True
    )

    date_fin = models.DateField(
        null=True,
        blank=True
    )

    active = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.libelle

        
class Semestre(models.Model):

    SEMESTRE_CHOICES = [
        ('S1', 'Semestre 1 (L1)'),
        ('S2', 'Semestre 2 (L1)'),
        ('S3', 'Semestre 3 (L2)'),
        ('S4', 'Semestre 4 (L2)'),
        ('S5', 'Semestre 5 (L3)'),
        ('S6', 'Semestre 6 (L3)'),
        ('S7', 'Semestre 7 (M1)'),
        ('S8', 'Semestre 8 (M1)'),
        ('S9', 'Semestre 9 (M2)'),
        ('S10', 'Semestre 10 (M2)'),
    ]

    nom = models.CharField(
        max_length=5,
        choices=SEMESTRE_CHOICES
    )

    date_debut = models.DateField(
        null=True,
        blank=True
    )

    date_fin = models.DateField(
        null=True,
        blank=True
    )

    niveau = models.ForeignKey(
        Niveau,
        on_delete=models.CASCADE,
        related_name='semestres'
    )

    # Rendu temporairement optionnel pour éviter le blocage des migrations
    annee_universitaire = models.ForeignKey(
        AnneeUniversitaire,
        on_delete=models.CASCADE,
        related_name='semestres',
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('niveau', 'annee_universitaire', 'nom')

    def __str__(self):
        annee_str = self.annee_universitaire.libelle if self.annee_universitaire else "Sans année"
        return f"{annee_str} — {self.niveau.nom} ({self.get_nom_display()})"


# --- SIGNAUX AUTOMATIQUES ---

CORRESPONDANCE_SEMESTRES = {
    'L1': ['S1', 'S2'],
    'L2': ['S3', 'S4'],
    'L3': ['S5', 'S6'],
    'M1': ['S7', 'S8'],
    'M2': ['S9', 'S10'],
}


@receiver(post_save, sender=AnneeUniversitaire)
def creer_semestres_pour_annee(sender, instance, created, **kwargs):
    if created:
        for niveau in Niveau.objects.all():
            if niveau.code in CORRESPONDANCE_SEMESTRES:
                for code_semestre in CORRESPONDANCE_SEMESTRES[niveau.code]:
                    Semestre.objects.get_or_create(
                        niveau=niveau,
                        annee_universitaire=instance,
                        nom=code_semestre
                    )


@receiver(post_save, sender=Niveau)
def creer_semestres_pour_niveau(sender, instance, created, **kwargs):
    if created:
        if instance.code in CORRESPONDANCE_SEMESTRES:
            for annee in AnneeUniversitaire.objects.all():
                for code_semestre in CORRESPONDANCE_SEMESTRES[instance.code]:
                    Semestre.objects.get_or_create(
                        niveau=instance,
                        annee_universitaire=annee,
                        nom=code_semestre
                    )


class Progression(models.Model):

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='progressions'
    )

    ancien_niveau = models.ForeignKey(
        Niveau,
        on_delete=models.PROTECT,
        related_name='progressions_depart'
    )

    nouveau_niveau = models.ForeignKey(
        Niveau,
        on_delete=models.PROTECT,
        related_name='progressions_arrivee'
    )

    annee_universitaire = models.ForeignKey(
        AnneeUniversitaire,
        on_delete=models.PROTECT,
        related_name='progressions'
    )

    credits_obtenus = models.PositiveIntegerField()

    credits_maximum = models.PositiveIntegerField(
        default=60
    )

    passage_avec_arrieres = models.BooleanField(
        default=False
    )

    date_passage = models.DateField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.student.matricule} - "
            f"{self.ancien_niveau.code} → "
            f"{self.nouveau_niveau.code}"
        )


class Arriere(models.Model):

    STATUT_CHOICES = [
        ('non_valide', 'Non validé'),
        ('valide', 'Validé'),
    ]

    progression = models.ForeignKey(
        Progression,
        on_delete=models.CASCADE,
        related_name='arrieres'
    )

    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.PROTECT,
        related_name='arrieres'
    )

    credits = models.PositiveIntegerField()

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='non_valide'
    )

    date_validation = models.DateField(
        null=True,
        blank=True
    )

    def __str__(self):
        return (
            f"{self.progression.student.matricule} - "
            f"{self.subject.nom} - "
            f"{self.statut}"
        )