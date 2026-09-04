from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

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
from apps.academic.models import Niveau, Filiere
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from apps.academic.models import Semestre
from django.utils import timezone
from apps.academic.models import AnneeUniversitaire
from apps.grades.models import Grade  
from apps.academic.models import Arriere
from django.db.models import Avg
from apps.academic.models import Progression, Arriere


# ==================================================
# PROTECTION ADMIN
# ==================================================

def admin_required(view_func):
    """
    Autorise uniquement les utilisateurs ayant
    le rôle administrateur.
    """

    @login_required
    def wrapper(request, *args, **kwargs):

        profile = UserProfile.objects.filter(
            user=request.user
        ).first()

        if profile is None:
            return redirect('connexion')

        if profile.role != 'admin':
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)

    return wrapper


# ==================================================
# TABLEAU DE BORD PRINCIPAL
# ==================================================

@login_required
def dashboard(request):

    profile = UserProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('connexion')

    if profile.role == 'admin':
        return redirect('admin_dashboard')

    if profile.role == 'professeur':
        return redirect('professeur_dashboard')

    if profile.role == 'etudiant':
        return redirect('etudiant_dashboard')

    return redirect('connexion')


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
        .select_related('niveau')
        .order_by('nom', 'prenom')
    )

    return render(
        request,
        'admin/students/liste.html',
        {
            'students': students,
        }
    )


import datetime
import unicodedata
import re

def generate_unique_email(prenom, nom):
    """Génère un email unique basé sur le prénom et le nom."""
    def clean(text):
        nfkd = unicodedata.normalize('NFKD', text)
        ascii_text = nfkd.encode('ASCII', 'ignore').decode('utf-8')
        return re.sub(r'[^a-zA-Z0-9]', '', ascii_text).lower()

    base_email = f"{clean(prenom)}.{clean(nom)}@ecole.com"
    email = base_email
    counter = 1
    
    while User.objects.filter(email__iexact=email).exists():
        email = f"{clean(prenom)}.{clean(nom)}{counter}@ecole.com"
        counter += 1
        
    return email


def generate_matricule(niveau):
    """
    Génère un matricule unique en vérifiant sa disponibilité 
    à la fois dans les étudiants et dans les utilisateurs Django.
    """
    annee_suffixe = datetime.datetime.now().strftime('%y')
    code_niveau = ''.join([c for c in niveau.code if c.isalpha()]).upper()[:3] or 'ETU'
    prefix = f"{annee_suffixe}{code_niveau}"
    
    count = Student.objects.filter(matricule__startswith=prefix).count() + 1
    
    while True:
        sequence = str(count).zfill(3)
        matricule = f"{prefix}{sequence}"
        
        student_exists = Student.objects.filter(matricule=matricule).exists()
        user_exists = User.objects.filter(username=matricule).exists()
        
        if not student_exists and not user_exists:
            return matricule
        
        count += 1

@admin_required
def admin_student_add(request):

    niveaux = Niveau.objects.order_by('code')
    filieres = Filiere.objects.order_by('nom')  # <-- Indispensable pour alimenter le select

    if request.method == 'POST':

        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
        age = request.POST.get('age', '').strip()
        niveau_id = request.POST.get('niveau')
        filiere_id = request.POST.get('filiere')  # <-- Récupération de la filière

        if not nom or not prenom or not age or not niveau_id or not filiere_id:
            return render(
                request,
                'admin/students/ajouter.html',
                {
                    'niveaux': niveaux,
                    'filieres': filieres,  # <-- Transmettre en cas d'erreur
                    'error': 'Veuillez renseigner tous les champs.',
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
                    'filieres': filieres,  # <-- Transmettre en cas d'erreur
                    'error': "L'âge doit être un nombre entier.",
                }
            )

        if age <= 0:
            return render(
                request,
                'admin/students/ajouter.html',
                {
                    'niveaux': niveaux,
                    'filieres': filieres,  # <-- Transmettre en cas d'erreur
                    'error': "L'âge doit être supérieur à 0.",
                }
            )

        niveau = get_object_or_404(Niveau, id=niveau_id)
        filiere = get_object_or_404(Filiere, id=filiere_id)  # <-- Récupération de l'objet Filiere

        # 1. GÉNÉRATION AUTOMATIQUE DU MATRICULE ET DE L'EMAIL
        matricule = generate_matricule(niveau)
        email = generate_unique_email(prenom, nom)
        default_password = "Password123!"

        # 2. CRÉATION DU COMPTE USER DJANGO
        user = User.objects.create_user(
            username=matricule,
            email=email,
            password=default_password,
            first_name=prenom,
            last_name=nom
        )

        # 3. CRÉATION DU PROFIL UTILISATEUR
        UserProfile.objects.create(
            user=user,
            role='etudiant'
        )

        # 4. CRÉATION DE L'ÉTUDIANT AVEC LA FILIÈRE
        Student.objects.create(
            user=user,
            matricule=matricule,
            nom=nom,
            prenom=prenom,
            age=age,
            niveau=niveau,
            filiere=filiere  # <-- Ajout du champ filiere
        )

        messages.success(
            request, 
            f"Étudiant créé ! Matricule : {matricule} / Email : {email}"
        )
        return redirect('admin_students')

    return render(
        request,
        'admin/students/ajouter.html',
        {
            'niveaux': niveaux,
            'filieres': filieres,  # <-- Transmettre pour l'affichage initial
        }
    )


