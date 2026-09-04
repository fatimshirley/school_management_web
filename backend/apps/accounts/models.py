from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('professeur', 'Professeur'),
        ('etudiant', 'Étudiant'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='etudiant'  # Rôle par défaut de sécurité
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


# --- SIGNAUX POUR LA CRÉATION AUTOMATIQUE DU PROFIL ---

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crée un UserProfile automatiquement dès qu'un User est créé"""
    if created:
        UserProfile.objects.get_or_create(user=instance, defaults={'role': 'etudiant'})


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarde le profil associé si l'utilisateur est modifié"""
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()