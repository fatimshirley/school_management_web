from datetime import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect, render

from .models import UserProfile
from apps.students.models import Student
from apps.academic.models import Niveau, Filiere


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


@login_required
def admin_student_add(request):
    """Vue pour ajouter un étudiant avec filière, niveau, génération automatique du matricule et du compte"""
    niveaux = Niveau.objects.all()
    filieres = Filiere.objects.all()

    context = {
        'niveaux': niveaux,
        'filieres': filieres
    }

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
        age_str = request.POST.get('age', '').strip()
        filiere_id = request.POST.get('filiere', '').strip()
        niveau_id = request.POST.get('niveau', '').strip()

        # Validation de base pour éviter les alertes de champs vides
        if not nom or not prenom or not age_str or not filiere_id or not niveau_id:
            context['error'] = "Veuillez renseigner tous les champs obligatoires."
            return render(request, 'admin/students/student_add.html', context)

        # Validation de l'âge (doit être un entier positif)
        try:
            age = int(age_str)
        except ValueError:
            context['error'] = "L'âge doit être un nombre entier."
            return render(request, 'admin/students/student_add.html', context)

        if age <= 0:
            context['error'] = "L'âge doit être supérieur à 0."
            return render(request, 'admin/students/student_add.html', context)

        try:
            filiere = Filiere.objects.get(id=filiere_id)
            niveau = Niveau.objects.get(id=niveau_id)
        except (Filiere.DoesNotExist, Niveau.DoesNotExist):
            context['error'] = "La filière ou le niveau sélectionné est invalide."
            return render(request, 'admin/students/student_add.html', context)

        # --- GÉNÉRATION AUTOMATIQUE DU MATRICULE UNIQUE ---
        # Format : Année (ex: 26) + Code Filière (ex: INFO) + Code Niveau (ex: L1) + Séquence (ex: 001)
        current_year_short = datetime.now().strftime('%y')
        filiere_code = filiere.code.upper()
        niveau_code = niveau.code.upper()
        prefix = f"{current_year_short}{filiere_code}{niveau_code}"

        last_student = Student.objects.filter(matricule__startswith=prefix).order_by('-matricule').first()

        if last_student:
            try:
                last_seq = int(last_student.matricule[len(prefix):])
                new_seq = last_seq + 1
            except ValueError:
                new_seq = 1
        else:
            new_seq = 1

        matricule = f"{prefix}{new_seq:03d}"
        # --------------------------------------------------

        # Création des identifiants uniques de connexion
        username = matricule.lower()
        email = f"{username}@school.mg"
        default_password = f"Pass{matricule}!"

        # Création de l'utilisateur Django de base
        user = User.objects.create_user(
            username=username,
            email=email,
            password=default_password,
            first_name=prenom,
            last_name=nom
        )

        # Attribution du rôle via le profil
        if hasattr(user, 'userprofile'):
            user.userprofile.role = 'etudiant'
            user.userprofile.save()

        # Création de l'étudiant lié au compte avec sa filière et son niveau
        Student.objects.create(
            user=user,
            matricule=matricule,
            nom=nom,
            prenom=prenom,
            age=age,
            filiere=filiere,
            niveau=niveau
        )

        messages.success(request, f"Étudiant enregistré ! Matricule généré : {matricule}")
        return redirect('admin_students')

    return render(request, 'admin/students/student_add.html', context)