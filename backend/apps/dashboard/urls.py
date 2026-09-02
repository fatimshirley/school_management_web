from django.urls import path

from . import views


urlpatterns = [

    # ==================================================
    # DASHBOARDS
    # ==================================================

    path(
        '',
        views.dashboard,
        name='dashboard'
    ),

    path(
        'admin/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

    path(
        'professeur/',
        views.professeur_dashboard,
        name='professeur_dashboard'
    ),

    path(
        'etudiant/',
        views.etudiant_dashboard,
        name='etudiant_dashboard'
    ),


    # ==================================================
    # ÉTUDIANTS
    # ==================================================

    path(
        'admin/etudiants/',
        views.admin_students,
        name='admin_students'
    ),

    path(
        'admin/etudiants/ajouter/',
        views.admin_student_add,
        name='admin_student_add'
    ),

    path(
        'admin/etudiants/<int:student_id>/',
        views.admin_student_detail,
        name='admin_student_detail'
    ),

    path(
        'admin/etudiants/<int:student_id>/modifier/',
        views.admin_student_edit,
        name='admin_student_edit'
    ),

    path(
        'admin/etudiants/<int:student_id>/supprimer/',
        views.admin_student_delete,
        name='admin_student_delete'
    ),


    # ==================================================
    # PROFESSEURS
    # ==================================================

    path(
        'admin/professeurs/',
        views.admin_teachers,
        name='admin_teachers'
    ),

    path(
        'admin/professeurs/ajouter/',
        views.admin_teacher_add,
        name='admin_teacher_add'
    ),

    path(
        'admin/professeurs/<int:teacher_id>/',
        views.admin_teacher_detail,
        name='admin_teacher_detail'
    ),

    path(
        'admin/professeurs/<int:teacher_id>/modifier/',
        views.admin_teacher_edit,
        name='admin_teacher_edit'
    ),

    path(
        'admin/professeurs/<int:teacher_id>/supprimer/',
        views.admin_teacher_delete,
        name='admin_teacher_delete'
    ),


    # ==================================================
    # MATIÈRES
    # ==================================================

    path(
        'admin/matieres/',
        views.admin_subjects,
        name='admin_subjects'
    ),

    path(
        'admin/matieres/ajouter/',
        views.admin_subject_add,
        name='admin_subject_add'
    ),

    path(
        'admin/matieres/<int:subject_id>/',
        views.admin_subject_detail,
        name='admin_subject_detail'
    ),

    path(
        'admin/matieres/<int:subject_id>/modifier/',
        views.admin_subject_edit,
        name='admin_subject_edit'
    ),

    path(
        'admin/matieres/<int:subject_id>/supprimer/',
        views.admin_subject_delete,
        name='admin_subject_delete'
    ),


    # ==================================================
    # NOTES
    # ==================================================

    path(
        'admin/notes/',
        views.admin_grades,
        name='admin_grades'
    ),

    path(
        'admin/notes/saisir/',
        views.admin_grade_add,
        name='admin_grade_add'
    ),

    path(
        'admin/notes/historique/',
        views.admin_grade_history,
        name='admin_grade_history'
    ),


    # ==================================================
    # ABSENCES
    # ==================================================

    path(
        'admin/absences/',
        views.admin_absences,
        name='admin_absences'
    ),

    path(
        'admin/absences/enregistrer/',
        views.admin_absence_add,
        name='admin_absence_add'
    ),

    path(
        'admin/absences/<int:absence_id>/',
        views.admin_absence_detail,
        name='admin_absence_detail'
    ),

    path(
        'admin/absences/<int:absence_id>/modifier/',
        views.admin_absence_edit,
        name='admin_absence_edit'
    ),

    path(
        'admin/absences/<int:absence_id>/supprimer/',
        views.admin_absence_delete,
        name='admin_absence_delete'
    ),

    path(
        'admin/absences/<int:absence_id>/justifier/',
        views.admin_absence_justify,
        name='admin_absence_justify'
    ),

    path(
        'admin/absences/<int:absence_id>/rattrapage/',
        views.admin_absence_makeup,
        name='admin_absence_makeup'
    ),


    # ==================================================
    # FILIÈRES
    # ==================================================

    path(
        'admin/filieres/',
        views.admin_filieres,
        name='admin_filieres'
    ),

    path(
        'admin/filieres/ajouter/',
        views.admin_filiere_add,
        name='admin_filiere_add'
    ),


    # ==================================================
    # NIVEAUX
    # ==================================================

    path(
        'admin/niveaux/',
        views.admin_niveaux,
        name='admin_niveaux'
    ),

    path(
        'admin/niveaux/ajouter/',
        views.admin_niveau_add,
        name='admin_niveau_add'
    ),


    # ==================================================
    # SEMESTRES
    # ==================================================

    path(
        'admin/semestres/',
        views.admin_semestres,
        name='admin_semestres'
    ),

    path(
        'admin/semestres/ajouter/',
        views.admin_semestre_add,
        name='admin_semestre_add'
    ),


    # ==================================================
    # ANNÉES UNIVERSITAIRES
    # ==================================================

    path(
        'admin/annees/',
        views.admin_annees,
        name='admin_annees'
    ),

    path(
        'admin/annees/ajouter/',
        views.admin_annee_add,
        name='admin_annee_add'
    ),


    # ==================================================
    # ARRIÉRÉS
    # ==================================================

    path(
        'admin/arrieres/',
        views.admin_arrieres,
        name='admin_arrieres'
    ),

    path(
        'admin/arrieres/ajouter/',
        views.admin_arriere_add,
        name='admin_arriere_add'
    ),

]