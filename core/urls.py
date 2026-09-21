from django.urls import path
from core.views import auth_views, student_views, admin_views, reports_views, export_views, media_views

urlpatterns = [
    # Auth
    path('login/', auth_views.student_login_view, name='login'),
    path('verify-otp/', auth_views.verify_otp_view, name='verify_otp'),
    path('register-profile/', auth_views.register_profile_view, name='register_profile'),
    path('admin-login/', auth_views.admin_login_view, name='admin_login'),
    path('logout/', auth_views.logout_view, name='logout'),

    # Student portal
    path('', student_views.student_dashboard, name='student_dashboard'),
    path('task/<int:task_id>/', student_views.student_assignment_detail, name='student_assignment_detail'),
    path('profile/', student_views.student_profile_view, name='student_profile'),

    # Admin Panel
    path('admin-panel/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/classrooms/', admin_views.classrooms_view, name='admin_classrooms'),
    path('admin-panel/students/', admin_views.students_view, name='admin_students'),
    path('admin-panel/students/import/', admin_views.student_excel_import_view, name='admin_students_import'),
    path('admin-panel/assignments/', admin_views.assignments_view, name='admin_assignments'),
    path('admin-panel/submissions/', admin_views.submissions_view, name='admin_submissions'),
    path('admin-panel/review/<int:task_id>/', admin_views.review_submission_view, name='admin_review_submission'),
    path('admin-panel/reports/', reports_views.reports_view, name='admin_reports'),
    path('admin-panel/reports/export/', export_views.export_excel_report_view, name='admin_export_excel'),
    path('admin-panel/reports/get-students/', reports_views.get_students_by_class, name='admin_get_students_ajax'),
    path('admin-panel/audit-logs/', admin_views.audit_logs_view, name='admin_audit_logs'),

    # Protected Media
    path('secure-media/submission/<int:attachment_id>/', media_views.secure_submission_media_view, name='secure_submission_media'),
    path('secure-media/assignment/<int:assignment_id>/', media_views.secure_assignment_media_view, name='secure_assignment_media'),
]
