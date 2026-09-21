from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, Http404
from django.contrib import messages


def admin_required(view_func):
    """Decorator ensuring that the logged in user is an Admin / Teacher"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_login')
        if not (request.user.is_staff or request.user.is_superuser or hasattr(request.user, 'admin_profile')):
            messages.error(request, "Ushbu sahifaga faqat administratorlar kira oladi!")
            return redirect('student_dashboard' if hasattr(request.user, 'student_profile') else 'login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def student_required(view_func):
    """Decorator ensuring that the logged in user is an enrolled Student"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_staff or request.user.is_superuser:
            # If admin visits student dashboard, let them or redirect to admin panel
            return redirect('admin_dashboard')
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, "O'quvchi profili topilmadi. Iltimos, profilingizni to'ldiring.")
            return redirect('register_profile')
        if not request.user.student_profile.is_active:
            messages.error(request, "Profilingiz faol emas. Iltimos, ma'muriyatga murojaat qiling.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def verify_student_owns_assignment(user, student_assignment):
    """
    Validates that student only accesses their own assignment.
    Staff/Admin can access any.
    """
    if user.is_staff or user.is_superuser:
        return True
    if hasattr(user, 'student_profile') and student_assignment.student_id == user.student_profile.id:
        return True
    return False


def verify_student_owns_attachment(user, attachment):
    """
    Validates that only the student owner or admin can download/view the file.
    """
    if user.is_staff or user.is_superuser:
        return True
    if hasattr(user, 'student_profile'):
        sub = attachment.submission
        if sub.student_assignment.student_id == user.student_profile.id:
            return True
    return False
