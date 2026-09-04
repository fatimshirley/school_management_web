from django.urls import path
from django.contrib.auth.views import LogoutView
from django.contrib.auth import logout
from django.shortcuts import redirect
from . import views

# Classe personnalisée qui déconnecte l'utilisateur et le redirige instantanément
class CustomLogoutView(LogoutView):
    http_method_names = ['get', 'post', 'options']

    def dispatch(self, request, *args, **kwargs):
        # Déconnecte l'utilisateur
        logout(request)
        # Redirige immédiatement vers la page de connexion admin (ou l'URL de votre choix)
        return redirect('connexion')

urlpatterns = [

    # ==================================================
    # DÉCONNEXION
    # ==================================================
    path(
        'logout/',
        CustomLogoutView.as_view(),
        name='logout'
    ),

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
    # ÉTUDIANTS (ADMIN)
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
    # PROFESSEURS (ADMIN)
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
    # MATIÈRES (ADMIN)
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
    # NOTES (ADMIN)
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
    # ABSENCES (ADMIN)
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
    # FILIÈRES (ADMIN)
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

    path(
        'admin/filieres/modifier/<int:pk>/',
        views.admin_filiere_edit,
        name='admin_filiere_edit'
    ),

    path(
        'admin/filieres/supprimer/<int:pk>/',
        views.admin_filiere_delete,
        name='admin_filiere_delete'
    ),


    # ==================================================
    # NIVEAUX (ADMIN)
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

    path(
        'admin/niveaux/modifier/<int:pk>/',
        views.admin_niveau_edit,
        name='admin_niveau_edit'
    ),

    path(
        'admin/niveaux/supprimer/<int:pk>/',
        views.admin_niveau_delete,
        name='admin_niveau_delete'
    ),


    # ==================================================
    # SEMESTRES (ADMIN)
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

    path(
        'admin/semestres/<int:semestre_id>/modifier/',
        views.admin_semestre_edit,
        name='admin_semestre_edit'
    ),

    path(
        'admin/semestres/<int:semestre_id>/supprimer/',
        views.admin_semestre_delete,
        name='admin_semestre_delete'
    ),


    # ==================================================
    # ANNÉES UNIVERSITAIRES (ADMIN)
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

    path(
        'admin/annees/modifier/<int:pk>/',
        views.admin_annee_edit,
        name='admin_annee_edit'
    ),

    path(
        'admin/annees/supprimer/<int:pk>/',
        views.admin_annee_delete,
        name='admin_annee_delete'
    ),


    # ==================================================
    # ARRIÉRÉS (ADMIN)
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

    path(
        'admin/arrieres/generer/',
        views.admin_generer_arrieres_automatique,
        name='admin_generer_arrieres'
    ),


    # ==================================================
    # ESPACE PROFESSEUR
    # ==================================================

    path(
        'professeur/evaluations/',
        views.professeur_evaluations,
        name='professeur_evaluations'
    ),

    path(
        'professeur/evaluations/ajouter/',
        views.professeur_evaluation_ajouter,
        name='professeur_evaluation_ajouter'
    ),

    path(
        'professeur/etudiants/',
        views.professeur_students,
        name='professeur_students'
    ),

    path(
        'professeur/matieres/',
        views.professeur_subjects,
        name='professeur_subjects'
    ),

    path(
        'professeur/notes/',
        views.professeur_grades,
        name='professeur_grades'
    ),

    path(
        'professeur/notes/saisir/',
        views.professeur_grade_add,
        name='professeur_grade_add'
    ),

    path(
        'professeur/absences/',
        views.professeur_absences,
        name='professeur_absences'
    ),

    path(
        'professeur/absences/enregistrer/',
        views.professeur_absence_add,
        name='professeur_absence_add'
    ),


    # ==================================================
    # ESPACE ÉTUDIANT
    # ==================================================

    path(
        'etudiant/notes/',
        views.etudiant_grades,
        name='etudiant_grades'
    ),

    path(
        'etudiant/absences/',
        views.etudiant_absences,
        name='etudiant_absences'
    ),

    path(
        'etudiant/matieres/',
        views.etudiant_subjects,
        name='etudiant_subjects'
    ),

    path(
        'etudiant/arrieres/',
        views.etudiant_arrieres,
        name='etudiant_arrieres'
    ),

]