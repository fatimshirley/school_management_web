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

        matricule = request.POST.get('matricule', '').strip()
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
        age = request.POST.get('age', '').strip()
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

        if Student.objects.filter(matricule=matricule).exists():
            return render(
                request,
                'admin/students/ajouter.html',
                {
                    'niveaux': niveaux,
                    'error': 'Ce matricule existe déjà.',
                }
            )

        niveau = get_object_or_404(Niveau, id=niveau_id)

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

        email_saisi = request.POST.get('email', '').strip()
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()

        if not email_saisi or not nom:
            return render(
                request,
                'admin/teachers/ajouter.html',
                {
                    'error': 'Veuillez renseigner les champs obligatoires.',
                }
            )

        if Teacher.objects.filter(identifiant=email_saisi).exists():
            return render(
                request,
                'admin/teachers/ajouter.html',
                {
                    'error': 'Cet email / identifiant existe déjà.',
                }
            )

        Teacher.objects.create(
            identifiant=email_saisi,
            nom=nom,
            prenom=prenom or None
        )

        return redirect('admin_teachers')

    return render(request, 'admin/teachers/ajouter.html')


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

    evaluations = (
        Evaluation.objects
        .select_related('subject', 'annee_universitaire')
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

        try:
            evaluation_id = int(evaluation_id)
        except (ValueError, TypeError):
            return render(
                request,
                'admin/grades/saisir.html',
                {
                    'students': students,
                    'evaluations': evaluations,
                    'error': "Sélection d'évaluation invalide.",
                }
            )

        Grade.objects.update_or_create(
            student_id=student_id,
            evaluation_id=evaluation_id,
            defaults={'note': note}
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
        .select_related('student', 'evaluation', 'evaluation__subject')
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
    evaluations = Evaluation.objects.select_related('subject').order_by('-date')

    if request.method == 'POST':

        student_id = request.POST.get('student')
        evaluation_id = request.POST.get('evaluation')
        date_absence = request.POST.get('date_absence')

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
def admin_absence_detail(request, absence_id):

    absence = get_object_or_404(
        Absence.objects.select_related('student', 'evaluation', 'evaluation__subject'),
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
    evaluations = Evaluation.objects.select_related('subject').order_by('-date')

    if request.method == 'POST':

        student_id = request.POST.get('student')
        evaluation_id = request.POST.get('evaluation')
        date_absence = request.POST.get('date_absence')

        if not student_id or not evaluation_id or not date_absence:
            return render(
                request,
                'admin/absences/modifier.html',
                {
                    'absence': absence,
                    'students': students,
                    'evaluations': evaluations,
                    'error': 'Veuillez renseigner tous les champs.',
                }
            )

        absence.student_id = student_id
        absence.evaluation_id = evaluation_id
        absence.date_absence = date_absence
        absence.save()

        return redirect('admin_absences')

    return render(
        request,
        'admin/absences/modifier.html',
        {
            'absence': absence,
            'students': students,
            'evaluations': evaluations,
        }
    )


@admin_required
def admin_absence_delete(request, absence_id):

    absence = get_object_or_404(Absence, id=absence_id)

    if request.method == 'POST':
        absence.delete()
        return redirect('admin_absences')

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

        if Filiere.objects.filter(code=code).exists():
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

        return redirect('admin_filieres')

    return render(
        request,
        'admin/academic/filiere_ajouter.html',
        {
            'niveaux': niveaux,
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


from django.shortcuts import render, get_object_or_404, redirect
from apps.academic.models import Semestre

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
        est_active = request.POST.get('est_active') == 'on'

        if not libelle:
            return render(
                request,
                'admin/academic/annee_ajouter.html',
                {
                    'error': "Le libellé de l'année universitaire est obligatoire.",
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

        if est_active:
            AnneeUniversitaire.objects.filter(est_active=True).update(est_active=False)

        AnneeUniversitaire.objects.create(
            libelle=libelle,
            est_active=est_active
        )

        return redirect('admin_annees')

    return render(request, 'admin/academic/annee_ajouter.html')


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
    context = {
        'teacher': teacher,
        'total_evaluations': Evaluation.objects.count(),
        'total_absences': Absence.objects.count(),
    }
    return render(request, 'professeur/dashboard/dashboard.html', context)

@professeur_required
def professeur_grades(request):
    grades = Grade.objects.select_related('student', 'evaluation__subject').all()
    return render(request, 'professeur/grades/liste.html', {'grades': grades})

@professeur_required
def professeur_grade_add(request):
    students = Student.objects.all()
    evaluations = Evaluation.objects.all()
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
    absences = Absence.objects.select_related('student', 'evaluation__subject').all()
    return render(request, 'professeur/absences/liste.html', {'absences': absences})

@professeur_required
def professeur_absence_add(request):
    students = Student.objects.all()
    evaluations = Evaluation.objects.all()
    if request.method == 'POST':
        student_id = request.POST.get('student')
        evaluation_id = request.POST.get('evaluation')
        date_absence = request.POST.get('date_absence')
        if student_id and evaluation_id and date_absence:
            Absence.objects.create(student_id=student_id, evaluation_id=evaluation_id, date_absence=date_absence)
            return redirect('professeur_absences')
    return render(request, 'professeur/absences/enregistrer.html', {'students': students, 'evaluations': evaluations})


# --------------------------------------------------
# DASHBOARD ÉTUDIANT
# --------------------------------------------------

@etudiant_required
def etudiant_dashboard(request):
    student = Student.objects.filter(matricule=request.user.email).first()
    context = {
        'student': student,
    }
    return render(request, 'etudiant/dashboard/dashboard.html', context)

@etudiant_required
def etudiant_grades(request):
    student = Student.objects.filter(matricule=request.user.email).first()
    grades = Grade.objects.filter(student=student).select_related('evaluation__subject') if student else []
    return render(request, 'etudiant/grades/liste.html', {'grades': grades})

@etudiant_required
def etudiant_absences(request):
    student = Student.objects.filter(matricule=request.user.email).first()
    absences = Absence.objects.filter(student=student).select_related('evaluation__subject') if student else []
    return render(request, 'etudiant/absences/liste.html', {'absences': absences})

@etudiant_required
def etudiant_subjects(request):
    student = Student.objects.filter(matricule=request.user.email).first()
    subjects = Subject.objects.filter(semestre__niveau=student.niveau) if student and student.niveau else []
    return render(request, 'etudiant/subjects/liste.html', {'subjects': subjects})

@etudiant_required
def etudiant_arrieres(request):
    student = Student.objects.filter(matricule=request.user.email).first()
    arrieres = Arriere.objects.filter(student=student) if student else []
    # Corriger "arrieres/liste.html" par "arrears/liste.html"
    return render(request, 'etudiant/arrears/liste.html', {'arrieres': arrieres})