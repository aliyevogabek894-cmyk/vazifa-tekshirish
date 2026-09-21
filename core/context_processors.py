def theme_and_user_processor(request):
    """
    Globally provides current user profile info and role to all templates.
    Ensures that templates can easily detect if user is student or admin.
    """
    context = {
        'is_admin_user': False,
        'student_profile': None,
        'admin_profile': None,
    }
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            context['is_admin_user'] = True
            if hasattr(request.user, 'admin_profile'):
                context['admin_profile'] = request.user.admin_profile
        elif hasattr(request.user, 'student_profile'):
            context['student_profile'] = request.user.student_profile
    return context
