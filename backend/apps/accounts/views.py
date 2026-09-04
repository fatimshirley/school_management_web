from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect, render

from .models import UserProfile


def redirection_par_role(request, user):
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        messages.error(
            request,
            "Aucun profil utilisateur n'est associé à ce compte."
        )
        logout(request)
        return redirect('connexion')

    if profile.role == 'admin':
        return redirect('admin_dashboard')

    if profile.role == 'professeur':
        return redirect('professeur_dashboard')

    if profile.role == 'etudiant':
        return redirect('etudiant_dashboard')

    messages.error(
        request,
        "Le rôle de votre compte est invalide."
    )
    logout(request)
    return redirect('connexion')


def connexion(request):
    if request.user.is_authenticated:
        return redirection_par_role(
            request,
            request.user
        )

    if request.method == 'POST':
        # On récupère la valeur entrée (qui peut être un matricule, un identifiant ou un email)
        identifiant_ou_email = request.POST.get(
            'username',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        if not identifiant_ou_email or not password:
            messages.error(
                request,
                "Veuillez renseigner tous les champs."
            )
            return render(
                request,
                'accounts/login.html'
            )

        # Recherche de l'utilisateur par Username (Matricule/Identifiant) OU par Email
        try:
            user_account = User.objects.get(
                Q(username__iexact=identifiant_ou_email) | Q(email__iexact=identifiant_ou_email)
            )
        except User.DoesNotExist:
            messages.error(
                request,
                "Identifiant, adresse email ou mot de passe incorrect."
            )
            return render(
                request,
                'accounts/login.html'
            )
        except User.MultipleObjectsReturned:
            messages.error(
                request,
                "Plusieurs comptes correspondent à ces informations."
            )
            return render(
                request,
                'accounts/login.html'
            )

        # Authentification avec le vrai username trouvé en base
        user = authenticate(
            request,
            username=user_account.username,
            password=password
        )

        if user is None:
            messages.error(
                request,
                "Identifiant, adresse email ou mot de passe incorrect."
            )
            return render(
                request,
                'accounts/login.html'
            )

        if not user.is_active:
            messages.error(
                request,
                "Ce compte est désactivé."
            )
            return render(
                request,
                'accounts/login.html'
            )

        login(
            request,
            user
        )

        return redirection_par_role(
            request,
            user
        )

    return render(
        request,
        'accounts/login.html'
    )


@login_required
def deconnexion(request):
    logout(request)
    return redirect('connexion')


def bypass_login(request, role):
    """Vue temporaire de dev pour se connecter instantanément par rôle"""
    try:
        profile = UserProfile.objects.filter(role=role).first()
        if profile:
            user = profile.user
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirection_par_role(request, user)
    except Exception as e:
        pass
    
    messages.error(request, f"Aucun utilisateur trouvé pour le rôle : {role}")
    return redirect('connexion')