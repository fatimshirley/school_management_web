from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def connexion(request):
    """
    Gère la connexion des utilisateurs.
    """

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(
                request,
                "Veuillez renseigner tous les champs."
            )

            return render(
                request,
                'accounts/login.html'
            )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            messages.error(
                request,
                "Nom d'utilisateur ou mot de passe incorrect."
            )

            return render(
                request,
                'accounts/login.html'
            )

        login(
            request,
            user
        )

        return redirect('dashboard')

    return render(
        request,
        'accounts/login.html'
    )


@login_required
def deconnexion(request):
    """
    Déconnecte l'utilisateur.
    """

    logout(request)

    return redirect('connexion')