from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, render

from .models import UserProfile
from apps.students.models import Student
from apps.teachers.models import Teacher
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
        identifiant = request.POST.get(
            'username',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        if not identifiant or not password:
            messages.error(
                request,
                "Veuillez renseigner tous les champs."
            )
            return render(
                request,
                'accounts/login.html'
            )

        user = None

        # ==================================================
        # CONNEXION ÉTUDIANT AVEC LE MATRICULE
        # ==================================================

        try:
            student = (
                Student.objects
                .select_related('user')
                .get(
                    matricule__iexact=identifiant
                )
            )

            if student.user:
                user = authenticate(
                    request,
                    username=student.user.username,
                    password=password
                )

        except Student.DoesNotExist:
            pass

        # ==================================================
        # CONNEXION PROFESSEUR AVEC L'IDENTIFIANT
        # ==================================================

        if user is None:
            try:
                teacher = (
                    Teacher.objects
                    .select_related('user')
                    .get(
                        identifiant__iexact=identifiant
                    )
                )

                if teacher.user:
                    user = authenticate(
                        request,
                        username=teacher.user.username,
                        password=password
                    )

            except Teacher.DoesNotExist:
                pass

        # ==================================================
        # CONNEXION AVEC L'EMAIL
        # ==================================================

        if user is None:
            try:
                user_account = User.objects.get(
                    email__iexact=identifiant
                )

                user = authenticate(
                    request,
                    username=user_account.username,
                    password=password
                )

            except User.DoesNotExist:
                pass

            except User.MultipleObjectsReturned:
                messages.error(
                    request,
                    "Plusieurs comptes utilisent cette adresse email."
                )
                return render(
                    request,
                    'accounts/login.html'
                )

        # ==================================================
        # IDENTIFIANT OU MOT DE PASSE INCORRECT
        # ==================================================

        if user is None:
            messages.error(
                request,
                "Identifiant, adresse email ou mot de passe incorrect."
            )
            return render(
                request,
                'accounts/login.html'
            )

        # ==================================================
        # COMPTE DÉSACTIVÉ
        # ==================================================

        if not user.is_active:
            messages.error(
                request,
                "Ce compte est désactivé."
            )
            return render(
                request,
                'accounts/login.html'
            )

        # ==================================================
        # CONNEXION
        # ==================================================

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
    if role not in [
        'admin',
        'professeur',
        'etudiant'
    ]:
        messages.error(
            request,
            "Rôle invalide."
        )
        return redirect('connexion')

    try:
        profile = (
            UserProfile.objects
            .select_related('user')
            .filter(role=role)
            .first()
        )

        if profile and profile.user:
            user = profile.user

            if not user.is_active:
                messages.error(
                    request,
                    "Ce compte est désactivé."
                )
                return redirect('connexion')

            user.backend = (
                'django.contrib.auth.backends.ModelBackend'
            )

            login(
                request,
                user
            )

            return redirection_par_role(
                request,
                user
            )

    except Exception:
        messages.error(
            request,
            "Impossible d'effectuer la connexion temporaire."
        )
        return redirect('connexion')

    messages.error(
        request,
        f"Aucun utilisateur trouvé pour le rôle : {role}"
    )

    return redirect('connexion')


@login_required
def admin_student_add(request):
    niveaux = Niveau.objects.all().order_by('code')
    filieres = Filiere.objects.all().order_by('code')

    context = {
        'niveaux': niveaux,
        'filieres': filieres
    }

    if request.method == 'POST':
        nom = request.POST.get(
            'nom',
            ''
        ).strip()

        prenom = request.POST.get(
            'prenom',
            ''
        ).strip()

        age_str = request.POST.get(
            'age',
            ''
        ).strip()

        filiere_id = request.POST.get(
            'filiere',
            ''
        ).strip()

        niveau_id = request.POST.get(
            'niveau',
            ''
        ).strip()

        if not nom or not prenom or not age_str or not filiere_id or not niveau_id:
            context['error'] = (
                "Veuillez renseigner tous les champs obligatoires."
            )
            return render(
                request,
                'admin/students/student_add.html',
                context
            )

        try:
            age = int(age_str)
        except ValueError:
            context['error'] = (
                "L'âge doit être un nombre entier."
            )
            return render(
                request,
                'admin/students/student_add.html',
                context
            )

        if age <= 0:
            context['error'] = (
                "L'âge doit être supérieur à 0."
            )
            return render(
                request,
                'admin/students/student_add.html',
                context
            )

        try:
            filiere = Filiere.objects.get(
                id=filiere_id
            )

            niveau = Niveau.objects.get(
                id=niveau_id
            )

        except Filiere.DoesNotExist:
            context['error'] = (
                "La filière sélectionnée est invalide."
            )
            return render(
                request,
                'admin/students/student_add.html',
                context
            )

        except Niveau.DoesNotExist:
            context['error'] = (
                "Le niveau sélectionné est invalide."
            )
            return render(
                request,
                'admin/students/student_add.html',
                context
            )

        current_year_short = datetime.now().strftime('%y')

        filiere_code = filiere.code.upper()
        niveau_code = niveau.code.upper()

        prefix = (
            f"{current_year_short}"
            f"{filiere_code}"
            f"{niveau_code}"
        )

        last_student = (
            Student.objects
            .filter(
                matricule__startswith=prefix
            )
            .order_by('-matricule')
            .first()
        )

        if last_student:
            try:
                last_seq = int(
                    last_student.matricule[len(prefix):]
                )
                new_seq = last_seq + 1
            except ValueError:
                new_seq = 1
        else:
            new_seq = 1

        matricule = f"{prefix}{new_seq:03d}"

        if Student.objects.filter(
            matricule__iexact=matricule
        ).exists():
            context['error'] = (
                "Le matricule généré existe déjà. "
                "Veuillez réessayer."
            )
            return render(
                request,
                'admin/students/student_add.html',
                context
            )

        try:
            with transaction.atomic():
                student = Student.objects.create(
                    matricule=matricule,
                    nom=nom,
                    prenom=prenom,
                    age=age,
                    filiere=filiere,
                    niveau=niveau
                )

                profile, created = UserProfile.objects.get_or_create(
                    user=student.user
                )

                profile.role = 'etudiant'
                profile.save()

        except Exception:
            context['error'] = (
                "Impossible d'enregistrer l'étudiant."
            )
            return render(
                request,
                'admin/students/student_add.html',
                context
            )

        messages.success(
            request,
            f"Étudiant enregistré ! "
            f"Matricule : {student.matricule} "
            f"| Mot de passe : {student.raw_password}"
        )

        return redirect(
            'admin_students'
        )

    return render(
        request,
        'admin/students/student_add.html',
        context
    )


@login_required
def admin_teacher_add(request):
    context = {}

    if request.method == 'POST':
        nom = request.POST.get(
            'nom',
            ''
        ).strip()

        prenom = request.POST.get(
            'prenom',
            ''
        ).strip()

        if not nom:
            context['error'] = (
                "Veuillez renseigner le nom du professeur."
            )
            return render(
                request,
                'admin/teachers/ajouter.html',
                context
            )

        try:
            with transaction.atomic():
                teacher = Teacher.objects.create(
                    nom=nom,
                    prenom=prenom or None
                )

                profile, created = UserProfile.objects.get_or_create(
                    user=teacher.user
                )

                profile.role = 'professeur'
                profile.save()

        except Exception:
            context['error'] = (
                "Impossible d'enregistrer le professeur."
            )
            return render(
                request,
                'admin/teachers/ajouter.html',
                context
            )

        messages.success(
            request,
            f"Professeur enregistré ! "
            f"Identifiant : {teacher.identifiant} "
            f"| Email : {teacher.user.email} "
            f"| Mot de passe : {teacher.raw_password}"
        )

        return redirect(
            'admin_teachers'
        )

    return render(
        request,
        'admin/teachers/ajouter.html',
        context
    )