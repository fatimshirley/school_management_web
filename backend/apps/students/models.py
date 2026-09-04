import secrets
import string
from django.contrib.auth.models import User
from django.db import models
from apps.academic.models import Niveau, Filiere


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    matricule = models.CharField(
        max_length=20,
        unique=True
    )

    nom = models.CharField(
        max_length=100
    )

    prenom = models.CharField(
        max_length=100
    )

    age = models.PositiveIntegerField()

    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.PROTECT,
        related_name='students',
        null=True,
        blank=True
    )

    niveau = models.ForeignKey(
        Niveau,
        on_delete=models.PROTECT,
        related_name='students',
        null=True,
        blank=True
    )

    # Champ temporaire pour afficher le mot de passe en clair à l'administrateur
    raw_password = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    @property
    def filiere_display(self):
        if self.filiere:
            return f"{self.filiere.code} — {self.filiere.nom}"
        return "Non affectée"

    @property
    def niveau_display(self):
        if self.niveau:
            return f"{self.niveau.code} — {self.niveau.nom}"
        return "Non affecté"

    def save(self, *args, **kwargs):
        # 1. S'assurer qu'un mot de passe en clair existe toujours pour l'affichage admin
        if not self.raw_password:
            alphabet = string.ascii_letters + string.digits
            generated_password = ''.join(secrets.choice(alphabet) for _ in range(8))
            self.raw_password = generated_password
        else:
            generated_password = self.raw_password

        # 2. Créer le compte utilisateur Django s'il n'existe pas encore
        if not self.user:
            username = self.matricule
            email = f"{self.matricule.lower()}@ecole.com"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=generated_password,
                first_name=self.prenom,
                last_name=self.nom
            )
            self.user = user

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenom}"