@admin_required
def admin_student_detail(request, student_id):

    student = get_object_or_404(
        Student.objects.select_related('niveau', 'filiere'),  # <-- Ajoutez 'filiere' ici
        id=student_id
    )

    return render(
        request,
        'admin/students/detail.html',
        {
            'student': student,
        }
    )

@admin_required
def admin_student_edit(request, student_id):

    student = get_object_or_404(
        Student.objects.select_related('niveau'),
        id=student_id
    )

    niveaux = Niveau.objects.order_by('code')

    if request.method == 'POST':

        matricule = request.POST.get('matricule', '').strip()
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
        age = request.POST.get('age', '').strip()
        niveau_id = request.POST.get('niveau')

        if not matricule or not nom or not prenom or not age or not niveau_id:
            return render(
                request,
                'admin/students/modifier.html',
                {
                    'student': student,
                    'niveaux': niveaux,
                    'error': 'Veuillez renseigner tous les champs.',
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
                    'error': "L'âge doit être un nombre entier.",
                }
            )

        if age <= 0:
            return render(
                request,
                'admin/students/modifier.html',
                {
                    'student': student,
                    'niveaux': niveaux,
                    'error': "L'âge doit être supérieur à 0.",
                }
            )

        if Student.objects.filter(matricule=matricule).exclude(id=student.id).exists():
            return render(
                request,
                'admin/students/modifier.html',
                {
                    'student': student,
                    'niveaux': niveaux,
                    'error': 'Ce matricule est déjà utilisé.',
                }
            )

        student.matricule = matricule
        student.nom = nom
        student.prenom = prenom
        student.age = age
        student.niveau_id = niveau_id

        student.save()

        return redirect('admin_student_detail', student_id=student.id)

    return render(
        request,
        'admin/students/modifier.html',
        {
            'student': student,
            'niveaux': niveaux,
        }
    )


@admin_required
def admin_student_delete(request, student_id):

    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        student.delete()
        return redirect('admin_students')

    return redirect('admin_student_detail', student_id=student.id)






# ==================================================
# PROFESSEURS
# ==================================================

@admin_required
def admin_teachers(request):

    teachers = Teacher.objects.order_by('nom', 'prenom')

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
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')

        if not nom:
            return render(request, 'admin/teachers/ajouter.html', {  # <-- Mettez le nom exact de votre fichier ici
                'error': "Veuillez renseigner les champs obligatoires."
            })

        Teacher.objects.create(
            nom=nom,
            prenom=prenom
        )

        return redirect('admin_teachers')

    return render(request, 'admin/teachers/ajouter.html')  # <-- Ici aussi


@admin_required
def admin_teacher_detail(request, teacher_id):

    teacher = get_object_or_404(Teacher, id=teacher_id)

    return render(
        request,
        'admin/teachers/detail.html',
        {
            'teacher': teacher,
        }
    )


@admin_required
def admin_teacher_edit(request, teacher_id):

    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == 'POST':

        identifiant = request.POST.get('identifiant', '').strip()
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()

        if not identifiant or not nom:
            return render(
                request,
                'admin/teachers/modifier.html',
                {
                    'teacher': teacher,
                    'error': 'Veuillez renseigner les champs obligatoires.',
                }
            )

        if Teacher.objects.filter(identifiant=identifiant).exclude(id=teacher.id).exists():
            return render(
                request,
                'admin/teachers/modifier.html',
                {
                    'teacher': teacher,
                    'error': 'Cet identifiant est déjà utilisé.',
                }
            )

        teacher.identifiant = identifiant
        teacher.nom = nom
        teacher.prenom = prenom or None

        teacher.save()

        return redirect('admin_teacher_detail', teacher_id=teacher.id)

    return render(
        request,
        'admin/teachers/modifier.html',
        {
            'teacher': teacher,
        }
    )


