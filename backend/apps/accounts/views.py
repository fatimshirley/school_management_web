from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
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
        email = request.POST.get(
            'username',
            ''
        ).strip().lower()

        password = request.POST.get(
            'password',
            ''
        )

        if not email or not password:
            messages.error(
                request,
                "Veuillez renseigner tous les champs."
            )
            return render(
                request,
                'accounts/login.html'
            )

        try:
            user_account = User.objects.get(
                email__iexact=email
            )
        except User.DoesNotExist:
            messages.error(
                request,
                "Adresse email ou mot de passe incorrect."
            )
            return render(
                request,
                'accounts/login.html'
            )
        except User.MultipleObjectsReturned:
            messages.error(
                request,
                "Plusieurs comptes utilisent cette adresse email."
            )
            return render(
                request,
                'accounts/login.html'
            )

        user = authenticate(
            request,
            username=user_account.username,
            password=password
        )

        if user is None:
            messages.error(
                request,
                "Adresse email ou mot de passe incorrect."
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
        # Cherche le premier UserProfile qui correspond au rôle demandé ('admin', 'professeur', 'etudiant')
        profile = UserProfile.objects.filter(role=role).first()
        if profile:
            user = profile.user
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            # Utilise ta fonction existante pour rediriger vers le bon dashboard
            return redirection_par_role(request, user)
    except Exception as e:
        pass
    
    messages.error(request, f"Aucun utilisateur trouvé pour le rôle : {role}")
    return redirect('connexion')