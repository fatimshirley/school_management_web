from datetime import datetime
import re
import unicodedata
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.subjects.models import Subject
from apps.grades.models import Evaluation, Grade
from apps.absences.models import Absence
from apps.academic.models import (
    Filiere,
    Niveau,
    Semestre,
    AnneeUniversitaire,
    Progression,
    Arriere,
)
from apps.academic.models import (
    Semestre,
    Filiere,
)

from apps.subjects.models import Enseignement


# ==================================================
# OUTIL : REDIRECTION SELON LE RÔLE
# ==================================================

def redirection_par_role(request):
    profile = (
        UserProfile.objects
        .filter(
            user=request.user
        )
        .first()
    )

    if profile is None:
        logout(request)
        return redirect('connexion')

    if profile.role == 'admin':
        return redirect('admin_dashboard')

    if profile.role == 'professeur':
        return redirect('professeur_dashboard')

    if profile.role == 'etudiant':
        return redirect('etudiant_dashboard')

    logout(request)
    return redirect('connexion')


# ==================================================
# PROTECTION ADMIN
# ==================================================

def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = (
            UserProfile.objects
            .filter(
                user=request.user
            )
            .first()
        )

        if profile is None:
            logout(request)
            return redirect('connexion')

        if profile.role != 'admin':
            return redirection_par_role(request)

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# ==================================================
# PROTECTION PROFESSEUR
# ==================================================

def professeur_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = (
            UserProfile.objects
            .filter(
                user=request.user
            )
            .first()
        )

        if profile is None:
            logout(request)
            return redirect('connexion')

        if profile.role != 'professeur':
            return redirection_par_role(request)

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# ==================================================
# PROTECTION ÉTUDIANT
# ==================================================

def etudiant_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = (
            UserProfile.objects
            .filter(
                user=request.user
            )
            .first()
        )

        if profile is None:
            logout(request)
            return redirect('connexion')

        if profile.role != 'etudiant':
            return redirection_par_role(request)

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# ==================================================
# TABLEAU DE BORD PRINCIPAL
# ==================================================

@login_required
def dashboard(request):
    return redirection_par_role(request)


# ==================================================
# DASHBOARD ADMIN
# ==================================================

@admin_required
def admin_dashboard(request):
    context = {
        'total_students': Student.objects.count(),
        'total_teachers': Teacher.objects.count(),
        'total_subjects': Subject.objects.count(),
        'total_absences': Absence.objects.count(),

        'recent_students': (
            Student.objects
            .select_related('niveau')
            .order_by('-id')[:5]
        ),

        'recent_evaluations': (
            Evaluation.objects
            .select_related('subject')
            .order_by('-date', '-id')[:5]
        ),
    }

    return render(
        request,
        'admin/dashboard/dashboard.html',
        context
    )




# ==================================================
# ÉTUDIANTS
# ==================================================

@admin_required
def admin_students(request):
    students = (
        Student.objects
        .select_related('niveau', 'filiere')
        .order_by('nom', 'prenom')
    )

    return render(
        request,
        'admin/students/liste.html',
        {
            'students': students,
        }
    )


# ==================================================
# UTILITAIRES ÉTUDIANTS
# ==================================================

def generate_unique_email(prenom, nom):
    def clean(text):
        nfkd = unicodedata.normalize('NFKD', text)
        ascii_text = nfkd.encode(
            'ASCII',
            'ignore'
        ).decode('utf-8')

        return re.sub(
            r'[^a-zA-Z0-9]',
            '',
            ascii_text
        ).lower()

    prenom_clean = clean(prenom)
    nom_clean = clean(nom)

    base_email = (
        f"{prenom_clean}.{nom_clean}@ecole.com"
    )

    email = base_email
    counter = 1

    while User.objects.filter(
        email__iexact=email
    ).exists():
        email = (
            f"{prenom_clean}."
            f"{nom_clean}"
            f"{counter}@ecole.com"
        )
        counter += 1

    return email


def generate_matricule(niveau):
    annee_suffixe = datetime.now().strftime('%y')

    code_niveau = (
        ''.join(
            c for c in niveau.code
            if c.isalpha()
        )
        .upper()[:3]
        or 'ETU'
    )

    prefix = f"{annee_suffixe}{code_niveau}"

    count = (
        Student.objects
        .filter(
            matricule__startswith=prefix
        )
        .count()
        + 1
    )

    while True:
        sequence = str(count).zfill(3)

        matricule = (
            f"{prefix}{sequence}"
        )

        student_exists = (
            Student.objects
            .filter(
                matricule=matricule
            )
            .exists()
        )

        user_exists = (
            User.objects
            .filter(
                username=matricule
            )
            .exists()
        )

        if not student_exists and not user_exists:
            return matricule

        count += 1


# ==================================================
# AJOUT ÉTUDIANT
# ==================================================

@admin_required
def admin_student_add(request):
    niveaux = Niveau.objects.order_by('code')
    filieres = Filiere.objects.order_by('nom')

    if request.method == 'POST':
        nom = request.POST.get(
            'nom',
            ''
        ).strip()

        prenom = request.POST.get(
            'prenom',
            ''
        ).strip()

        age = request.POST.get(
            'age',
            ''
        ).strip()

        niveau_id = request.POST.get('niveau')
        filiere_id = request.POST.get('filiere')

        if (
            not nom
            or not prenom
            or not age
            or not niveau_id
            or not filiere_id
        ):
            return render(
                request,
                'admin/students/ajouter.html',
                {
                    'niveaux': niveaux,
                    'filieres': filieres,
                    'error': (
                        'Veuillez renseigner '
                        'tous les champs.'
                    ),
                }
            )

        try:
            age = int(age)
        except ValueError:
            return render(
                request,
                'admin/students/ajouter.html',
                {
                    'niveaux': niveaux,
                    'filieres': filieres,
                    'error': (
                        "L'âge doit être "
                        "un nombre entier."
                    ),
                }
            )

        if age <= 0:
            return render(
                request,
                'admin/students/ajouter.html',
                {
                    'niveaux': niveaux,
                    'filieres': filieres,
                    'error': (
                        "L'âge doit être "
                        "supérieur à 0."
                    ),
                }
            )

        niveau = get_object_or_404(
            Niveau,
            id=niveau_id
        )

        filiere = get_object_or_404(
            Filiere,
            id=filiere_id
        )

        matricule = generate_matricule(niveau)

        email = generate_unique_email(
            prenom,
            nom
        )

        default_password = "Password123!"

        user = User.objects.create_user(
            username=matricule,
            email=email,
            password=default_password,
            first_name=prenom,
            last_name=nom
        )

        UserProfile.objects.filter(
            user=user
        ).update(
            role='etudiant'
        )

        Student.objects.create(
            user=user,
            matricule=matricule,
            nom=nom,
            prenom=prenom,
            age=age,
            niveau=niveau,
            filiere=filiere
        )

        messages.success(
            request,
            (
                f"Étudiant créé ! "
                f"Matricule : {matricule} / "
                f"Email : {email}"
            )
        )

        return redirect('admin_students')

    return render(
        request,
        'admin/students/ajouter.html',
        {
            'niveaux': niveaux,
            'filieres': filieres,
        }
    )


# ==================================================
# DÉTAIL ÉTUDIANT
# ==================================================

@admin_required
def admin_student_detail(request, student_id):
    student = get_object_or_404(
        Student.objects.select_related(
            'niveau',
            'filiere'
        ),
        id=student_id
    )

    return render(
        request,
        'admin/students/detail.html',
        {
            'student': student,
        }
    )


# ==================================================
# MODIFICATION ÉTUDIANT
# ==================================================

@admin_required
def admin_student_edit(request, student_id):
    student = get_object_or_404(
        Student.objects.select_related(
            'niveau',
            'filiere'
        ),
        id=student_id
    )

    niveaux = Niveau.objects.order_by('code')
    filieres = Filiere.objects.order_by('nom')

    if request.method == 'POST':
        matricule = request.POST.get(
            'matricule',
            ''
        ).strip()

        nom = request.POST.get(
            'nom',
            ''
        ).strip()

        prenom = request.POST.get(
            'prenom',
            ''
        ).strip()

        age = request.POST.get(
            'age',
            ''
        ).strip()

        niveau_id = request.POST.get('niveau')
        filiere_id = request.POST.get('filiere')

        if (
            not matricule
            or not nom
            or not prenom
            or not age
            or not niveau_id
            or not filiere_id
        ):
            return render(
                request,
                'admin/students/modifier.html',
                {
                    'student': student,
                    'niveaux': niveaux,
                    'filieres': filieres,
                    'error': (
                        'Veuillez renseigner '
                        'tous les champs.'
                    ),
                }
            )

        try:
            age = int(age)
        except ValueError:
            return render(
                request,
                'admin/students/modifier.html',
                {
                    'student': student,
                    'niveaux': niveaux,
                    'filieres': filieres,
                    'error': (
                        "L'âge doit être "
                        "un nombre entier."
                    ),
                }
            )

        if age <= 0:
            return render(
                request,
                'admin/students/modifier.html',
                {
                    'student': student,
                    'niveaux': niveaux,
                    'filieres': filieres,
                    'error': (
                        "L'âge doit être "
                        "supérieur à 0."
                    ),
                }
            )

        if (
            Student.objects
            .filter(matricule=matricule)
            .exclude(id=student.id)
            .exists()
        ):
            return render(
                request,
                'admin/students/modifier.html',
                {
                    'student': student,
                    'niveaux': niveaux,
                    'filieres': filieres,
                    'error': (
                        'Ce matricule est '
                        'déjà utilisé.'
                    ),
                }
            )

        niveau = get_object_or_404(
            Niveau,
            id=niveau_id
        )

        filiere = get_object_or_404(
            Filiere,
            id=filiere_id
        )

        student.matricule = matricule
        student.nom = nom
        student.prenom = prenom
        student.age = age
        student.niveau = niveau
        student.filiere = filiere
        student.save()

        if student.user:
            student.user.username = matricule
            student.user.first_name = prenom
            student.user.last_name = nom
            student.user.save()

        return redirect(
            'admin_student_detail',
            student_id=student.id
        )

    return render(
        request,
        'admin/students/modifier.html',
        {
            'student': student,
            'niveaux': niveaux,
            'filieres': filieres,
        }
    )


