# accounts/signals.py
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Si aucun profil n'existe encore pour cet utilisateur, on lui en crée un par défaut (ex: etudiant)
        # Tu pourras ajuster le rôle dynamiquement dans tes formulaires de création.
        UserProfile.objects.get_or_create(user=instance, defaults={'role': 'etudiant'})

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()