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


@admin_required
def admin_student_add(request):

    niveaux = Niveau.objects.order_by('code')

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

        if not matricule or not nom or not prenom or not age or not niveau_id:

            return render(
                request,
                'admin/students/ajouter.html',
                {
                    'niveaux': niveaux,
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
                    'error': "L'âge doit être un nombre entier.",
                }
            )

        if age <= 0:

            return render(
                request,
                'admin/students/ajouter.html',
                {
                    'niveaux': niveaux,
                    'error': "L'âge doit être supérieur à 0.",
                }
            )

        if Student.objects.filter(
            matricule=matricule
        ).exists():

            return render(
                request,
                'admin/students/ajouter.html',
                {
                    'niveaux': niveaux,
                    'error': 'Ce matricule existe déjà.',
                }
            )

        niveau = get_object_or_404(
            Niveau,
            id=niveau_id
        )

        Student.objects.create(
            matricule=matricule,
            nom=nom,
            prenom=prenom,
            age=age,
            niveau=niveau
        )

        return redirect('admin_students')

    return render(
        request,
        'admin/students/ajouter.html',
        {
            'niveaux': niveaux,
        }
    )


@admin_required
def admin_student_detail(request, student_id):

    student = get_object_or_404(
        Student.objects.select_related('niveau'),
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

        if Student.objects.filter(
            matricule=matricule
        ).exclude(
            id=student.id
        ).exists():

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
        }
    )


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
                'admin/teachers/ajouter.html',
                {
                    'error': 'Veuillez renseigner les champs obligatoires.',
                }
            )

        if Teacher.objects.filter(
            identifiant=identifiant
        ).exists():

            return render(
                request,
                'admin/teachers/ajouter.html',
                {
                    'error': 'Cet identifiant existe déjà.',
                }
            )

        Teacher.objects.create(
            identifiant=identifiant,
            nom=nom,
            prenom=prenom or None
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
                    'error': 'Veuillez renseigner les champs obligatoires.',
                }
            )

        if Teacher.objects.filter(
            identifiant=identifiant
        ).exclude(
            id=teacher.id
        ).exists():

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

    subjects = (
        Subject.objects
        .select_related(
            'semestre',
            'semestre__niveau'
        )
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

        semestre_id = request.POST.get(
            'semestre'
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
                    'teachers': teachers,
                    'error': 'Le nom de la matière est obligatoire.',
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

        semestre_id = request.POST.get(
            'semestre'
        )

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
                    'error': 'Le nom de la matière est obligatoire.',
                }
            )

        if Subject.objects.filter(
            nom=nom
        ).exclude(
            id=subject.id
        ).exists():

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
            'evaluation__annee_universitaire',
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

    students = (
        Student.objects
        .order_by('nom', 'prenom')
    )

    evaluations = (
        Evaluation.objects
        .select_related(
            'subject',
            'annee_universitaire'
        )
        .order_by('-date')
    )

    if request.method == 'POST':

        student_id = request.POST.get('student')
        evaluation_id = request.POST.get('evaluation')
        note = request.POST.get('note', '').strip()

        if not student_id or not evaluation_id or not note:

            return render(
                request,
                'admin/grades/saisir.html',
                {
                    'students': students,
                    'evaluations': evaluations,
                    'error': 'Veuillez renseigner tous les champs.',
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
                    'evaluations': evaluations,
                    'error': 'La note doit être numérique.',
                }
            )

        if note < 0 or note > 20:

            return render(
                request,
                'admin/grades/saisir.html',
                {
                    'students': students,
                    'evaluations': evaluations,
                    'error': 'La note doit être comprise entre 0 et 20.',
                }
            )

        Grade.objects.update_or_create(
            student_id=student_id,
            evaluation_id=evaluation_id,
            defaults={
                'note': note,
            }
        )

        return redirect('admin_grades')

    return render(
        request,
        'admin/grades/saisir.html',
        {
            'students': students,
            'evaluations': evaluations,
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
            'evaluation',
            'evaluation__subject',
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

    students = (
        Student.objects
        .order_by('nom', 'prenom')
    )

    evaluations = (
        Evaluation.objects
        .select_related('subject')
        .order_by('-date')
    )

    if request.method == 'POST':

        student_id = request.POST.get('student')
        evaluation_id = request.POST.get('evaluation')
        date_absence = request.POST.get(
            'date_absence'
        )

        if not student_id or not evaluation_id or not date_absence:

            return render(
                request,
                'admin/absences/enregistrer.html',
                {
                    'students': students,
                    'evaluations': evaluations,
                    'error': 'Veuillez renseigner tous les champs.',
                }
            )

        Absence.objects.create(
            student_id=student_id,
            evaluation_id=evaluation_id,
            date_absence=date_absence
        )

        return redirect('admin_absences')

    return render(
        request,
        'admin/absences/enregistrer.html',
        {
            'students': students,
            'evaluations': evaluations,
        }
    )


@admin_required
def admin_absence_justify(request, absence_id):

    absence = get_object_or_404(
        Absence,
        id=absence_id
    )

    if request.method == 'POST':

        absence.justifiee = True

        absence.justification = request.POST.get(
            'justification',
            ''
        ).strip()

        absence.date_justification = (
            request.POST.get('date_justification')
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

        absence.rattrapage_effectue = True

        absence.note_rattrapage = (
            request.POST.get('note_rattrapage')
            or None
        )

        absence.date_rattrapage = (
            request.POST.get('date_rattrapage')
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


# ==================================================
# DASHBOARD PROFESSEUR
# ==================================================

@login_required
def professeur_dashboard(request):

    profile = UserProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('connexion')

    if profile.role != 'professeur':
        return redirect('dashboard')

    return render(
        request,
        'professeur/dashboard/dashboard.html'
    )


# ==================================================
# DASHBOARD ÉTUDIANT
# ==================================================

@login_required
def etudiant_dashboard(request):

    profile = UserProfile.objects.filter(
        user=request.user
    ).first()

    if profile is None:
        return redirect('connexion')

    if profile.role != 'etudiant':
        return redirect('dashboard')

    return render(
        request,
        'etudiant/dashboard/dashboard.html'
    )