# ==================================================
# SUPPRESSION ÉTUDIANT
# ==================================================

@admin_required
def admin_student_delete(request, student_id):
    student = get_object_or_404(
        Student,
        id=student_id
    )

    if request.method == 'POST':
        student.delete()
        return redirect('admin_students')

    return redirect(
        'admin_student_detail',
        student_id=student.id
    )


# ==================================================
# PROFESSEURS
# ==================================================

@admin_required
def admin_teachers(request):
    teachers = (
        Teacher.objects
        .order_by('nom', 'prenom')
    )

    return render(
        request,
        'admin/teachers/liste.html',
        {
            'teachers': teachers,
        }
    )


@admin_required
def admin_teacher_add(request):
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
            return render(
                request,
                'admin/teachers/ajouter.html',
                {
                    'error': (
                        'Veuillez renseigner '
                        'le nom.'
                    )
                }
            )

        Teacher.objects.create(
            nom=nom,
            prenom=prenom
        )

        return redirect('admin_teachers')

    return render(
        request,
        'admin/teachers/ajouter.html'
    )


@admin_required
def admin_teacher_detail(request, teacher_id):
    teacher = get_object_or_404(
        Teacher,
        id=teacher_id
    )

    return render(
        request,
        'admin/teachers/detail.html',
        {
            'teacher': teacher,
        }
    )


@admin_required
def admin_teacher_edit(request, teacher_id):
    teacher = get_object_or_404(
        Teacher,
        id=teacher_id
    )

    if request.method == 'POST':
        identifiant = request.POST.get(
            'identifiant',
            ''
        ).strip()

        nom = request.POST.get(
            'nom',
            ''
        ).strip()

        prenom = request.POST.get(
            'prenom',
            ''
        ).strip()

        if not identifiant or not nom:
            return render(
                request,
                'admin/teachers/modifier.html',
                {
                    'teacher': teacher,
                    'error': (
                        'Veuillez renseigner '
                        'les champs obligatoires.'
                    ),
                }
            )

        if (
            Teacher.objects
            .filter(
                identifiant=identifiant
            )
            .exclude(
                id=teacher.id
            )
            .exists()
        ):
            return render(
                request,
                'admin/teachers/modifier.html',
                {
                    'teacher': teacher,
                    'error': (
                        'Cet identifiant est '
                        'déjà utilisé.'
                    ),
                }
            )

        teacher.identifiant = identifiant
        teacher.nom = nom
        teacher.prenom = prenom or None
        teacher.save()

        return redirect(
            'admin_teacher_detail',
            teacher_id=teacher.id
        )

    return render(
        request,
        'admin/teachers/modifier.html',
        {
            'teacher': teacher,
        }
    )


@admin_required
def admin_teacher_delete(request, teacher_id):
    teacher = get_object_or_404(
        Teacher,
        id=teacher_id
    )

    if request.method == 'POST':
        teacher.delete()
        return redirect('admin_teachers')

    return redirect(
        'admin_teacher_detail',
        teacher_id=teacher.id
    )


# ==================================================
# MATIÈRES
# ==================================================
@admin_required
def admin_subjects(request):

    enseignements = (
        Enseignement.objects
        .select_related(
            'subject',
            'teacher',
            'semestre',
            'semestre__niveau',
            'filiere'
        )
        .order_by(
            'subject__nom',
            'semestre__niveau__code',
            'filiere__code',
            'teacher__nom'
        )
    )

    return render(
        request,
        'admin/subjects/liste.html',
        {
            'enseignements': enseignements,
        }
    )

    
@admin_required
def admin_subject_add(request):

    semestres = (
        Semestre.objects
        .select_related('niveau')
        .order_by(
            'niveau__code',
            'nom'
        )
    )

    filieres = (
        Filiere.objects
        .order_by(
            'code',
            'nom'
        )
    )

    teachers = (
        Teacher.objects
        .order_by(
            'nom',
            'prenom'
        )
    )

    if request.method == 'POST':

        nom = request.POST.get(
            'nom',
            ''
        ).strip()

        credits = request.POST.get(
            'credits',
            ''
        ).strip()

        semestre_id = request.POST.get(
            'semestre'
        )

        filiere_id = request.POST.get(
            'filiere'
        )

        teacher_ids = request.POST.getlist(
            'teachers'
        )


        if not nom:

            return render(
                request,
                'admin/subjects/ajouter.html',
                {
                    'semestres': semestres,
                    'filieres': filieres,
                    'teachers': teachers,
                    'error': (
                        'Le nom de la matière '
                        'est obligatoire.'
                    ),
                }
            )


        if not semestre_id:

            return render(
                request,
                'admin/subjects/ajouter.html',
                {
                    'semestres': semestres,
                    'filieres': filieres,
                    'teachers': teachers,
                    'error': (
                        'Veuillez sélectionner '
                        'un semestre.'
                    ),
                }
            )


        if not filiere_id:

            return render(
                request,
                'admin/subjects/ajouter.html',
                {
                    'semestres': semestres,
                    'filieres': filieres,
                    'teachers': teachers,
                    'error': (
                        'Veuillez sélectionner '
                        'une filière.'
                    ),
                }
            )


        if not teacher_ids:

            return render(
                request,
                'admin/subjects/ajouter.html',
                {
                    'semestres': semestres,
                    'filieres': filieres,
                    'teachers': teachers,
                    'error': (
                        'Veuillez sélectionner '
                        'au moins un professeur.'
                    ),
                }
            )


        if Subject.objects.filter(
            nom=nom
        ).exists():

            return render(
                request,
                'admin/subjects/ajouter.html',
                {
                    'semestres': semestres,
                    'filieres': filieres,
                    'teachers': teachers,
                    'error': (
                        'Cette matière '
                        'existe déjà.'
                    ),
                }
            )


        semestre = get_object_or_404(
            Semestre,
            id=semestre_id
        )


        filiere = get_object_or_404(
            Filiere,
            id=filiere_id
        )


        subject = Subject.objects.create(
            nom=nom,
            credits=credits or None,
            semestre=semestre
        )


        subject.teachers.set(
            teacher_ids
        )


        for teacher_id in teacher_ids:

            teacher = get_object_or_404(
                Teacher,
                id=teacher_id
            )

            Enseignement.objects.get_or_create(
                subject=subject,
                teacher=teacher,
                semestre=semestre,
                filiere=filiere
            )


        return redirect(
            'admin_subjects'
        )


    return render(
        request,
        'admin/subjects/ajouter.html',
        {
            'semestres': semestres,
            'filieres': filieres,
            'teachers': teachers,
        }
    )

@admin_required
def admin_subject_detail(request, subject_id):
    subject = get_object_or_404(
        Subject.objects
        .select_related(
            'semestre',
            'semestre__niveau'
        )
        .prefetch_related('teachers'),
        id=subject_id
    )

    return render(
        request,
        'admin/subjects/detail.html',
        {
            'subject': subject,
        }
    )


@admin_required
def admin_subject_edit(request, subject_id):
    subject = get_object_or_404(
        Subject,
        id=subject_id
    )

    semestres = (
        Semestre.objects
        .select_related('niveau')
        .order_by(
            'niveau__code',
            'nom'
        )
    )

    teachers = Teacher.objects.order_by(
        'nom',
        'prenom'
    )

    if request.method == 'POST':
        nom = request.POST.get(
            'nom',
            ''
        ).strip()

        credits = request.POST.get(
            'credits',
            ''
        ).strip()

        semestre_id = request.POST.get('semestre')

        teacher_ids = request.POST.getlist(
            'teachers'
        )

        if not nom:
            return render(
                request,
                'admin/subjects/modifier.html',
                {
                    'subject': subject,
                    'semestres': semestres,
                    'teachers': teachers,
                    'error': (
                        'Le nom de la matière '
                        'est obligatoire.'
                    ),
                }
            )

        if (
            Subject.objects
            .filter(nom=nom)
            .exclude(id=subject.id)
            .exists()
        ):
            return render(
                request,
                'admin/subjects/modifier.html',
                {
                    'subject': subject,
                    'semestres': semestres,
                    'teachers': teachers,
                    'error': (
                        'Cette matière '
                        'existe déjà.'
                    ),
                }
            )

        subject.nom = nom
        subject.credits = credits or None
        subject.semestre_id = semestre_id or None
        subject.save()

        subject.teachers.set(teacher_ids)

        return redirect(
            'admin_subject_detail',
            subject_id=subject.id
        )

    return render(
        request,
        'admin/subjects/modifier.html',
        {
            'subject': subject,
            'semestres': semestres,
            'teachers': teachers,
        }
    )


