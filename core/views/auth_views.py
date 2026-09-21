import re
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from core.models import StudentProfile, AdminProfile, Classroom
from core.forms import StudentRegisterProfileForm
from core.utils.otp_service import normalize_phone, send_otp, verify_otp
from core.utils.audit import log_action


def student_login_view(request):
    """Student phone login - step 1: phone entry & OTP dispatch"""
    if request.user.is_authenticated:
        if request.user.is_staff or hasattr(request.user, 'admin_profile'):
            return redirect('admin_dashboard')
        return redirect('student_dashboard')

    if request.method == 'POST':
        raw_phone = request.POST.get('phone', '').strip()
        if not raw_phone:
            messages.error(request, "Telefon raqamingizni kiriting.")
            return render(request, 'auth/login.html')

        phone = normalize_phone(raw_phone)
        success, msg, otp_code = send_otp(phone)
        if success:
            request.session['auth_phone'] = phone
            # Store test otp in session for display in DEV mode
            request.session['dev_otp'] = otp_code
            messages.success(request, f"Telefoningizga 6 xonali tasdiqlash kodi yuborildi.")
            return redirect('verify_otp')
        else:
            messages.error(request, msg)

    return render(request, 'auth/login.html')


def verify_otp_view(request):
    """Student phone login - step 2: OTP verification"""
    phone = request.session.get('auth_phone')
    if not phone:
        messages.warning(request, "Iltimos, telefon raqamingizni kiriting.")
        return redirect('login')

    dev_otp = request.session.get('dev_otp')

    if request.method == 'POST':
        otp_code = request.POST.get('otp', '').strip()
        if not otp_code:
            messages.error(request, "Tasdiqlash kodini kiriting.")
            return render(request, 'auth/verify_otp.html', {'phone': phone, 'dev_otp': dev_otp})

        is_valid, msg = verify_otp(phone, otp_code)
        if is_valid:
            # Check if student already registered
            student_profile = StudentProfile.objects.filter(phone_number=phone).first()
            if student_profile:
                # Student exists, log in
                user = student_profile.user
                login(request, user)
                student_profile.last_active = timezone.now()
                student_profile.save()
                log_action(request, "O'quvchi tizimga kirdi", "StudentProfile", student_profile.id)
                # Clear session temp vars
                request.session.pop('auth_phone', None)
                request.session.pop('dev_otp', None)
                messages.success(request, f"Xush kelibsiz, {student_profile.first_name}!")
                return redirect('student_dashboard')
            else:
                # New student -> register profile
                return redirect('register_profile')
        else:
            messages.error(request, msg)

    return render(request, 'auth/verify_otp.html', {'phone': phone, 'dev_otp': dev_otp})


def register_profile_view(request):
    """First-time student profile registration"""
    phone = request.session.get('auth_phone')
    if not phone:
        messages.warning(request, "Iltimos, avval telefon raqamingizni tasdiqlang.")
        return redirect('login')

    if request.method == 'POST':
        form = StudentRegisterProfileForm(request.POST, request.FILES)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            classroom = form.cleaned_data['classroom']
            avatar = form.cleaned_data.get('avatar')

            # Create User
            digits_only = re.sub(r'[^0-9]', '', phone)[-9:]
            username = f"std_{digits_only}"
            base_user = username
            c = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_user}_{c}"
                c += 1

            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            user.set_unusable_password()
            user.save()

            profile = StudentProfile.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                classroom=classroom,
                phone_number=phone,
                avatar=avatar,
                last_active=timezone.now()
            )

            # Auto-enroll in all existing active assignments of this classroom
            for ass in classroom.assignments.filter(is_active=True):
                from core.models import StudentAssignment
                StudentAssignment.objects.get_or_create(assignment=ass, student=profile)

            login(request, user)
            log_action(request, "Yangi o'quvchi ro'yxatdan o'tdi", "StudentProfile", profile.id)
            request.session.pop('auth_phone', None)
            request.session.pop('dev_otp', None)
            messages.success(request, f"Profilingiz muvaffaqiyatli yaratildi, {first_name}!")
            return redirect('student_dashboard')
    else:
        form = StudentRegisterProfileForm()

    return render(request, 'auth/register_profile.html', {'form': form, 'phone': phone})


def admin_login_view(request):
    """Admin / Teacher username & password login"""
    if request.user.is_authenticated:
        if request.user.is_staff or hasattr(request.user, 'admin_profile'):
            return redirect('admin_dashboard')
        return redirect('student_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_staff or user.is_superuser or hasattr(user, 'admin_profile'):
                login(request, user)
                log_action(request, "Admin tizimga kirdi", "User", user.id)
                messages.success(request, f"Xush kelibsiz, {user.first_name or user.username}!")
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url and next_url.startswith('/'):
                    # Map old dashboard URLs if needed
                    if '/dashboard/submissions' in next_url:
                        return redirect('admin_submissions')
                    elif '/dashboard/assignments' in next_url:
                        return redirect('admin_assignments')
                    elif '/dashboard/students' in next_url:
                        return redirect('admin_students')
                    elif '/dashboard/classrooms' in next_url:
                        return redirect('admin_classrooms')
                    elif '/dashboard/reports' in next_url:
                        return redirect('admin_reports')
                    elif '/dashboard' in next_url:
                        return redirect('admin_dashboard')
                    return redirect(next_url)
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Ushbu profil administrator huquqiga ega emas.")
        else:
            messages.error(request, "Login yoki parol noto'g'ri!")

    next_url = request.GET.get('next', '')
    return render(request, 'auth/admin_login.html', {'next': next_url})


def logout_view(request):
    """Logout view for both student and admin"""
    if request.user.is_authenticated:
        log_action(request, "Tizimdan chiqdi")
    logout(request)
    messages.info(request, "Tizimdan muvaffaqiyatli chiqdingiz.")
    return redirect('login')


def accounts_login_redirect(request):
    """
    Backwards compatibility redirect for old bookmark or cached URLs.
    Redirects /accounts/login/ to /admin-login/ or /login/.
    """
    next_url = request.GET.get('next', '')
    if 'dashboard' in next_url or 'admin' in next_url or 'submission' in next_url:
        return redirect(f"/admin-login/?next={next_url}")
    return redirect(f"/login/?next={next_url}")

