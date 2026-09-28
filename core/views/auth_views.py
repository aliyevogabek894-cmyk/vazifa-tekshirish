import re
import random
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from core.models import StudentProfile, AdminProfile, Classroom
from core.forms import StudentRegisterProfileForm
from core.utils.otp_service import normalize_phone
from core.utils.audit import log_action


def student_login_view(request):
    """
    O'quvchilar kirish oynasi:
    - Har safar: Telefon raqami va berilgan Paroli bilan kiradi.
    - 1-marta kirayotganda: Telefonini kiritadi va unga 1 marta parol beriladi (ekranda ko'rsatiladi).
    """
    if request.user.is_authenticated:
        if request.user.is_staff or hasattr(request.user, 'admin_profile'):
            return redirect('admin_dashboard')
        return redirect('student_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action', 'login')
        raw_phone = request.POST.get('phone', '').strip()

        if not raw_phone:
            messages.error(request, "Telefon raqamingizni kiriting.")
            return render(request, 'auth/login.html')

        phone = normalize_phone(raw_phone)

        # 1-holat: Doimiy kirish (Telefon + Parol)
        if action == 'login':
            password = request.POST.get('password', '').strip()
            if not password:
                messages.error(request, "Iltimos, parolingizni kiriting. Agar hali parolingiz bo'lmasa, 'Parol olish' tugmasidan foydalaning.")
                return render(request, 'auth/login.html', {'phone': raw_phone})

            student_profile = StudentProfile.objects.filter(phone_number=phone).first()
            if not student_profile:
                messages.warning(request, "Ushbu telefon raqam ro'yxatdan o'tmagan! Iltimos, 'Parol olish' bo'limi orqali parolingizni oling.")
                return render(request, 'auth/login.html', {'phone': raw_phone, 'active_tab': 'get_password'})

            user = authenticate(request, username=student_profile.user.username, password=password)
            if user is not None:
                if not student_profile.is_active:
                    messages.error(request, "Profilingiz faol emas. Iltimos, maktab ma'muriyatiga murojaat qiling.")
                    return render(request, 'auth/login.html', {'phone': raw_phone})

                login(request, user)
                student_profile.last_active = timezone.now()
                student_profile.save()
                log_action(request, "O'quvchi tizimga kirdi", "StudentProfile", student_profile.id)
                messages.success(request, f"Xush kelibsiz, {student_profile.first_name}!")
                return redirect('student_dashboard')
            else:
                messages.error(request, "Kiritilgan parol noto'g'ri! Agar parolingizni unutgan bo'lsangiz, 'Parol olish' tugmasi orqali qayta oling.")
                return render(request, 'auth/login.html', {'phone': raw_phone})

        # 2-holat: 1 martalik parol olish / yangilash
        elif action == 'get_password':
            # 6 xonali maxsus parol yaratamiz
            pin = f"{random.randint(100000, 999999)}"
            student_profile = StudentProfile.objects.filter(phone_number=phone).first()

            if student_profile:
                # O'quvchi avval ro'yxatdan o'tgan -> uning paroli yangilanadi
                student_profile.user.set_password(pin)
                student_profile.user.save()
                student_profile.raw_password = pin
                student_profile.save()

                request.session['issued_phone'] = phone
                request.session['issued_password'] = pin
                request.session['student_name'] = student_profile.full_name
                request.session['is_new'] = False

                log_action(request, f"O'quvchi paroli berildi: {student_profile.full_name}", "StudentProfile", student_profile.id)
                return redirect('student_password_issued')
            else:
                # Yangi o'quvchi -> profil to'ldirish bosqichiga o'tadi
                request.session['auth_phone'] = phone
                request.session['auth_pin'] = pin
                messages.info(request, "Telefon raqamingiz qabul qilindi. Endi o'zingiz haqingizda ma'lumotlarni kiriting.")
                return redirect('register_profile')

    return render(request, 'auth/login.html')


def student_password_issued_view(request):
    """
    O'quvchiga uning 1 marta berilgan parolini katta va aniq ko'rsatuvchi sahifa
    """
    phone = request.session.get('issued_phone')
    password = request.session.get('issued_password')
    student_name = request.session.get('student_name', "O'quvchi")
    is_new = request.session.get('is_new', False)

    if not phone or not password:
        return redirect('login')

    context = {
        'phone': phone,
        'password': password,
        'student_name': student_name,
        'is_new': is_new,
    }
    return render(request, 'auth/password_issued.html', context)


def register_profile_view(request):
    """Yangi o'quvchi birinchi marta kirganda profilni to'ldirishi"""
    phone = request.session.get('auth_phone')
    pin = request.session.get('auth_pin')

    if not phone:
        messages.warning(request, "Iltimos, avval telefon raqamingizni kiriting.")
        return redirect('login')

    if not pin:
        pin = f"{random.randint(100000, 999999)}"

    if request.method == 'POST':
        form = StudentRegisterProfileForm(request.POST, request.FILES)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            classroom = form.cleaned_data['classroom']
            avatar = form.cleaned_data.get('avatar')

            # User yaratish
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
            user.set_password(pin)
            user.save()

            profile = StudentProfile.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                classroom=classroom,
                phone_number=phone,
                raw_password=pin,
                avatar=avatar,
                last_active=timezone.now()
            )

            # Sinfga biriktirilgan faol vazifalarni bog'lash
            for ass in classroom.assignments.filter(is_active=True):
                from core.models import StudentAssignment
                StudentAssignment.objects.get_or_create(assignment=ass, student=profile)

            # Tizimga kiritish
            login(request, user)
            log_action(request, "Yangi o'quvchi ro'yxatdan o'tdi va parol berildi", "StudentProfile", profile.id)

            request.session.pop('auth_phone', None)
            request.session.pop('auth_pin', None)

            request.session['issued_phone'] = phone
            request.session['issued_password'] = pin
            request.session['student_name'] = profile.full_name
            request.session['is_new'] = True

            return redirect('student_password_issued')
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
                role_title = "O'qituvchi"
                if hasattr(user, 'admin_profile') and user.admin_profile.role == 'admin':
                    role_title = "Administrator"
                elif user.is_superuser:
                    role_title = "Bosh administrator"

                log_action(request, f"{role_title} tizimga kirdi", "User", user.id)
                messages.success(request, f"Xush kelibsiz, {user.first_name or user.username}! ({role_title})")
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Ushbu profil o'qituvchi yoki administrator huquqiga ega emas.")
        else:
            messages.error(request, "Login yoki parol noto'g'ri!")

    next_url = request.GET.get('next', '')
    return render(request, 'auth/admin_login.html', {'next': next_url})


def logout_view(request):
    """Logout view for student, teacher and admin"""
    if request.user.is_authenticated:
        log_action(request, "Tizimdan chiqdi")
    logout(request)
    messages.info(request, "Tizimdan muvaffaqiyatli chiqdingiz.")
    return redirect('login')


def accounts_login_redirect(request):
    """Backwards compatibility redirect"""
    next_url = request.GET.get('next', '')
    if 'dashboard' in next_url or 'admin' in next_url or 'submission' in next_url:
        return redirect(f"/admin-login/?next={next_url}")
    return redirect(f"/login/?next={next_url}")


def verify_otp_view(request):
    """Backwards compatibility redirect to modern password login"""
    return redirect('login')