@admin_required
def admin_subject_delete(request, subject_id):
    subject = get_object_or_404(
        Subject,
        id=subject_id
    )

    if request.method == 'POST':
        subject.delete()
        return redirect('admin_subjects')

    return redirect(
        'admin_subject_detail',
        subject_id=subject.id
    )


# ==================================================
# NOTES
# ==================================================

@admin_required
def admin_grades(request):
    grades = (
        Grade.objects
        .select_related(
            'student',
            'evaluation',
            'evaluation__subject',
            'evaluation__annee_universitaire'
        )
        .order_by(
            '-evaluation__date',
            'student__nom'
        )
    )

    return render(
        request,
        'admin/grades/liste.html',
        {
            'grades': grades,
        }
    )


@admin_required
def admin_grade_add(request):
    students = Student.objects.order_by(
        'nom',
        'prenom'
    )

    subjects = (
        Subject.objects
        .select_related(
            'semestre',
            'semestre__niveau'
        )
        .order_by('nom')
    )

    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')

        type_evaluation = request.POST.get(
            'type_evaluation'
        )

        session = request.POST.get(
            'session',
            1
        )

        note = request.POST.get(
            'note',
            ''
        ).strip()

        if (
            not student_id
            or not subject_id
            or not type_evaluation
            or not note
        ):
            return render(
                request,
                'admin/grades/saisir.html',
                {
                    'students': students,
                    'subjects': subjects,
                    'error': (
                        'Veuillez renseigner '
                        'tous les champs.'
                    ),
                }
            )

        try:
            note = float(note)
        except ValueError:
            return render(
                request,
                'admin/grades/saisir.html',
                {
                    'students': students,
                    'subjects': subjects,
                    'error': (
                        'La note doit être '
                        'numérique.'
                    ),
                }
            )

        if note < 0 or note > 20:
            return render(
                request,
                'admin/grades/saisir.html',
                {
                    'students': students,
                    'subjects': subjects,
                    'error': (
                        'La note doit être '
                        'comprise entre 0 et 20.'
                    ),
                }
            )

        annee_univ = (
            AnneeUniversitaire.objects
            .filter(active=True)
            .first()
        )

        if not annee_univ:
            annee_univ = (
                AnneeUniversitaire.objects
                .order_by('-id')
                .first()
            )

        if not annee_univ:
            return render(
                request,
                'admin/grades/saisir.html',
                {
                    'students': students,
                    'subjects': subjects,
                    'error': (
                        'Aucune année universitaire '
                        'configurée dans le système.'
                    ),
                }
            )

        try:
            session = int(session)
        except (ValueError, TypeError):
            session = 1

        evaluation, created = (
            Evaluation.objects.get_or_create(
                subject_id=subject_id,
                type_evaluation=type_evaluation,
                session=session,
                annee_universitaire=annee_univ,
                defaults={
                    'date': timezone.now().date(),
                }
            )
        )

        Grade.objects.update_or_create(
            student_id=student_id,
            evaluation=evaluation,
            defaults={
                'note': note
            }
        )

        return redirect('admin_grades')

    return render(
        request,
        'admin/grades/saisir.html',
        {
            'students': students,
            'subjects': subjects,
        }
    )


@admin_required
def admin_grade_history(request):
    grades = (
        Grade.objects
        .select_related(
            'student',
            'evaluation',
            'evaluation__subject',
            'evaluation__annee_universitaire'
        )
        .order_by(
            'student__nom',
            '-evaluation__date'
        )
    )

    return render(
        request,
        'admin/grades/historique.html',
        {
            'grades': grades,
        }
    )


# ==================================================
# ABSENCES
# ==================================================

@admin_required
def admin_absences(request):
    absences = (
        Absence.objects
        .select_related(
            'student',
            'subject'
        )
        .order_by('-date_absence')
    )

    return render(
        request,
        'admin/absences/liste.html',
        {
            'absences': absences,
        }
    )


@admin_required
def admin_absence_add(request):
    students = Student.objects.order_by(
        'nom',
        'prenom'
    )

    subjects = Subject.objects.order_by('nom')

    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')

        type_evaluation = request.POST.get(
            'type_evaluation'
        )

        date_absence = request.POST.get(
            'date_absence'
        )

        if (
            not student_id
            or not subject_id
            or not type_evaluation
            or not date_absence
        ):
            return render(
                request,
                'admin/absences/enregistrer.html',
                {
                    'students': students,
                    'subjects': subjects,
                    'error': (
                        'Veuillez renseigner '
                        'tous les champs.'
                    ),
                }
            )

        Absence.objects.create(
            student_id=student_id,
            subject_id=subject_id,
            type_evaluation=type_evaluation,
            date_absence=date_absence
        )

        return redirect('admin_absences')

    return render(
        request,
        'admin/absences/enregistrer.html',
        {
            'students': students,
            'subjects': subjects,
        }
    )


@admin_required
def admin_absence_detail(request, absence_id):
    absence = get_object_or_404(
        Absence.objects.select_related(
            'student',
            'subject'
        ),
        id=absence_id
    )

    return render(
        request,
        'admin/absences/detail.html',
        {
            'absence': absence,
        }
    )


@admin_required
def admin_absence_edit(request, absence_id):
    absence = get_object_or_404(
        Absence,
        id=absence_id
    )

    students = Student.objects.order_by(
        'nom',
        'prenom'
    )

    subjects = Subject.objects.order_by('nom')

    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')

        type_evaluation = request.POST.get(
            'type_evaluation'
        )

        date_absence = request.POST.get(
            'date_absence'
        )

        if (
            not student_id
            or not subject_id
            or not type_evaluation
            or not date_absence
        ):
            return render(
                request,
                'admin/absences/modifier.html',
                {
                    'absence': absence,
                    'students': students,
                    'subjects': subjects,
                    'error': (
                        'Veuillez renseigner '
                        'tous les champs.'
                    ),
                }
            )

        absence.student_id = student_id
        absence.subject_id = subject_id
        absence.type_evaluation = type_evaluation
        absence.date_absence = date_absence
        absence.save()

        return redirect('admin_absences')

    return render(
        request,
        'admin/absences/modifier.html',
        {
            'absence': absence,
            'students': students,
            'subjects': subjects,
        }
    )


@admin_required
def admin_absence_delete(request, absence_id):
    absence = get_object_or_404(
        Absence,
        id=absence_id
    )

    if request.method == 'POST':
        absence.delete()

    return redirect('admin_absences')


@admin_required
def admin_absence_justify(request, absence_id):
    absence = get_object_or_404(
        Absence,
        id=absence_id
    )

    if request.method == 'POST':
        absence.justifiee = True
        absence.justification = (
            request.POST.get(
                'justification',
                ''
            ).strip()
        )

        absence.date_justification = (
            request.POST.get(
                'date_justification'
            )
            or None
        )

        absence.save()

        return redirect('admin_absences')

    return render(
        request,
        'admin/absences/justifier.html',
        {
            'absence': absence,
        }
    )


@admin_required
def admin_absence_makeup(request, absence_id):
    absence = get_object_or_404(
        Absence,
        id=absence_id
    )

    if request.method == 'POST':
        note_rattrapage_str = (
            request.POST.get(
                'note_rattrapage',
                ''
            ).strip()
        )

        note_rattrapage = None

        if note_rattrapage_str:
            try:
                note_rattrapage = float(
                    note_rattrapage_str
                )

                if (
                    note_rattrapage < 0
                    or note_rattrapage > 20
                ):
                    return render(
                        request,
                        'admin/absences/rattrapage.html',
                        {
                            'absence': absence,
                            'error': (
                                'La note doit être '
                                'comprise entre 0 et 20.'
                            ),
                        }
                    )

            except ValueError:
                return render(
                    request,
                    'admin/absences/rattrapage.html',
                    {
                        'absence': absence,
                        'error': (
                            'La note doit être '
                            'un nombre valide.'
                        ),
                    }
                )

        absence.rattrapage_effectue = True
        absence.note_rattrapage = note_rattrapage
        absence.date_rattrapage = (
            request.POST.get(
                'date_rattrapage'
            )
            or None
        )

        absence.save()

        return redirect('admin_absences')

    return render(
        request,
        'admin/absences/rattrapage.html',
        {
            'absence': absence,
        }
    )


# ==================================================
# FILIÈRES
# ==================================================

@admin_required
def admin_filieres(request):
    filieres = (
        Filiere.objects
        .prefetch_related('niveaux')
        .order_by('nom')
    )

    return render(
        request,
        'admin/academic/filieres.html',
        {
            'filieres': filieres,
        }
    )


