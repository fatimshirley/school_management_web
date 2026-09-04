import secrets
import string
from django.contrib.auth.models import User
from django.db import models


class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    identifiant = models.CharField(
        max_length=20,
        unique=True,
        blank=True  # Permet de le générer automatiquement s'il est vide
    )

    nom = models.CharField(
        max_length=100
    )

    prenom = models.CharField(
       max_length=100,
       null=True,
       blank=True
    )

    raw_password = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    def save(self, *args, **kwargs):
        # 1. Générer un identifiant unique si absent (ex: PROF7823)
        if not self.identifiant:
            rand_digits = ''.join(secrets.choice(string.digits) for _ in range(4))
            self.identifiant = f"PROF{rand_digits}"

        # 2. S'assurer qu'un mot de passe en clair existe pour l'affichage admin
        if not self.raw_password:
            alphabet = string.ascii_letters + string.digits
            generated_password = ''.join(secrets.choice(alphabet) for _ in range(8))
            self.raw_password = generated_password
        else:
            generated_password = self.raw_password

        # 3. Créer le compte utilisateur Django s'il n'existe pas encore
        if not self.user:
            username = self.identifiant.lower()
            email = f"{username}@ecole.com"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=generated_password,
                first_name=self.prenom or "",
                last_name=self.nom
            )
            self.user = user

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.identifiant} - {self.nom} {self.prenom}"