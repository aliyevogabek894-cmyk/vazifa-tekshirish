from django.db import connection


def theme_and_user_processor(request):
    """
    Globally provides current user profile info and role to all templates.
    Ensures that templates can easily detect if user is student, teacher or school admin.
    """
    context = {
        'is_admin_user': False,
        'is_school_admin': False,
        'is_teacher': False,
        'student_profile': None,
        'admin_profile': None,
        'active_db_name': 'Neon PostgreSQL' if connection.vendor == 'postgresql' else 'SQLite',
        'is_postgres': connection.vendor == 'postgresql',
    }
    if request.user.is_authenticated:
        if hasattr(request.user, 'admin_profile'):
            context['admin_profile'] = request.user.admin_profile
            context['is_admin_user'] = True
            if request.user.is_superuser or request.user.admin_profile.role == 'admin':
                context['is_school_admin'] = True
            else:
                context['is_teacher'] = True
        elif request.user.is_staff or request.user.is_superuser:
            context['is_admin_user'] = True
            context['is_school_admin'] = True
        elif hasattr(request.user, 'student_profile'):
            context['student_profile'] = request.user.student_profile
    return context