@admin_required
def admin_filiere_add(request):
    niveaux = Niveau.objects.order_by('code')

    if request.method == 'POST':
        code = request.POST.get(
            'code',
            ''
        ).strip()

        nom = request.POST.get(
            'nom',
            ''
        ).strip()

        niveaux_ids = request.POST.getlist(
            'niveaux'
        )

        if not code or not nom:
            return render(
                request,
                'admin/academic/filiere_ajouter.html',
                {
                    'niveaux': niveaux,
                    'error': (
                        'Le code et le nom '
                        'de la filière sont obligatoires.'
                    ),
                }
            )

        if (
            Filiere.objects
            .filter(code__iexact=code)
            .exists()
        ):
            return render(
                request,
                'admin/academic/filiere_ajouter.html',
                {
                    'niveaux': niveaux,
                    'error': (
                        'Une filière avec '
                        'ce code existe déjà.'
                    ),
                }
            )

        filiere = Filiere.objects.create(
            code=code,
            nom=nom
        )

        if niveaux_ids:
            filiere.niveaux.set(niveaux_ids)

        messages.success(
            request,
            'Filière ajoutée avec succès !'
        )

        return redirect('admin_filieres')

    return render(
        request,
        'admin/academic/filiere_ajouter.html',
        {
            'niveaux': niveaux,
        }
    )


@admin_required
def admin_filiere_edit(request, pk):
    filiere = get_object_or_404(
        Filiere,
        pk=pk
    )

    niveaux = Niveau.objects.order_by('code')

    if request.method == 'POST':
        code = request.POST.get(
            'code',
            ''
        ).strip()

        nom = request.POST.get(
            'nom',
            ''
        ).strip()

        niveaux_ids = request.POST.getlist(
            'niveaux'
        )

        if not code or not nom:
            return render(
                request,
                'admin/academic/filiere_modifier.html',
                {
                    'error': (
                        'Veuillez renseigner '
                        'tous les champs obligatoires.'
                    ),
                    'filiere': filiere,
                    'niveaux': niveaux
                }
            )

        if (
            Filiere.objects
            .filter(code__iexact=code)
            .exclude(pk=pk)
            .exists()
        ):
            return render(
                request,
                'admin/academic/filiere_modifier.html',
                {
                    'error': (
                        'Ce code de filière '
                        'existe déjà.'
                    ),
                    'filiere': filiere,
                    'niveaux': niveaux
                }
            )

        filiere.code = code
        filiere.nom = nom
        filiere.save()

        filiere.niveaux.set(niveaux_ids)

        messages.success(
            request,
            'Filière modifiée avec succès !'
        )

        return redirect('admin_filieres')

    return render(
        request,
        'admin/academic/filiere_modifier.html',
        {
            'filiere': filiere,
            'niveaux': niveaux
        }
    )


@admin_required
def admin_filiere_delete(request, pk):
    if request.method == 'POST':
        filiere = get_object_or_404(
            Filiere,
            pk=pk
        )

        filiere.delete()

        messages.success(
            request,
            'Filière supprimée avec succès !'
        )

    return redirect('admin_filieres')


# ==================================================
# NIVEAUX
# ==================================================

@admin_required
def admin_niveaux(request):
    niveaux = (
        Niveau.objects
        .prefetch_related('filieres')
        .order_by('code')
    )

    return render(
        request,
        'admin/academic/niveaux.html',
        {
            'niveaux': niveaux,
        }
    )


@admin_required
def admin_niveau_add(request):
    if request.method == 'POST':
        code = request.POST.get(
            'code',
            ''
        ).strip()

        nom = request.POST.get(
            'nom',
            ''
        ).strip()

        if not code or not nom:
            return render(
                request,
                'admin/academic/niveau_ajouter.html',
                {
                    'error': (
                        'Veuillez renseigner '
                        'tous les champs.'
                    ),
                }
            )

        if (
            Niveau.objects
            .filter(code__iexact=code)
            .exists()
        ):
            return render(
                request,
                'admin/academic/niveau_ajouter.html',
                {
                    'error': (
                        'Ce code de niveau '
                        'existe déjà.'
                    ),
                }
            )

        Niveau.objects.create(
            code=code,
            nom=nom
        )

        messages.success(
            request,
            'Niveau créé avec succès !'
        )

        return redirect('admin_niveaux')

    return render(
        request,
        'admin/academic/niveau_ajouter.html'
    )


@admin_required
def admin_niveau_edit(request, pk):
    niveau = get_object_or_404(
        Niveau,
        pk=pk
    )

    if request.method == 'POST':
        code = request.POST.get(
            'code',
            ''
        ).strip()

        nom = request.POST.get(
            'nom',
            ''
        ).strip()

        if not code or not nom:
            return render(
                request,
                'admin/academic/niveau_modifier.html',
                {
                    'error': (
                        'Veuillez renseigner '
                        'tous les champs.'
                    ),
                    'niveau': niveau
                }
            )

        if (
            Niveau.objects
            .filter(code__iexact=code)
            .exclude(pk=pk)
            .exists()
        ):
            return render(
                request,
                'admin/academic/niveau_modifier.html',
                {
                    'error': (
                        'Ce code de niveau '
                        'existe déjà.'
                    ),
                    'niveau': niveau
                }
            )

        niveau.code = code
        niveau.nom = nom
        niveau.save()

        messages.success(
            request,
            'Niveau modifié avec succès !'
        )

        return redirect('admin_niveaux')

    return render(
        request,
        'admin/academic/niveau_modifier.html',
        {
            'niveau': niveau
        }
    )


@admin_required
def admin_niveau_delete(request, pk):
    if request.method == 'POST':
        niveau = get_object_or_404(
            Niveau,
            pk=pk
        )

        niveau.delete()

        messages.success(
            request,
            'Niveau supprimé avec succès !'
        )

    return redirect('admin_niveaux')


# ==================================================
# SEMESTRES
# ==================================================

@admin_required
def admin_semestres(request):
    semestres = (
        Semestre.objects
        .select_related('niveau')
        .order_by(
            'niveau__code',
            'nom'
        )
    )

    return render(
        request,
        'admin/academic/semestres.html',
        {
            'semestres': semestres,
        }
    )


@admin_required
def admin_semestre_edit(request, semestre_id):
    semestre = get_object_or_404(
        Semestre,
        id=semestre_id
    )

    if request.method == 'POST':
        date_debut = request.POST.get(
            'date_debut'
        )

        date_fin = request.POST.get(
            'date_fin'
        )

        if date_debut and date_fin:
            semestre.date_debut = date_debut
            semestre.date_fin = date_fin
            semestre.save()

            return redirect('admin_semestres')

    return render(
        request,
        'admin/academic/semestre_modifier.html',
        {
            'semestre': semestre,
        }
    )


@admin_required
def admin_semestre_add(request):
    niveaux = Niveau.objects.order_by('code')
    semestre_choices = Semestre.SEMESTRE_CHOICES

    if request.method == 'POST':
        nom = request.POST.get(
            'nom',
            ''
        ).strip()

        niveau_id = request.POST.get('niveau')

        date_debut = request.POST.get(
            'date_debut'
        )

        date_fin = request.POST.get(
            'date_fin'
        )

        if not nom or not niveau_id:
            return render(
                request,
                'admin/academic/semestres_ajouter.html',
                {
                    'niveaux': niveaux,
                    'semestre_choices': semestre_choices,
                    'error': (
                        'Le semestre et le '
                        'niveau sont obligatoires.'
                    ),
                }
            )

        niveau = get_object_or_404(
            Niveau,
            id=niveau_id
        )

        semestre, created = (
            Semestre.objects.get_or_create(
                nom=nom,
                niveau=niveau,
                defaults={
                    'date_debut': (
                        date_debut
                        if date_debut
                        else None
                    ),
                    'date_fin': (
                        date_fin
                        if date_fin
                        else None
                    ),
                }
            )
        )

        if (
            not created
            and (
                date_debut
                or date_fin
            )
        ):
            semestre.date_debut = (
                date_debut
                if date_debut
                else semestre.date_debut
            )

            semestre.date_fin = (
                date_fin
                if date_fin
                else semestre.date_fin
            )

            semestre.save()

        return redirect('admin_semestres')

    return render(
        request,
        'admin/academic/semestres_ajouter.html',
        {
            'niveaux': niveaux,
            'semestre_choices': semestre_choices,
        }
    )


@admin_required
def admin_semestre_delete(request, semestre_id):
    semestre = get_object_or_404(
        Semestre,
        id=semestre_id
    )

    if request.method == 'POST':
        semestre.delete()

    return redirect('admin_semestres')


# ==================================================
# ANNÉES UNIVERSITAIRES
# ==================================================

@admin_required
def admin_annees(request):
    annees = (
        AnneeUniversitaire.objects
        .order_by('-libelle')
    )

    return render(
        request,
        'admin/academic/annees.html',
        {
            'annees': annees,
        }
    )


@admin_required
def admin_annee_add(request):
    if request.method == 'POST':
        libelle = request.POST.get(
            'libelle',
            ''
        ).strip()

        date_debut = request.POST.get(
            'date_debut'
        )

        date_fin = request.POST.get(
            'date_fin'
        )

        active = (
            request.POST.get(
                'est_active'
            ) == 'on'
        )

        if (
            not libelle
            or not date_debut
            or not date_fin
        ):
            return render(
                request,
                'admin/academic/annee_ajouter.html',
                {
                    'error': (
                        'Tous les champs obligatoires '
                        '(libellé et dates) doivent '
                        'être remplis.'
                    ),
                }
            )

        if (
            AnneeUniversitaire.objects
            .filter(libelle=libelle)
            .exists()
        ):
            return render(
                request,
                'admin/academic/annee_ajouter.html',
                {
                    'error': (
                        'Cette année universitaire '
                        'existe déjà.'
                    ),
                }
            )

        if active:
            (
                AnneeUniversitaire.objects
                .filter(active=True)
                .update(active=False)
            )

        AnneeUniversitaire.objects.create(
            libelle=libelle,
            date_debut=date_debut,
            date_fin=date_fin,
            active=active
        )

        return redirect('admin_annees')

    return render(
        request,
        'admin/academic/annee_ajouter.html'
    )


