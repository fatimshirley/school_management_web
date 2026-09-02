from django.db import models


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


class Semestre(models.Model):

    nom = models.CharField(
        max_length=20
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

    def __str__(self):
        return f"{self.niveau} - {self.nom}"


class AnneeUniversitaire(models.Model):

    libelle = models.CharField(
        max_length=20,
        unique=True
    )

    active = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.libelle



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