@admin_required
def admin_teacher_delete(request, teacher_id):

    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == 'POST':
        teacher.delete()
        return redirect('admin_teachers')

    return redirect('admin_teacher_detail', teacher_id=teacher.id)


# ==================================================
# MATIÈRES
# ==================================================

@admin_required
def admin_subjects(request):

    subjects = (
        Subject.objects
        .select_related('semestre', 'semestre__niveau')
        .prefetch_related('teachers')
        .order_by('nom')
    )

    return render(
        request,
        'admin/subjects/liste.html',
        {
            'subjects': subjects,
        }
    )


@admin_required
def admin_subject_add(request):

    semestres = (
        Semestre.objects
        .select_related('niveau')
        .order_by('niveau__code', 'nom')
    )

    teachers = Teacher.objects.order_by('nom', 'prenom')

    if request.method == 'POST':

        nom = request.POST.get('nom', '').strip()
        credits = request.POST.get('credits', '').strip()
        semestre_id = request.POST.get('semestre')
        teacher_ids = request.POST.getlist('teachers')

        if not nom:
            return render(
                request,
                'admin/subjects/ajouter.html',
                {
                    'semestres': semestres,
                    'teachers': teachers,
                    'error': 'Le nom de la matière est obligatoire.',
                }
            )

        if Subject.objects.filter(nom=nom).exists():
            return render(
                request,
                'admin/subjects/ajouter.html',
                {
                    'semestres': semestres,
                    'teachers': teachers,
                    'error': 'Cette matière existe déjà.',
                }
            )

        subject = Subject.objects.create(
            nom=nom,
            credits=credits or None,
            semestre_id=semestre_id or None
        )

        subject.teachers.set(teacher_ids)

        return redirect('admin_subjects')

    return render(
        request,
        'admin/subjects/ajouter.html',
        {
            'semestres': semestres,
            'teachers': teachers,
        }
    )