@admin_required
def admin_annee_edit(request, pk):
    annee = get_object_or_404(
        AnneeUniversitaire,
        pk=pk
    )

    if request.method == 'POST':
        libelle = request.POST.get(
            'libelle',
            ''
        ).strip()

        date_debut = request.POST.get(
            'date_debut'
        )

        date_fin = request.POST.get(
            'date_fin'
        )

        active = (
            request.POST.get(
                'est_active'
            ) == 'on'
        )

        if (
            not libelle
            or not date_debut
            or not date_fin
        ):
            return render(
                request,
                'admin/academic/annee_modifier.html',
                {
                    'annee': annee,
                    'error': (
                        'Tous les champs obligatoires '
                        '(libellé et dates) doivent '
                        'être remplis.'
                    ),
                }
            )

        if (
            AnneeUniversitaire.objects
            .filter(libelle=libelle)
            .exclude(pk=pk)
            .exists()
        ):
            return render(
                request,
                'admin/academic/annee_modifier.html',
                {
                    'annee': annee,
                    'error': (
                        'Cette année universitaire '
                        'existe déjà.'
                    ),
                }
            )

        if active:
            (
                AnneeUniversitaire.objects
                .filter(active=True)
                .exclude(pk=pk)
                .update(active=False)
            )

        annee.libelle = libelle
        annee.date_debut = date_debut
        annee.date_fin = date_fin
        annee.active = active
        annee.save()

        return redirect('admin_annees')

    return render(
        request,
        'admin/academic/annee_modifier.html',
        {
            'annee': annee,
        }
    )


@admin_required
def admin_annee_delete(request, pk):
    if request.method == 'POST':
        annee = get_object_or_404(
            AnneeUniversitaire,
            pk=pk
        )

        annee.delete()

    return redirect('admin_annees')


# ==================================================
# ARRIÉRÉS
# ==================================================

@admin_required
def admin_arrieres(request):
    arrieres = (
        Arriere.objects
        .select_related(
            'progression',
            'progression__student',
            'subject'
        )
        .order_by(
            'statut',
            'progression__student__nom'
        )
    )

    return render(
        request,
        'admin/academic/arrieres.html',
        {
            'arrieres': arrieres,
        }
    )


@admin_required
def admin_arriere_add(request):
    progressions = (
        Progression.objects
        .select_related(
            'student',
            'annee_universitaire',
            'niveau'
        )
        .order_by(
            'student__nom',
            'student__prenom'
        )
    )

    subjects = Subject.objects.order_by('nom')

    if request.method == 'POST':
        progression_id = request.POST.get(
            'progression'
        )

        subject_id = request.POST.get(
            'subject'
        )

        statut = request.POST.get(
            'statut',
            'A_RATTRAPER'
        )

        if (
            not progression_id
            or not subject_id
        ):
            return render(
                request,
                'admin/academic/arriere_ajouter.html',
                {
                    'progressions': progressions,
                    'subjects': subjects,
                    'error': (
                        "L'étudiant/progression "
                        "et la matière sont obligatoires."
                    ),
                }
            )

        progression = get_object_or_404(
            Progression,
            id=progression_id
        )

        subject = get_object_or_404(
            Subject,
            id=subject_id
        )

        Arriere.objects.create(
            progression=progression,
            subject=subject,
            statut=statut
        )

        return redirect('admin_arrieres')

    return render(
        request,
        'admin/academic/arriere_ajouter.html',
        {
            'progressions': progressions,
            'subjects': subjects,
        }
    )


@admin_required
def admin_arriere_edit(request, arriere_id):
    arriere = get_object_or_404(
        Arriere,
        id=arriere_id
    )

    progressions = (
        Progression.objects
        .select_related(
            'student',
            'annee_universitaire',
            'niveau'
        )
        .order_by(
            'student__nom',
            'student__prenom'
        )
    )

    subjects = Subject.objects.order_by('nom')

    if request.method == 'POST':
        progression_id = request.POST.get(
            'progression'
        )

        subject_id = request.POST.get(
            'subject'
        )

        statut = request.POST.get(
            'statut',
            arriere.statut
        )

        if (
            not progression_id
            or not subject_id
        ):
            return render(
                request,
                'admin/academic/arriere_modifier.html',
                {
                    'arriere': arriere,
                    'progressions': progressions,
                    'subjects': subjects,
                    'error': (
                        "L'étudiant/progression "
                        "et la matière sont obligatoires."
                    ),
                }
            )

        progression = get_object_or_404(
            Progression,
            id=progression_id
        )

        subject = get_object_or_404(
            Subject,
            id=subject_id
        )

        arriere.progression = progression
        arriere.subject = subject
        arriere.statut = statut
        arriere.save()

        return redirect('admin_arrieres')

    return render(
        request,
        'admin/academic/arriere_modifier.html',
        {
            'arriere': arriere,
            'progressions': progressions,
            'subjects': subjects,
        }
    )


# ==================================================
# GÉNÉRATION AUTOMATIQUE DES ARRIÉRÉS
# ==================================================

def verifier_et_generer_arrieres(progression):
    moyennes_par_matiere = (
        Grade.objects
        .filter(
            student=progression.student,
            evaluation__annee_universitaire=(
                progression.annee_universitaire
            )
        )
        .values(
            'evaluation__subject'
        )
        .annotate(
            moyenne=Avg('note')
        )
    )

    for item in moyennes_par_matiere:
        subject_id = item[
            'evaluation__subject'
        ]

        moyenne = item['moyenne']

        if (
            subject_id
            and moyenne is not None
            and moyenne < 10
        ):
            Arriere.objects.get_or_create(
                progression=progression,
                subject_id=subject_id,
                defaults={
                    'statut': 'A_RATTRAPER'
                }
            )


@admin_required
def admin_generer_arrieres_automatique(request):
    progressions = (
        Progression.objects
        .select_related(
            'student',
            'annee_universitaire'
        )
    )

    for progression in progressions:
        verifier_et_generer_arrieres(
            progression
        )

    messages.success(
        request,
        'Les arriérés ont été générés automatiquement.'
    )

    return redirect('admin_arrieres')


# ==================================================
# OUTIL : PROFESSEUR CONNECTÉ
# ==================================================

def get_current_teacher(request):
    teacher = (
        Teacher.objects
        .filter(
            user=request.user
        )
        .first()
    )

    if teacher:
        return teacher

    teacher = (
        Teacher.objects
        .filter(
            identifiant__iexact=request.user.username
        )
        .first()
    )

    if teacher:
        return teacher

    teacher = (
        Teacher.objects
        .filter(
            identifiant__iexact=request.user.email
        )
        .first()
    )

    return teacher


# ==================================================
# DASHBOARD PROFESSEUR
# ==================================================

@professeur_required
def professeur_dashboard(request):
    """
    Tableau de bord du professeur.

    Logique principale :

        Professeur
            ↓
        Enseignements
            ↓
        Matières + niveaux + filières

    Les évaluations, notes et absences sont ensuite
    filtrées à partir des matières enseignées.
    """

    teacher = get_current_teacher(request)

    if not teacher:
        return redirect('professeur_dashboard')

    # ============================================================
    # ENSEIGNEMENTS DU PROFESSEUR
    # ============================================================

    enseignements = (
        Enseignement.objects
        .filter(
            teacher=teacher
        )
        .select_related(
            'subject',
            'semestre',
            'semestre__niveau',
            'filiere'
        )
        .distinct()
    )

    # Une ligne = une affectation matière + niveau + filière
    total_subjects = enseignements.count()

    # ============================================================
    # ÉVALUATIONS DU PROFESSEUR
    # ============================================================

    evaluations = (
        Evaluation.objects
        .filter(
            subject__in=enseignements.values('subject_id')
        )
        .select_related(
            'subject',
            'annee_universitaire'
        )
        .distinct()
        .order_by(
            '-date',
            '-id'
        )
    )

    total_evaluations = evaluations.count()

    recent_evaluations = evaluations[:5]

    # ============================================================
    # ABSENCES DU PROFESSEUR
    # ============================================================

    absences = (
        Absence.objects
        .filter(
            subject__in=enseignements.values('subject_id')
        )
        .select_related(
            'student',
            'subject'
        )
        .distinct()
    )

    total_absences = absences.count()

    # ============================================================
    # NOTES DU PROFESSEUR
    # ============================================================

    notes = (
        Grade.objects
        .filter(
            evaluation__subject__in=enseignements.values('subject_id')
        )
        .select_related(
            'student',
            'evaluation',
            'evaluation__subject'
        )
        .distinct()
        .order_by(
            '-evaluation__date',
            '-evaluation__id',
            '-id'
        )
    )

    recent_notes = notes[:5]

    # ============================================================
    # AFFICHAGE
    # ============================================================

    return render(
        request,
        'professeur/dashboard/dashboard.html',
        {
            'teacher': teacher,

            'total_subjects': total_subjects,
            'total_evaluations': total_evaluations,
            'total_absences': total_absences,

            'recent_evaluations': recent_evaluations,
            'recent_notes': recent_notes,
        }
    )


# ==================================================
# ÉVALUATIONS PROFESSEUR
# ==================================================

@professeur_required
def professeur_evaluations(request):

    teacher = get_current_teacher(request)

    if not teacher:
        return redirect(
            'professeur_dashboard'
        )

    evaluations = (
        Evaluation.objects
        .filter(
            subject__teachers=teacher
        )
        .select_related(
            'subject',
            'subject__semestre',
            'subject__semestre__niveau',
            'annee_universitaire',
        )
        .distinct()
        .order_by(
            '-date',
            '-id',
        )
    )

    return render(
        request,
        'professeur/evaluations/liste.html',
        {
            'teacher': teacher,
            'evaluations': evaluations,
        }
    )


# ==================================================
# AJOUTER UNE ÉVALUATION (PROFESSEUR)
# ==================================================
@professeur_required
def professeur_evaluation_ajouter(request):
    """
    Permet au professeur de créer une évaluation.
    Logique :

        Professeur
            ↓
        Ses matières
            ↓
        Évaluation
            ↓
        Année universitaire active

    Le professeur ne peut créer une évaluation
    que pour une matière qui lui est affectée.
    """

    teacher = get_current_teacher(request)

    if not teacher:
        return redirect('professeur_evaluations')

    subjects = (
        Subject.objects
        .filter(
            teachers=teacher
        )
        .select_related(
            'semestre',
            'semestre__niveau'
        )
        .distinct()
        .order_by(
            'nom'
        )
    )

    if request.method == 'POST':

        subject_id = request.POST.get('subject')
        type_evaluation = request.POST.get('type_evaluation')
        session = request.POST.get('session', 1)
        date_evaluation = request.POST.get('date_evaluation')

        if not subject_id or not type_evaluation:
            return render(
                request,
                'professeur/evaluations/ajouter.html',
                {
                    'subjects': subjects,
                    'error': (
                        'Veuillez renseigner tous les champs obligatoires.'
                    )
                }
            )

        subject = get_object_or_404(
            Subject,
            id=subject_id,
            teachers=teacher
        )

        try:
            session = int(session)
        except (ValueError, TypeError):
            session = 1

        # ============================================================
        # ANNÉE UNIVERSITAIRE ACTIVE
        # ============================================================

        annee_univ = (
            AnneeUniversitaire.objects
            .filter(
                active=True
            )
            .first()
        )

        # Si aucune année n'est active,
        # on prend la dernière année enregistrée.
        if not annee_univ:

            annee_univ = (
                AnneeUniversitaire.objects
                .order_by('-id')
                .first()
            )

        if not annee_univ:

            return render(
                request,
                'professeur/evaluations/ajouter.html',
                {
                    'subjects': subjects,
                    'error': (
                        'Aucune année universitaire n’est configurée.'
                    )
                }
            )

        # ============================================================
        # DATE DE L'ÉVALUATION
        # ============================================================

        evaluation_date = (
            date_evaluation
            if date_evaluation
            else timezone.now().date()
        )

        # ============================================================
        # CRÉATION DE L'ÉVALUATION
        # ============================================================

        Evaluation.objects.get_or_create(
            subject=subject,
            type_evaluation=type_evaluation,
            session=session,
            annee_universitaire=annee_univ,
            defaults={
                'date': evaluation_date
            }
        )

        return redirect(
            'professeur_evaluations'
        )

    return render(
        request,
        'professeur/evaluations/ajouter.html',
        {
            'subjects': subjects
        }
    )

# ==================================================
# DÉTAIL ÉVALUATION PROFESSEUR
# ==================================================

@professeur_required
def professeur_evaluation_detail(request, pk):

    teacher = get_current_teacher(request)

    if not teacher:
        return redirect(
            'professeur_evaluations'
        )

    evaluation = get_object_or_404(
        Evaluation.objects.select_related(
            'subject',
            'annee_universitaire',
        ),
        pk=pk,
        subject__teachers=teacher,
    )

    return render(
        request,
        'professeur/evaluations/detail.html',
        {
            'evaluation': evaluation,
        }
    )



# ==================================================
# MODIFICATION ÉVALUATION PROFESSEUR
# ==================================================
@professeur_required
def professeur_evaluation_modifier(request, pk):
    teacher = get_current_teacher(request)
    if not teacher:
        return redirect(
            'professeur_evaluations'
        )

    evaluation = get_object_or_404(
        Evaluation,
        pk=pk,
        subject__teachers=teacher
    )

    subjects = (
        Subject.objects
        .filter(
            teachers=teacher
        )
        .select_related(
            'semestre',
            'semestre__niveau'
        )
        .distinct()
        .order_by('nom')
    )

    if request.method == 'POST':
        subject_id = request.POST.get(
            'subject'
        )

        type_evaluation = request.POST.get(
            'type_evaluation'
        )

        session = request.POST.get(
            'session',
            1
        )

        date_evaluation = request.POST.get(
            'date_evaluation'
        )

        if (
            not subject_id
            or not type_evaluation
            or not date_evaluation
        ):
            return render(
                request,
                'professeur/evaluations/modifier.html',
                {
                    'evaluation': evaluation,
                    'subjects': subjects,
                    'error': (
                        'Veuillez renseigner '
                        'tous les champs obligatoires.'
                    ),
                }
            )

        subject = get_object_or_404(
            Subject,
            id=subject_id,
            teachers=teacher
        )

        try:
            session = int(session)
        except (ValueError, TypeError):
            session = 1

        evaluation.subject = subject
        evaluation.type_evaluation = type_evaluation
        evaluation.session = session
        evaluation.date = date_evaluation

        evaluation.save()

        return redirect(
            'professeur_evaluation_detail',
            evaluation.pk
        )

    return render(
        request,
        'professeur/evaluations/modifier.html',
        {
            'evaluation': evaluation,
            'subjects': subjects,
        }
    )


# ==================================================
# SUPPRESSION ÉVALUATION PROFESSEUR
# ==================================================

@professeur_required
def professeur_evaluation_supprimer(request, pk):

    teacher = get_current_teacher(request)

    if not teacher:
        return redirect(
            'professeur_evaluations'
        )

    evaluation = get_object_or_404(
        Evaluation,
        pk=pk,
        subject__teachers=teacher,
    )

    if request.method != 'POST':
        return redirect(
            'professeur_evaluation_detail',
            pk=evaluation.pk,
        )

    evaluation.delete()

    return redirect(
        'professeur_evaluations'
    )



# ==================================================
# NOTES PROFESSEUR
# ==================================================

@professeur_required
def professeur_grades(request):
    teacher = get_current_teacher(request)

    if not teacher:
        return redirect('professeur_evaluations')

    grades = (
        Grade.objects
        .filter(
            evaluation__subject__teachers=teacher
        )
        .select_related(
            'student',
            'evaluation',
            'evaluation__subject'
        )
        .order_by(
            'student__nom',
            'student__prenom'
        )
    )

    return render(
        request,
        'professeur/grades/liste.html',
        {
            'grades': grades,
        }
    )

from decimal import Decimal, InvalidOperation


# ============================================================
# PROFESSEUR — SAISIE DES NOTES
# ============================================================