@admin_required
def admin_subject_detail(request, subject_id):

    subject = get_object_or_404(
        Subject.objects
        .select_related('semestre', 'semestre__niveau')
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

    subject = get_object_or_404(Subject, id=subject_id)

    semestres = (
        Semestre.objects
        .select_related('niveau')
        .order_by('niveau__code', 'nom')
    )

    teachers = Teacher.objects.order_by('nom', 'prenom')

    if request.method == 'POST':

        nom = request.POST.get('nom', '').strip()
        credits = request.POST.get('credits', '').strip()
        semestre_id = request.POST.get('semestre')
        teacher_ids = request.POST.getlist('teachers')

        if not nom:
            return render(
                request,
                'admin/subjects/modifier.html',
                {
                    'subject': subject,
                    'semestres': semestres,
                    'teachers': teachers,
                    'error': 'Le nom de la matière est obligatoire.',
                }
            )

        if Subject.objects.filter(nom=nom).exclude(id=subject.id).exists():
            return render(
                request,
                'admin/subjects/modifier.html',
                {
                    'subject': subject,
                    'semestres': semestres,
                    'teachers': teachers,
                    'error': 'Cette matière existe déjà.',
                }
            )

        subject.nom = nom
        subject.credits = credits or None
        subject.semestre_id = semestre_id or None

        subject.save()
        subject.teachers.set(teacher_ids)

        return redirect('admin_subject_detail', subject_id=subject.id)

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

    subject = get_object_or_404(Subject, id=subject_id)

    if request.method == 'POST':
        subject.delete()
        return redirect('admin_subjects')

    return redirect('admin_subject_detail', subject_id=subject.id)


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
            'evaluation__annee_universitaire',
        )
        .order_by('-evaluation__date', 'student__nom')
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

    students = Student.objects.order_by('nom', 'prenom')
    subjects = Subject.objects.select_related('semestre', 'semestre__niveau').order_by('nom')

    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        type_evaluation = request.POST.get('type_evaluation')
        session = request.POST.get('session', 1)
        note = request.POST.get('note', '').strip()

        # Vérification que tous les champs sont remplis
        if not student_id or not subject_id or not type_evaluation or not note:
            return render(request, 'admin/grades/saisir.html', {
                'students': students,
                'subjects': subjects,
                'error': 'Veuillez renseigner tous les champs.',
            })

        try:
            note = float(note)
        except ValueError:
            return render(request, 'admin/grades/saisir.html', {
                'students': students,
                'subjects': subjects,
                'error': 'La note doit être numérique.',
            })

        if note < 0 or note > 20:
            return render(request, 'admin/grades/saisir.html', {
                'students': students,
                'subjects': subjects,
                'error': 'La note doit être comprise entre 0 et 20.',
            })

        # Récupérer l'année universitaire active (la plus récente par défaut)
        annee_univ = AnneeUniversitaire.objects.order_by('-id').first()
        if not annee_univ:
            return render(request, 'admin/grades/saisir.html', {
                'students': students,
                'subjects': subjects,
                'error': 'Aucune année universitaire configurée dans le système.',
            })

        # 1. CRÉATION OU RÉCUPÉRATION AUTOMATIQUE DE L'ÉVALUATION EN DB
        evaluation, created = Evaluation.objects.get_or_create(
            subject_id=subject_id,
            type_evaluation=type_evaluation,
            session=int(session),
            defaults={
                'annee_universitaire': annee_univ,
                'date': timezone.now().date(),
            }
        )

        # 2. ENREGISTREMENT DE LA NOTE LIÉE À CETTE ÉVALUATION EN DB
        Grade.objects.update_or_create(
            student_id=student_id,
            evaluation=evaluation,
            defaults={'note': note}
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
        .order_by('student__nom', '-evaluation__date')
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
        .select_related('student', 'subject')
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
    students = Student.objects.order_by('nom', 'prenom')
    subjects = Subject.objects.order_by('nom')

    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        type_evaluation = request.POST.get('type_evaluation')
        date_absence = request.POST.get('date_absence')

        if not student_id or not subject_id or not type_evaluation or not date_absence:
            return render(
                request,
                'admin/absences/enregistrer.html',
                {
                    'students': students,
                    'subjects': subjects,
                    'error': 'Veuillez renseigner tous les champs.',
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
        Absence.objects.select_related('student', 'subject'),
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
    absence = get_object_or_404(Absence, id=absence_id)
    students = Student.objects.order_by('nom', 'prenom')
    subjects = Subject.objects.order_by('nom')

    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        type_evaluation = request.POST.get('type_evaluation')
        date_absence = request.POST.get('date_absence')

        if not student_id or not subject_id or not type_evaluation or not date_absence:
            return render(
                request,
                'admin/absences/modifier.html',
                {
                    'absence': absence,
                    'students': students,
                    'subjects': subjects,
                    'error': 'Veuillez renseigner tous les champs.',
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
    absence = get_object_or_404(Absence, id=absence_id)
    if request.method == 'POST':
        absence.delete()
    return redirect('admin_absences')


@admin_required
def admin_absence_justify(request, absence_id):
    absence = get_object_or_404(Absence, id=absence_id)
    if request.method == 'POST':
        absence.justifiee = True
        absence.justification = request.POST.get('justification', '').strip()
        absence.date_justification = request.POST.get('date_justification') or None
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
    absence = get_object_or_404(Absence, id=absence_id)
    if request.method == 'POST':
        note_rattrapage_str = request.POST.get('note_rattrapage', '').strip()
        note_rattrapage = None

        if note_rattrapage_str:
            try:
                note_rattrapage = float(note_rattrapage_str)
                if note_rattrapage < 0 or note_rattrapage > 20:
                    return render(
                        request,
                        'admin/absences/rattrapage.html',
                        {
                            'absence': absence,
                            'error': 'La note doit être comprise entre 0 et 20.',
                        }
                    )
            except ValueError:
                return render(
                    request,
                    'admin/absences/rattrapage.html',
                    {
                        'absence': absence,
                        'error': 'La note doit être un nombre valide.',
                    }
                )

        absence.rattrapage_effectue = True
        absence.note_rattrapage = note_rattrapage
        absence.date_rattrapage = request.POST.get('date_rattrapage') or None
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
        code = request.POST.get('code', '').strip()
        nom = request.POST.get('nom', '').strip()
        niveaux_ids = request.POST.getlist('niveaux')

        if not code or not nom:
            return render(
                request,
                'admin/academic/filiere_ajouter.html',
                {
                    'niveaux': niveaux,
                    'error': 'Le code et le nom de la filière sont obligatoires.',
                }
            )

        if Filiere.objects.filter(code__iexact=code).exists():
            return render(
                request,
                'admin/academic/filiere_ajouter.html',
                {
                    'niveaux': niveaux,
                    'error': 'Une filière avec ce code existe déjà.',
                }
            )

        filiere = Filiere.objects.create(code=code, nom=nom)
        if niveaux_ids:
            filiere.niveaux.set(niveaux_ids)

        messages.success(request, "Filière ajoutée avec succès !")
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
    filiere = get_object_or_404(Filiere, pk=pk)
    niveaux = Niveau.objects.order_by('code')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        nom = request.POST.get('nom', '').strip()
        niveaux_ids = request.POST.getlist('niveaux')

        if not code or not nom:
            return render(
                request,
                'admin/academic/filiere_modifier.html',
                {
                    'error': 'Veuillez renseigner tous les champs obligatoires.',
                    'filiere': filiere,
                    'niveaux': niveaux
                }
            )

        if Filiere.objects.filter(code__iexact=code).exclude(pk=pk).exists():
            return render(
                request,
                'admin/academic/filiere_modifier.html',
                {
                    'error': 'Ce code de filière existe déjà.',
                    'filiere': filiere,
                    'niveaux': niveaux
                }
            )

        filiere.code = code
        filiere.nom = nom
        filiere.save()
        filiere.niveaux.set(niveaux_ids)

        messages.success(request, "Filière modifiée avec succès !")
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
        filiere = get_object_or_404(Filiere, pk=pk)
        filiere.delete()
        messages.success(request, "Filière supprimée avec succès !")
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
        code = request.POST.get('code', '').strip()
        nom = request.POST.get('nom', '').strip()

        if not code or not nom:
            return render(
                request,
                'admin/academic/niveau_ajouter.html',  # <-- CORRIGÉ ICI
                {
                    'error': 'Veuillez renseigner tous les champs.',
                }
            )

        if Niveau.objects.filter(code__iexact=code).exists():
            return render(
                request,
                'admin/academic/niveau_ajouter.html',  # <-- CORRIGÉ ICI
                {
                    'error': 'Ce code de niveau existe déjà.',
                }
            )

        Niveau.objects.create(
            code=code,
            nom=nom
        )

        messages.success(request, "Niveau créé avec succès !")
        return redirect('admin_niveaux')

    return render(
        request,
        'admin/academic/niveau_ajouter.html'  # <-- CORRIGÉ ICI
    )


@admin_required
def admin_niveau_edit(request, pk):
    niveau = get_object_or_404(Niveau, pk=pk)

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        nom = request.POST.get('nom', '').strip()

        if not code or not nom:
            return render(
                request,
                'admin/academic/niveau_modifier.html',
                {
                    'error': 'Veuillez renseigner tous les champs.',
                    'niveau': niveau
                }
            )

        if Niveau.objects.filter(code__iexact=code).exclude(pk=pk).exists():
            return render(
                request,
                'admin/academic/niveau_modifier.html',
                {
                    'error': 'Ce code de niveau existe déjà.',
                    'niveau': niveau
                }
            )

        niveau.code = code
        niveau.nom = nom
        niveau.save()

        messages.success(request, "Niveau modifié avec succès !")
        return redirect('admin_niveaux')

    return render(
        request,
        'admin/academic/niveau_modifier.html',
        {'niveau': niveau}
    )


@admin_required
def admin_niveau_delete(request, pk):
    if request.method == 'POST':
        niveau = get_object_or_404(Niveau, pk=pk)
        niveau.delete()
        messages.success(request, "Niveau supprimé avec succès !")
    return redirect('admin_niveaux')




@admin_required
def admin_semestre_edit(request, semestre_id):
    # On récupère le semestre concerné par l'ID dans l'URL
    semestre = get_object_or_404(Semestre, id=semestre_id)

    if request.method == 'POST':
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        
        if date_debut and date_fin:
            semestre.date_debut = date_debut
            semestre.date_fin = date_fin
            semestre.save()
            return redirect('admin_semestres') # Redirige vers la liste

    context = {
        'semestre': semestre, # Transmet l'objet au template pour afficher le nom, le niveau et l'année
    }
    return render(request, 'admin/academic/semestre_modifier.html', context)



# ==================================================
# SEMESTRES
# ==================================================

@admin_required
def admin_semestres(request):

    semestres = (
        Semestre.objects
        .select_related('niveau')
        .order_by('niveau__code', 'nom')
    )

    return render(
        request,
        'admin/academic/semestres.html',
        {
            'semestres': semestres,
        }
    )

@admin_required
def admin_semestre_add(request):
    niveaux = Niveau.objects.order_by('code')
    semestre_choices = Semestre.SEMESTRE_CHOICES

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        niveau_id = request.POST.get('niveau')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')

        if not nom or not niveau_id:
            return render(
                request,
                'admin/academic/semestres_ajouter.html',  # <-- Corrigé ici
                {
                    'niveaux': niveaux,
                    'semestre_choices': semestre_choices,
                    'error': 'Le semestre et le niveau sont obligatoires.',
                }
            )

        niveau = get_object_or_404(Niveau, id=niveau_id)

        # Création ou récupération du semestre avec ses dates
        semestre, created = Semestre.objects.get_or_create(
            nom=nom,
            niveau=niveau,
            defaults={
                'date_debut': date_debut if date_debut else None,
                'date_fin': date_fin if date_fin else None,
            }
        )
        
        # Si le semestre existait déjà, on met à jour ses dates
        if not created and date_debut and date_fin:
            semestre.date_debut = date_debut
            semestre.date_fin = date_fin
            semestre.save()

        return redirect('admin_semestres')

    return render(
        request,
        'admin/academic/semestres_ajouter.html',  # <-- Corrigé ici aussi
        {
            'niveaux': niveaux,
            'semestre_choices': semestre_choices,
        }
    )


@admin_required
def admin_semestre_delete(request, semestre_id):  # <-- Utilisez bien "semestre_id" ici
    semestre = get_object_or_404(Semestre, id=semestre_id)
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
        libelle = request.POST.get('libelle', '').strip()
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        active = request.POST.get('est_active') == 'on'

        if not libelle or not date_debut or not date_fin:
            return render(
                request,
                'admin/academic/annee_ajouter.html',
                {
                    'error': "Tous les champs obligatoires (libellé et dates) doivent être remplis.",
                }
            )

        if AnneeUniversitaire.objects.filter(libelle=libelle).exists():
            return render(
                request,
                'admin/academic/annee_ajouter.html',
                {
                    'error': 'Cette année universitaire existe déjà.',
                }
            )

        if active:
            AnneeUniversitaire.objects.filter(active=True).update(active=False)

        AnneeUniversitaire.objects.create(
            libelle=libelle,
            date_debut=date_debut,
            date_fin=date_fin,
            active=active
        )

        return redirect('admin_annees')

    return render(request, 'admin/academic/annee_ajouter.html')


@admin_required
def admin_annee_edit(request, pk):
    annee = get_object_or_404(AnneeUniversitaire, pk=pk)

    if request.method == 'POST':
        libelle = request.POST.get('libelle', '').strip()
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        active = request.POST.get('est_active') == 'on'

        if not libelle or not date_debut or not date_fin:
            return render(
                request,
                'admin/academic/annee_modifier.html',
                {
                    'annee': annee,
                    'error': "Tous les champs obligatoires (libellé et dates) doivent être remplis.",
                }
            )

        if AnneeUniversitaire.objects.filter(libelle=libelle).exclude(pk=pk).exists():
            return render(
                request,
                'admin/academic/annee_modifier.html',
                {
                    'annee': annee,
                    'error': 'Cette année universitaire existe déjà.',
                }
            )

        if active:
            AnneeUniversitaire.objects.filter(active=True).exclude(pk=pk).update(active=False)

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
        annee = get_object_or_404(AnneeUniversitaire, pk=pk)
        annee.delete()
    return redirect('admin_annees')

# ==================================================
# ARRIÉRÉS
# ==================================================

@admin_required
def admin_arrieres(request):

    arrieres = (
        Arriere.objects
        .select_related('progression', 'progression__student', 'subject')
        .order_by('statut', 'progression__student__nom')
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
        .select_related('student', 'annee_universitaire', 'niveau')
        .order_by('student__nom', 'student__prenom')
    )
    subjects = Subject.objects.order_by('nom')

    if request.method == 'POST':
        progression_id = request.POST.get('progression')
        subject_id = request.POST.get('subject')
        statut = request.POST.get('statut', 'A_RATTRAPER')

        if not progression_id or not subject_id:
            return render(
                request,
                'admin/academic/arriere_ajouter.html',
                {
                    'progressions': progressions,
                    'subjects': subjects,
                    'error': "L'étudiant/progression et la matière sont obligatoires.",
                }
            )

        progression = get_object_or_404(Progression, id=progression_id)
        subject = get_object_or_404(Subject, id=subject_id)

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
    arriere = get_object_or_404(Arriere, id=arriere_id)
    
    progressions = (
        Progression.objects
        .select_related('student', 'annee_universitaire', 'niveau')
        .order_by('student__nom', 'student__prenom')
    )
    subjects = Subject.objects.order_by('nom')

    if request.method == 'POST':
        progression_id = request.POST.get('progression')
        subject_id = request.POST.get('subject')
        statut = request.POST.get('statut', arriere.statut)

        if not progression_id or not subject_id:
            return render(
                request,
                'admin/academic/arriere_modifier.html',
                {
                    'arriere': arriere,
                    'progressions': progressions,
                    'subjects': subjects,
                    'error': "L'étudiant/progression et la matière sont obligatoires.",
                }
            )

        progression = get_object_or_404(Progression, id=progression_id)
        subject = get_object_or_404(Subject, id=subject_id)

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





def verifier_et_generer_arrieres(progression):
    """
    Vérifie les notes de la progression d'un étudiant pour son année universitaire 
    et génère automatiquement les arriérés pour les matières échouées (< 10/20).
    """
    moyennes_par_matiere = (
        Grade.objects.filter(
            student=progression.student,
            annee_universitaire=progression.annee_universitaire
        )
        .values('subject')
        .annotate(moyenne=Avg('note'))
    )

    matieres_echecs = []
    
    for item in moyennes_par_matiere:
        if item['moyenne'] is not None and item['moyenne'] < 10:
            matieres_echecs.append(item['subject'])

    for subject_id in matieres_echecs:
        Arriere.objects.get_or_create(
            progression=progression,
            subject_id=subject_id,
            defaults={'statut': 'A_RATTRAPER'}
        )


@admin_required
def admin_generer_arrieres_automatique(request):
    """
    Vue pour lancer la génération automatique des arriérés pour toutes les progressions.
    """
    progressions = Progression.objects.all()
    
    for progression in progressions:
        verifier_et_generer_arrieres(progression)
        
    return redirect('admin_arrieres')



# ==================================================
# DASHBOARDS PROFESSEUR ET ÉTUDIANT
# ==================================================

@login_required
def professeur_dashboard(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    if profile is None or profile.role != 'professeur':
        return redirect('dashboard')
    
    return render(request, 'professeur/dashboard.html')


@login_required
def etudiant_dashboard(request):
    profile = UserProfile.objects.filter(user=request.user).first()
    if profile is None or profile.role != 'etudiant':
        return redirect('dashboard')
        
    return render(request, 'etudiant/dashboard.html')



# ==================================================
# DEDICATED ROLE DECORATORS & VIEWS
# ==================================================

def professeur_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = UserProfile.objects.filter(user=request.user).first()
        if not profile or profile.role != 'professeur':
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def etudiant_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = UserProfile.objects.filter(user=request.user).first()
        if not profile or profile.role != 'etudiant':
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

# --------------------------------------------------
# DASHBOARD PROFESSEUR
# --------------------------------------------------

@professeur_required
def professeur_dashboard(request):
    teacher = Teacher.objects.filter(identifiant=request.user.email).first()
    
    total_evaluations = Evaluation.objects.filter(teacher=teacher).count() if teacher else 0
    total_absences = Absence.objects.filter(evaluation__teacher=teacher).count() if teacher else 0

    context = {
        'teacher': teacher,
        'total_evaluations': total_evaluations,
        'total_absences': total_absences,
    }
    return render(request, 'professeur/dashboard/dashboard.html', context)

@professeur_required
def professeur_evaluations(request):
    teacher = Teacher.objects.filter(identifiant=request.user.email).first()
    evaluations = Evaluation.objects.filter(teacher=teacher).select_related('subject') if teacher else []
    
    context = {
        'evaluations': evaluations,
    }
    return render(request, 'professeur/evaluations/liste.html', context)

@professeur_required
def professeur_evaluation_ajouter(request):
    teacher = Teacher.objects.filter(identifiant=request.user.email).first()
    # Si vos matières sont liées au professeur, vous pouvez filtrer ici : Subject.objects.filter(teacher=teacher)
    subjects = Subject.objects.all() 
    
    if request.method == 'POST':
        title = request.POST.get('title')
        subject_id = request.POST.get('subject')
        date_evaluation = request.POST.get('date_evaluation')
        
        if title and subject_id and teacher:
            Evaluation.objects.create(
                title=title,
                subject_id=subject_id,
                teacher=teacher,
                date=date_evaluation if date_evaluation else None
            )
            return redirect('professeur_evaluations')
            
    return render(request, 'professeur/evaluations/ajouter.html', {'subjects': subjects})

@professeur_required
def professeur_grades(request):
    teacher = Teacher.objects.filter(identifiant=request.user.email).first()
    grades = Grade.objects.filter(evaluation__teacher=teacher).select_related('student', 'evaluation__subject') if teacher else []
    return render(request, 'professeur/grades/liste.html', {'grades': grades})

@professeur_required
def professeur_grade_add(request):
    teacher = Teacher.objects.filter(identifiant=request.user.email).first()
    students = Student.objects.all()
    evaluations = Evaluation.objects.filter(teacher=teacher) if teacher else []
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        evaluation_id = request.POST.get('evaluation')
        note = request.POST.get('note')
        if student_id and evaluation_id and note:
            Grade.objects.update_or_create(
                student_id=student_id,
                evaluation_id=evaluation_id,
                defaults={'note': float(note)}
            )
            return redirect('professeur_grades')
    return render(request, 'professeur/grades/saisir.html', {'students': students, 'evaluations': evaluations})

@professeur_required
def professeur_absences(request):
    teacher = Teacher.objects.filter(identifiant=request.user.email).first()
    absences = Absence.objects.filter(evaluation__teacher=teacher).select_related('student', 'evaluation__subject') if teacher else []
    return render(request, 'professeur/absences/liste.html', {'absences': absences})

@professeur_required
def professeur_absence_add(request):
    teacher = Teacher.objects.filter(identifiant=request.user.email).first()
    students = Student.objects.all()
    evaluations = Evaluation.objects.filter(teacher=teacher) if teacher else []
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        evaluation_id = request.POST.get('evaluation')
        date_absence = request.POST.get('date_absence')
        if student_id and evaluation_id and date_absence:
            Absence.objects.create(student_id=student_id, evaluation_id=evaluation_id, date_absence=date_absence)
            return redirect('professeur_absences')
    return render(request, 'professeur/absences/enregistrer.html', {'students': students, 'evaluations': evaluations})

@professeur_required
def professeur_students(request):
    """
    Affiche uniquement les étudiants liés aux évaluations du professeur connecté.
    """
    teacher = Teacher.objects.filter(identifiant=request.user.email).first()
    if teacher:
        students = Student.objects.filter(grade__evaluation__teacher=teacher).distinct()
    else:
        students = Student.objects.none()
        
    return render(request, 'professeur/students/liste.html', {'students': students})

@professeur_required
def professeur_subjects(request):
    """
    Affiche uniquement les matières enseignées par le professeur connecté.
    """
    teacher = Teacher.objects.filter(identifiant=request.user.email).first()
    # Modifiez 'teacher=teacher' en fonction du champ réel dans votre modèle Subject (ex: professeur=teacher)
    subjects = Subject.objects.filter(teacher=teacher) if teacher else []
    
    return render(request, 'professeur/subjects/liste.html', {'subjects': subjects})



# --------------------------------------------------
# DASHBOARD ÉTUDIANT
# --------------------------------------------------

@etudiant_required
def etudiant_dashboard(request):
    student = Student.objects.filter(user=request.user).first()
    context = {
        'student': student,
    }
    return render(request, 'etudiant/dashboard/dashboard.html', context)

@etudiant_required
def etudiant_grades(request):
    student = Student.objects.filter(user=request.user).first()
    grades = Grade.objects.filter(student=student).select_related('evaluation__subject') if student else []
    return render(request, 'etudiant/grades/liste.html', {'grades': grades})

@etudiant_required
def etudiant_absences(request):
    student = Student.objects.filter(user=request.user).first()
    absences = Absence.objects.filter(student=student).select_related('evaluation__subject') if student else []
    return render(request, 'etudiant/absences/liste.html', {'absences': absences})

@etudiant_required
def etudiant_subjects(request):
    student = Student.objects.filter(user=request.user).first()
    subjects = Subject.objects.filter(semestre__niveau=student.niveau) if student and student.niveau else []
    return render(request, 'etudiant/subjects/liste.html', {'subjects': subjects})

@etudiant_required
def etudiant_arrieres(request):
    student = Student.objects.filter(user=request.user).first()
    arrieres = Arriere.objects.filter(student=student) if student else []
    return render(request, 'etudiant/arrears/liste.html', {'arrieres': arrieres})