@professeur_required
def professeur_grade_add(request):

    teacher = get_current_teacher(request)

    if not teacher:
        return redirect('professeur_grades')

    # ------------------------------------------------------------
    # ÉVALUATIONS DU PROFESSEUR
    # ------------------------------------------------------------

    evaluations = (
        Evaluation.objects
        .filter(
            subject__teachers=teacher
        )
        .select_related(
            'subject',
            'subject__semestre',
            'subject__semestre__niveau',
            'annee_universitaire',
        )
        .distinct()
        .order_by(
            '-date',
            '-id'
        )
    )

    selected_evaluation = None
    students = Student.objects.none()
    error = None

    # ------------------------------------------------------------
    # ÉVALUATION SÉLECTIONNÉE
    # ------------------------------------------------------------

    evaluation_id = (
        request.POST.get('evaluation')
        or request.GET.get('evaluation')
    )

    if evaluation_id:

        selected_evaluation = get_object_or_404(
            Evaluation.objects.select_related(
                'subject',
                'subject__semestre',
                'subject__semestre__niveau',
                'annee_universitaire',
            ),
            pk=evaluation_id,
            subject__teachers=teacher,
        )

        # --------------------------------------------------------
        # RÉCUPÉRER LE NIVEAU DE LA MATIÈRE
        # --------------------------------------------------------

        niveau_id = None

        if selected_evaluation.subject.semestre:
            niveau_id = (
                selected_evaluation
                .subject
                .semestre
                .niveau_id
            )

        # --------------------------------------------------------
        # RÉCUPÉRER TOUS LES ÉTUDIANTS DU NIVEAU
        # --------------------------------------------------------

        if niveau_id:

            students = (
                Student.objects
                .filter(
                    niveau_id=niveau_id
                )
                .order_by(
                    'nom',
                    'prenom'
                )
            )

        # --------------------------------------------------------
        # CHARGER LES NOTES EXISTANTES
        # --------------------------------------------------------

        existing_grades = {
            grade.student_id: grade
            for grade in Grade.objects.filter(
                evaluation=selected_evaluation
            )
        }

        # Ajouter la note existante à chaque étudiant
        for student in students:

            grade = existing_grades.get(student.id)

            student.existing_note = (
                grade.note
                if grade
                else None
            )

    # ============================================================
    # ENREGISTREMENT
    # ============================================================

    if request.method == 'POST':

        if not selected_evaluation:

            error = (
                "Veuillez sélectionner une évaluation."
            )

        elif not students.exists():

            error = (
                "Aucun étudiant n'est associé au niveau "
                "de cette évaluation."
            )

        else:

            errors = []

            # ----------------------------------------------------
            # VÉRIFIER TOUTES LES NOTES AVANT D'ENREGISTRER
            # ----------------------------------------------------

            notes_a_enregistrer = []

            for student in students:

                note_value = request.POST.get(
                    f'note_{student.id}',
                    ''
                ).strip()

                # ------------------------------------------------
                # NOTE OBLIGATOIRE
                # ------------------------------------------------

                if note_value == '':

                    errors.append(
                        f"La note de "
                        f"{student.nom} {student.prenom} "
                        f"est obligatoire."
                    )

                    continue

                # ------------------------------------------------
                # CONVERSION
                # ------------------------------------------------

                try:

                    note = Decimal(note_value)

                except (
                    InvalidOperation,
                    ValueError,
                    TypeError
                ):

                    errors.append(
                        f"La note de "
                        f"{student.nom} {student.prenom} "
                        f"doit être un nombre valide."
                    )

                    continue

                # ------------------------------------------------
                # VALIDATION 0 → 20
                # ------------------------------------------------

                if (
                    note < Decimal('0')
                    or note > Decimal('20')
                ):

                    errors.append(
                        f"La note de "
                        f"{student.nom} {student.prenom} "
                        f"doit être comprise entre 0 et 20."
                    )

                    continue

                notes_a_enregistrer.append(
                    (
                        student,
                        note
                    )
                )

            # ----------------------------------------------------
            # S'IL Y A UNE ERREUR
            # AUCUNE NOTE N'EST ENREGISTRÉE
            # ----------------------------------------------------

            if errors:

                error = " ".join(errors)

            else:

                # ------------------------------------------------
                # CRÉER / MODIFIER LES NOTES
                # ------------------------------------------------

                for student, note in notes_a_enregistrer:

                    Grade.objects.update_or_create(
                        student=student,
                        evaluation=selected_evaluation,
                        defaults={
                            'note': note,
                        }
                    )

                # ------------------------------------------------
                # SUCCÈS
                # ------------------------------------------------

                return redirect(
                    'professeur_grades'
                )

    # ============================================================
    # AFFICHAGE
    # ============================================================

    return render(
        request,
        'professeur/grades/saisir.html',
        {
            'evaluations': evaluations,
            'students': students,
            'selected_evaluation': selected_evaluation,
            'error': error,
        }
    )

    
# ==================================================
# HISTORIQUE DES NOTES PROFESSEUR
# ==================================================

@professeur_required
def professeur_grade_history(request):
    """
    Affiche l'historique des notes saisies par le professeur.

    Logique :
        Professeur
            ↓
        Notes
            ↓
        Évaluation
            ↓
        Matière du professeur
    """

    teacher = get_current_teacher(request)

    if not teacher:
        return redirect('professeur_grades')

    grades = (
        Grade.objects
        .filter(
            evaluation__subject__teachers=teacher
        )
        .select_related(
            'student',
            'evaluation',
            'evaluation__subject',
        )
        .order_by(
            '-evaluation__date',
            '-evaluation__id',
            'student__nom',
            'student__prenom',
        )
    )

    return render(
        request,
        'professeur/grades/historique.html',
        {
            'grades': grades,
        }
    )

# ==================================================
# ABSENCES PROFESSEUR
# ==================================================

@professeur_required
def professeur_absences(request):
    """
    Liste uniquement les absences enregistrées
    dans les matières enseignées par le professeur connecté.

    Logique :

        Professeur
            ↓
        Ses matières
            ↓
        Absences de ces matières
            ↓
        Affichage

    Cette logique est totalement indépendante
    des évaluations et des notes.
    """

    teacher = get_current_teacher(request)

    if not teacher:
        return redirect('professeur_absences')

    absences = (
        Absence.objects
        .filter(
            subject__teachers=teacher
        )
        .select_related(
            'student',
            'subject'
        )
        .distinct()
        .order_by(
            '-date_absence',
            '-id'
        )
    )

    return render(
        request,
        'professeur/absences/liste.html',
        {
            'absences': absences,
        }
    )


@professeur_required
def professeur_absence_add(request):
    """
    Permet au professeur d'enregistrer une absence.

    Logique :

        Professeur
            ↓
        Ses matières
            ↓
        Niveau de la matière
            ↓
        Étudiants du niveau
            ↓
        Absence

    Les évaluations et les notes ne sont jamais utilisées.
    """

    teacher = get_current_teacher(request)

    if not teacher:
        return redirect('professeur_absences')

    # ==================================================
    # MATIÈRES DU PROFESSEUR
    # ==================================================

    subjects = (
        Subject.objects
        .filter(
            teachers=teacher
        )
        .select_related(
            'semestre',
            'semestre__niveau'
        )
        .distinct()
        .order_by(
            'nom'
        )
    )

    # ==================================================
    # VALEURS DU FORMULAIRE
    # ==================================================

    selected_subject = None
    students = Student.objects.none()
    selected_student_id = ''
    date_absence = ''
    error = None

    subject_id = (
        request.POST.get('subject')
        or request.GET.get('subject')
    )

    selected_student_id = (
        request.POST.get('student')
        or request.GET.get('student')
        or ''
    )

    date_absence = (
        request.POST.get('date_absence')
        or request.GET.get('date_absence')
        or ''
    )

    # ==================================================
    # SÉLECTION DE LA MATIÈRE
    # ==================================================

    if subject_id:

        selected_subject = get_object_or_404(
            Subject.objects.select_related(
                'semestre',
                'semestre__niveau'
            ),
            id=subject_id,
            teachers=teacher
        )

        # ==================================================
        # RÉCUPÉRATION DU NIVEAU
        # ==================================================

        niveau_id = None

        if selected_subject.semestre:
            niveau_id = selected_subject.semestre.niveau_id

        # ==================================================
        # ÉTUDIANTS DU NIVEAU
        # ==================================================

        if niveau_id:

            students = (
                Student.objects
                .filter(
                    niveau_id=niveau_id
                )
                .order_by(
                    'nom',
                    'prenom'
                )
            )

    # ==================================================
    # ENREGISTREMENT
    # ==================================================

    if request.method == 'POST':

        # --------------------------------------------------
        # MATIÈRE
        # --------------------------------------------------

        if not subject_id:

            error = (
                'Veuillez sélectionner une matière.'
            )

        # --------------------------------------------------
        # ÉTUDIANT
        # --------------------------------------------------

        elif not selected_student_id:

            error = (
                'Veuillez sélectionner un étudiant.'
            )

        # --------------------------------------------------
        # DATE
        # --------------------------------------------------

        elif not date_absence:

            error = (
                'Veuillez renseigner la date de l’absence.'
            )

        else:

            # --------------------------------------------------
            # VÉRIFICATION DE LA MATIÈRE
            # --------------------------------------------------

            selected_subject = get_object_or_404(
                Subject.objects.select_related(
                    'semestre',
                    'semestre__niveau'
                ),
                id=subject_id,
                teachers=teacher
            )

            # --------------------------------------------------
            # NIVEAU DE LA MATIÈRE
            # --------------------------------------------------

            niveau_id = None

            if selected_subject.semestre:
                niveau_id = selected_subject.semestre.niveau_id

            if not niveau_id:

                error = (
                    'Cette matière n’est associée à aucun niveau.'
                )

            else:

                # --------------------------------------------------
                # VÉRIFICATION DE L'ÉTUDIANT
                # --------------------------------------------------

                student = get_object_or_404(
                    Student,
                    id=selected_student_id,
                    niveau_id=niveau_id
                )

                # --------------------------------------------------
                # VÉRIFICATION DU DOUBLON
                # --------------------------------------------------

                absence_exists = Absence.objects.filter(
                    student=student,
                    subject=selected_subject,
                    date_absence=date_absence
                ).exists()

                if absence_exists:

                    error = (
                        'Cette absence est déjà enregistrée '
                        'pour cet étudiant, cette matière et cette date.'
                    )

                else:

                    # --------------------------------------------------
                    # CRÉATION
                    # --------------------------------------------------

                    Absence.objects.create(
                        student=student,
                        subject=selected_subject,
                        date_absence=date_absence
                    )

                    return redirect(
                        'professeur_absences'
                    )

    # ==================================================
    # AFFICHAGE
    # ==================================================

    return render(
        request,
        'professeur/absences/enregistrer.html',
        {
            'subjects': subjects,
            'students': students,
            'selected_subject': selected_subject,
            'selected_student_id': selected_student_id,
            'date_absence': date_absence,
            'error': error,
        }
    )


# ==================================================
# ÉTUDIANTS DU PROFESSEUR
# ==================================================
@professeur_required
def professeur_students(request):
    teacher = get_current_teacher(request)

    if teacher is None:
        messages.error(
            request,
            "Aucun profil professeur associé à ce compte."
        )
        return redirect('professeur_dashboard')

    # Matières enseignées par le professeur
    subjects = (
        Subject.objects
        .filter(
            teachers=teacher
        )
        .select_related(
            'semestre',
            'semestre__niveau'
        )
        .distinct()
    )

    # Récupération des niveaux des matières enseignées
    niveau_ids = (
        subjects
        .exclude(semestre__niveau_id=None)
        .values_list(
            'semestre__niveau_id',
            flat=True
        )
        .distinct()
    )

    # Étudiants appartenant aux niveaux concernés
    students = (
        Student.objects
        .filter(
            niveau_id__in=niveau_ids
        )
        .select_related(
            'user',
            'niveau',
            'filiere'
        )
        .order_by(
            'nom',
            'prenom'
        )
    )

    return render(
        request,
        'professeur/students/liste.html',
        {
            'students': students,
            'teacher': teacher,
        }
    )

# ==================================================
# DÉTAIL D'UN ÉTUDIANT DU PROFESSEUR
# ==================================================
@professeur_required
def professeur_student_detail(request, pk):

    teacher = get_current_teacher(request)

    if teacher is None:
        messages.error(
            request,
            "Aucun profil professeur associé à ce compte."
        )
        return redirect('professeur_dashboard')


    # --------------------------------------------------
    # Matières enseignées par le professeur
    # --------------------------------------------------

    subjects = (
        Subject.objects
        .filter(
            teachers=teacher
        )
        .select_related(
            'semestre',
            'semestre__niveau'
        )
        .distinct()
    )


    # --------------------------------------------------
    # Niveaux associés à ces matières
    # --------------------------------------------------

    niveau_ids = (
        subjects
        .exclude(
            semestre__niveau_id=None
        )
        .values_list(
            'semestre__niveau_id',
            flat=True
        )
        .distinct()
    )


    # --------------------------------------------------
    # Étudiant autorisé
    #
    # Le professeur ne peut consulter que les étudiants
    # appartenant aux niveaux de ses matières.
    # --------------------------------------------------

    student = get_object_or_404(
        Student.objects.select_related(
            'user',
            'niveau',
            'filiere'
        ),
        pk=pk,
        niveau_id__in=niveau_ids
    )


    return render(
        request,
        'professeur/students/detail.html',
        {
            'student': student,
            'teacher': teacher,
        }
    )


# ==================================================
# MATIÈRES DU PROFESSEUR
# ==================================================
@professeur_required
def professeur_subjects(request):
    """
    Affiche uniquement les matières affectées
    au professeur connecté.

    Les affectations sont récupérées depuis
    le modèle Enseignement.

    Une ligne correspond à :
        Matière + Niveau + Filière + Crédits
    """

    teacher = get_current_teacher(request)

    if teacher is None:
        messages.error(
            request,
            "Aucun profil professeur associé à ce compte."
        )

        return redirect(
            'professeur_dashboard'
        )

    enseignements = (
        Enseignement.objects
        .filter(
            teacher_id=teacher.id
        )
        .select_related(
            'subject',
            'semestre',
            'semestre__niveau',
            'filiere'
        )
        .order_by(
            'subject__nom',
            'semestre__niveau__code',
            'filiere__code'
        )
    )

    return render(
        request,
        'professeur/subjects/liste.html',
        {
            'enseignements': enseignements,
            'teacher': teacher,
        }
    )



# ==================================================
# PROTECTION ÉTUDIANT
# ==================================================

def etudiant_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):

        profile = (
            UserProfile.objects
            .filter(user=request.user)
            .first()
        )

        if profile is None or profile.role != 'etudiant':
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper


# ==================================================
# DASHBOARD ÉTUDIANT
# ==================================================
# ==================================================
# DASHBOARD ÉTUDIANT
# ==================================================

@etudiant_required
def etudiant_dashboard(request):
    """
    Tableau de bord personnel de l'étudiant connecté.

    Les données sont toujours récupérées à partir
    de request.user afin qu'un étudiant ne puisse
    jamais consulter les données d'un autre étudiant.
    """

    student = (
        Student.objects
        .select_related(
            'user',
            'filiere',
            'niveau',
        )
        .filter(
            user=request.user,
        )
        .first()
    )

    if not student:
        return redirect('dashboard')

    # --------------------------------------------------
    # NOTES DE L'ÉTUDIANT
    # --------------------------------------------------

    grades = (
        Grade.objects
        .filter(
            student=student,
        )
        .select_related(
            'evaluation',
            'evaluation__matiere',
        )
        .order_by(
            '-evaluation__date',
            '-id',
        )
    )

    # --------------------------------------------------
    # STATISTIQUES
    # --------------------------------------------------

    total_grades = grades.count()

    total_absences = (
        Absence.objects
        .filter(
            student=student,
        )
        .count()
    )

    total_subjects = 0

    if student.niveau:
        total_subjects = (
            Subject.objects
            .filter(
                semestre__niveau=student.niveau,
            )
            .distinct()
            .count()
        )

    # --------------------------------------------------
    # NOTES RÉCENTES
    # --------------------------------------------------

    recent_grades = grades[:5]

    # --------------------------------------------------
    # CONTEXTE
    # --------------------------------------------------

    context = {
        'student': student,
        'grades': grades,
        'recent_grades': recent_grades,

        'total_grades': total_grades,
        'total_absences': total_absences,
        'total_subjects': total_subjects,
    }

    return render(
        request,
        'etudiant/dashboard/dashboard.html',
        context,
    )

# ==================================================
# PROFIL ÉTUDIANT
# ==================================================
@etudiant_required
def etudiant_profile(request):
    student = (
        Student.objects
        .select_related(
            'user',
            'filiere',
            'niveau',
        )
        .filter(
            user=request.user
        )
        .first()
    )

    if student is None:
        messages.error(
            request,
            "Aucun profil étudiant n'est associé à votre compte."
        )
        return redirect('etudiant_dashboard')

    return render(
        request,
        'etudiant/profile/detail.html',
        {
            'student': student,
        }
    )

# ==================================================
# NOTES ÉTUDIANT
# ==================================================

@etudiant_required
def etudiant_grades(request):

    student = (
        Student.objects
        .select_related('user')
        .filter(user=request.user)
        .first()
    )

    if not student:
        return redirect('etudiant_dashboard')

    grades = (
        Grade.objects
        .filter(student=student)
        .select_related(
            'student',
            'evaluation',
            'evaluation__matiere',
            'evaluation__annee_universitaire',
        )
        .order_by(
            '-evaluation__date',
            '-id',
        )
    )

    return render(
        request,
        'etudiant/grades/liste.html',
        {
            'student': student,
            'grades': grades,
        }
    )


# ==================================================
# RÉSULTATS ÉTUDIANT
# ==================================================

@etudiant_required
def etudiant_results(request):

    student = (
        Student.objects
        .select_related('user')
        .filter(user=request.user)
        .first()
    )

    if not student:
        return redirect('etudiant_dashboard')

    grades = (
        Grade.objects
        .filter(student=student)
        .select_related(
            'student',
            'evaluation',
            'evaluation__matiere',
            'evaluation__annee_universitaire',
        )
        .order_by(
            'evaluation__matiere__nom',
            '-evaluation__date',
            '-id',
        )
    )

    moyennes = (
        Grade.objects
        .filter(
            student=student,
            valeur__isnull=False,
        )
        .values(
            'evaluation__matiere__id',
            'evaluation__matiere__nom',
        )
        .annotate(
            moyenne=Avg('valeur')
        )
        .order_by(
            'evaluation__matiere__nom'
        )
    )

    return render(
        request,
        'etudiant/results/detail.html',
        {
            'student': student,
            'grades': grades,
            'moyennes': moyennes,
        }
    )


# ==================================================
# ABSENCES ÉTUDIANT
# ==================================================

@etudiant_required
def etudiant_absences(request):

    student = (
        Student.objects
        .filter(
            user=request.user
        )
        .first()
    )

    if student is None:
        absences = Absence.objects.none()
    else:
        absences = (
            Absence.objects
            .filter(
                student=student
            )
            .select_related(
                'class_subject',
                'class_subject__subject',
                'semester',
            )
            .order_by(
                '-date'
            )
        )

    return render(
        request,
        'etudiant/absences/liste.html',
        {
            'absences': absences,
        }
    )


# ==================================================
# MATIÈRES ÉTUDIANT
# ==================================================

@etudiant_required
def etudiant_subjects(request):

    student = (
        Student.objects
        .select_related(
            'classe'
        )
        .filter(
            user=request.user
        )
        .first()
    )

    if student is None:
        subjects = Subject.objects.none()
    else:
        subjects = (
            Subject.objects
            .filter(
                classsubject__classe=student.classe
            )
            .distinct()
            .order_by(
                'nom'
            )
        )

    return render(
        request,
        'etudiant/subjects/liste.html',
        {
            'subjects': subjects,
        }
    )


# ==================================================
# ARRIÉRÉS ÉTUDIANT
# ==================================================

@etudiant_required
def etudiant_arrieres(request):

    student = (
        Student.objects
        .filter(
            user=request.user
        )
        .first()
    )

    if student is None:
        arrieres = Arriere.objects.none()
    else:
        arrieres = (
            Arriere.objects
            .filter(
                progression__student=student
            )
            .select_related(
                'progression',
                'progression__annee_universitaire',
                'subject',
            )
            .order_by(
                'statut',
                'subject__nom',
            )
        )

    return render(
        request,
        'etudiant/arrears/liste.html',
        {
            'arrieres': arrieres,
        }
    )


# ==================================================
# DÉCONNEXION
# ==================================================

@login_required
def dashboard_logout(request):

    logout(request)

    return redirect('connexion')