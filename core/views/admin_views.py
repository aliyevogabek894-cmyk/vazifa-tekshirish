import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Q
from django.http import JsonResponse

from core.models import (
    Classroom, StudentProfile, Assignment, Subject,
    StudentAssignment, Submission, SubmissionAttachment, SubmissionHistory, AuditLog, AdminProfile
)
from core.forms import AssignmentForm, StudentAdminForm, ClassroomForm, SubjectForm, TeacherCreateForm
from core.permissions import admin_required, admin_only_required, is_admin_user, is_teacher_user
from core.utils.audit import log_action
from core.utils.excel_importer import import_students_from_excel


@admin_required
def admin_dashboard(request):
    total_classrooms = Classroom.objects.filter(is_active=True).count()
    total_students = StudentProfile.objects.filter(is_active=True).count()
    total_assignments = Assignment.objects.filter(is_active=True).count()
    total_teachers = AdminProfile.objects.filter(role='teacher').count()

    # Aggregate submission statuses
    all_student_assignments = StudentAssignment.objects.all()
    completed_count = all_student_assignments.filter(status__in=['completed', 'approved']).count()
    not_started_count = all_student_assignments.filter(status__in=['not_started', 'overdue']).count()
    pending_review_count = all_student_assignments.filter(status__in=['submitted', 'under_review']).count()
    approved_count = all_student_assignments.filter(status='approved').count()
    needs_work_count = all_student_assignments.filter(status='needs_work').count()

    # Recent submissions waiting for review
    recent_submissions = StudentAssignment.objects.filter(
        status__in=['submitted', 'under_review', 'completed']
    ).select_related('student', 'student__classroom', 'assignment', 'submission').order_by('-updated_at')[:8]

    # Chart 1: Status distribution
    status_chart_data = {
        'labels': ['Qabul qilindi', 'Bajarildi', 'Kutilmoqda', 'Qayta ishlash', 'Bajarilmagan'],
        'data': [approved_count, completed_count - approved_count, pending_review_count, needs_work_count, not_started_count]
    }

    # Chart 2: Completion rate by classroom (optimized single query)
    class_labels = []
    class_completion_rates = []
    active_classes = list(Classroom.objects.filter(is_active=True)[:8])
    if active_classes:
        class_stats = StudentAssignment.objects.filter(
            student__classroom__in=active_classes
        ).values('student__classroom').annotate(
            total=Count('id'),
            done=Count('id', filter=Q(status__in=['completed', 'approved']))
        )
        stats_map = {s['student__classroom']: s for s in class_stats}
        for c in active_classes:
            c_data = stats_map.get(c.id, {'total': 0, 'done': 0})
            c_total = c_data['total']
            c_done = c_data['done']
            rate = round((c_done / c_total * 100), 1) if c_total > 0 else 0
            class_labels.append(c.name)
            class_completion_rates.append(rate)

    context = {
        'total_classrooms': total_classrooms,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_assignments': total_assignments,
        'completed_count': completed_count,
        'not_started_count': not_started_count,
        'pending_review_count': pending_review_count,
        'approved_count': approved_count,
        'recent_submissions': recent_submissions,
        'status_chart_json': json.dumps(status_chart_data),
        'class_chart_labels_json': json.dumps(class_labels),
        'class_chart_data_json': json.dumps(class_completion_rates),
        'is_school_admin': is_admin_user(request.user),
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_only_required
def teachers_view(request):
    """
    O'qituvchilarni boshqarish bo'limi:
    Admin o'qituvchilarga login va parol beradi, fanlarini biriktiradi.
    """
    teachers = AdminProfile.objects.filter(role='teacher').select_related('user', 'subject').prefetch_related('classrooms').order_by('-created_at')
    subjects = Subject.objects.filter(is_active=True)
    classrooms = Classroom.objects.filter(is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            form = TeacherCreateForm(request.POST)
            if form.is_valid():
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                full_name = form.cleaned_data['full_name']
                phone_number = form.cleaned_data.get('phone_number', '')
                subject = form.cleaned_data.get('subject')
                cls_list = form.cleaned_data.get('classrooms')

                # Create User
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    first_name=full_name.split()[0] if full_name else '',
                    is_staff=True
                )

                # Create Teacher AdminProfile
                teacher_prof = AdminProfile.objects.create(
                    user=user,
                    full_name=full_name,
                    phone_number=phone_number,
                    role='teacher',
                    subject=subject,
                    raw_password=password
                )
                if cls_list:
                    teacher_prof.classrooms.set(cls_list)

                log_action(request, f"Yangi o'qituvchi qo'shildi: {full_name} (login: {username})", "AdminProfile", teacher_prof.id)
                messages.success(request, f"O'qituvchi '{full_name}' muvaffaqiyatli yaratildi! Login: {username}, Parol: {password}")
                return redirect('admin_teachers')
            else:
                messages.error(request, f"Xatolik: {form.errors}")

        elif action == 'update_password':
            teacher_id = request.POST.get('teacher_id')
            new_pass = request.POST.get('new_password', '').strip()
            if teacher_id and new_pass:
                t_prof = get_object_or_404(AdminProfile, id=teacher_id, role='teacher')
                t_prof.user.set_password(new_pass)
                t_prof.user.save()
                t_prof.raw_password = new_pass
                t_prof.save()
                log_action(request, f"O'qituvchi paroli yangilandi: {t_prof.full_name}", "AdminProfile", t_prof.id)
                messages.success(request, f"{t_prof.full_name} paroli yangilandi: {new_pass}")
            return redirect('admin_teachers')

        elif action == 'delete':
            teacher_id = request.POST.get('teacher_id')
            t_prof = get_object_or_404(AdminProfile, id=teacher_id, role='teacher')
            name = t_prof.full_name
            t_user = t_prof.user
            t_prof.delete()
            t_user.delete()
            log_action(request, f"O'qituvchi o'chirildi: {name}", "AdminProfile", teacher_id)
            messages.success(request, f"O'qituvchi {name} tizimdan o'chirildi.")
            return redirect('admin_teachers')

    form = TeacherCreateForm()
    return render(request, 'admin_panel/teachers.html', {
        'teachers': teachers,
        'subjects': subjects,
        'classrooms': classrooms,
        'form': form,
    })


@admin_required
def classrooms_view(request):
    now = timezone.now()
    classrooms_qs = Classroom.objects.filter(is_active=True).annotate(
        students_total=Count('students', filter=Q(students__is_active=True), distinct=True)
    ).order_by('grade_level', 'name')

    # Har bir sinf uchun o'quvchilar vazifa statistikasi (qildi, qilmadi, kech qoldi)
    class_stats = []
    for c in classrooms_qs:
        tasks = StudentAssignment.objects.filter(student__classroom=c, student__is_active=True)
        completed_c = tasks.filter(status__in=['completed', 'approved', 'submitted', 'under_review']).count()
        overdue_c = tasks.filter(Q(status='overdue') | Q(status='not_started', assignment__due_date__lt=now)).count()
        not_done_c = tasks.filter(status='not_started', assignment__due_date__gte=now).count()

        class_stats.append({
            'classroom': c,
            'students_total': c.students_total,
            'completed_count': completed_c,
            'not_done_count': not_done_c,
            'overdue_count': overdue_c,
        })

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            form = ClassroomForm(request.POST)
            if form.is_valid():
                cls_obj = form.save()
                log_action(request, f"Yangi sinf yaratildi: {cls_obj.name}", "Classroom", cls_obj.id)
                messages.success(request, f"{cls_obj.name} sinfi muvaffaqiyatli yaratildi!")
                return redirect('admin_classrooms')
            else:
                messages.error(request, "Ma'lumotlar to'ldirishda xatolik yuz berdi.")
        elif action == 'delete':
            class_id = request.POST.get('classroom_id')
            cls_obj = get_object_or_404(Classroom, id=class_id)
            name = cls_obj.name
            cls_obj.delete()
            log_action(request, f"Sinf o'chirildi: {name}", "Classroom", class_id)
            messages.success(request, f"{name} sinfi o'chirildi.")
            return redirect('admin_classrooms')

    form = ClassroomForm()
    return render(request, 'admin_panel/classrooms.html', {
        'class_stats': class_stats,
        'form': form
    })


@admin_required
def students_view(request):
    query = request.GET.get('q', '').strip()
    class_id = request.GET.get('classroom_id')
    now = timezone.now()

    students_qs = StudentProfile.objects.select_related('classroom', 'user')
    selected_classroom = None
    class_metrics = None

    if class_id:
        selected_classroom = Classroom.objects.filter(id=class_id).first()
        if selected_classroom:
            students_qs = students_qs.filter(classroom_id=class_id)

            # Sinfga oid vazifalar statistikasi: Necha kishi qildi, necha kishi qilmadi, necha kishi kech qoldi
            tasks = StudentAssignment.objects.filter(student__classroom=selected_classroom, student__is_active=True)
            completed_c = tasks.filter(status__in=['completed', 'approved', 'submitted', 'under_review']).count()
            overdue_c = tasks.filter(Q(status='overdue') | Q(status='not_started', assignment__due_date__lt=now)).count()
            not_done_c = tasks.filter(status='not_started', assignment__due_date__gte=now).count()

            class_metrics = {
                'classroom': selected_classroom,
                'total_students': students_qs.count(),
                'total_tasks': tasks.count(),
                'completed_count': completed_c,
                'not_done_count': not_done_c,
                'overdue_count': overdue_c,
            }

    if query:
        students_qs = students_qs.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query)
        )

    students = list(students_qs.order_by('classroom__grade_level', 'classroom__name', 'last_name'))

    # Har bir o'quvchining shaxsiy vazifalar ko'rsatkichlari (qildi, qilmadi, kech qoldi)
    for st in students:
        st_tasks = StudentAssignment.objects.filter(student=st)
        st.total_tasks_count = st_tasks.count()
        st.done_count = st_tasks.filter(status__in=['completed', 'approved', 'submitted', 'under_review']).count()
        st.not_done_count = st_tasks.filter(status='not_started', assignment__due_date__gte=now).count()
        st.overdue_count = st_tasks.filter(Q(status='overdue') | Q(status='not_started', assignment__due_date__lt=now)).count()

    classrooms = Classroom.objects.filter(is_active=True).order_by('grade_level', 'name')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            form = StudentAdminForm(request.POST)
            if form.is_valid():
                phone = form.cleaned_data['phone_number']
                fn = form.cleaned_data['first_name']
                ln = form.cleaned_data['last_name']
                cls_obj = form.cleaned_data['classroom']

                # Create user with a generated 6-digit password
                gen_pass = f"{random.randint(100000, 999999)}"
                import re
                username = f"std_{re.sub(r'[^0-9]', '', phone)[-9:]}"
                user = User.objects.create_user(username=username, first_name=fn, last_name=ln)
                user.set_password(gen_pass)
                user.save()

                student = form.save(commit=False)
                student.user = user
                student.raw_password = gen_pass
                student.save()

                # Sync assignments
                if cls_obj:
                    for ass in cls_obj.assignments.filter(is_active=True):
                        StudentAssignment.objects.get_or_create(assignment=ass, student=student)

                log_action(request, f"O'quvchi qo'shildi: {student.full_name} (parol: {gen_pass})", "StudentProfile", student.id)
                messages.success(request, f"O'quvchi {student.full_name} qo'shildi! Biriktirilgan parol: {gen_pass}")
                return redirect('admin_students')
            else:
                messages.error(request, "Xatolik! Telefon raqami band bo'lishi mumkin.")
        elif action == 'reset_password':
            sid = request.POST.get('student_id')
            st = get_object_or_404(StudentProfile, id=sid)
            new_pass = f"{random.randint(100000, 999999)}"
            st.user.set_password(new_pass)
            st.user.save()
            st.raw_password = new_pass
            st.save()
            log_action(request, f"O'quvchi paroli qayta tiklandi: {st.full_name} ({new_pass})", "StudentProfile", st.id)
            messages.success(request, f"{st.full_name} uchun yangi parol: {new_pass}")
            return redirect('admin_students')
        elif action == 'toggle_status':
            sid = request.POST.get('student_id')
            st = get_object_or_404(StudentProfile, id=sid)
            st.is_active = not st.is_active
            st.save()
            log_action(request, f"O'quvchi faolligi o'zgartirildi: {st.full_name} ({st.is_active})", "StudentProfile", st.id)
            messages.info(request, f"{st.full_name} holati o'zgartirildi.")
            return redirect('admin_students')

    form = StudentAdminForm()
    return render(request, 'admin_panel/students.html', {
        'students': students,
        'classrooms': classrooms,
        'selected_class': class_id,
        'selected_classroom': selected_classroom,
        'class_metrics': class_metrics,
        'search_query': query,
        'form': form
    })


@admin_required
def student_excel_import_view(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        result = import_students_from_excel(file)
        succ = result['success_count']
        upd = result['updated_count']
        errs = result['errors']

        log_action(request, f"O'quvchilar Excel orqali import qilindi: {succ} yangi, {upd} yangilandi", "StudentProfile")
        if succ or upd:
            messages.success(request, f"Excel import muvaffaqiyatli! {succ} ta yangi o'quvchi qo'shildi, {upd} ta o'quvchi yangilandi.")
        if errs:
            messages.warning(request, f"Ba'zi qatorlarda xatolik: {', '.join(errs[:3])}")
    else:
        messages.error(request, "Excel fayli tanlanmadi!")

    return redirect('admin_students')


@admin_required
def assignments_view(request):
    """
    Uy vazifalari bo'limi:
    - Administrator ham, o'qituvchi ham yangi vazifa yuklashi va boshqarishi mumkin.
    - Vazifa biriktirilgan sinfning barcha o'quvchilariga avtomatik yuboriladi.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            form = AssignmentForm(request.POST, request.FILES)
            if form.is_valid():
                ass = form.save(commit=False)
                ass.created_by = request.user
                ass.save()
                form.save_m2m()  # Saves classrooms

                # Automatically enroll all active students of selected classrooms
                enrolled_count = 0
                for cls_obj in ass.classrooms.all():
                    for st in cls_obj.students.filter(is_active=True):
                        StudentAssignment.objects.get_or_create(assignment=ass, student=st)
                        enrolled_count += 1

                log_action(request, f"Yangi uy vazifasi yaratildi: {ass.title}", "Assignment", ass.id)
                messages.success(request, f"'{ass.title}' vazifasi muvaffaqiyatli yaratildi va {enrolled_count} ta o'quvchiga biriktirildi!")
                return redirect('admin_assignments')
            else:
                messages.error(request, f"Formada xatoliklar mavjud: {form.errors}")
        elif action == 'delete':
            ass_id = request.POST.get('assignment_id')
            ass = get_object_or_404(Assignment, id=ass_id)
            title = ass.title
            ass.delete()
            log_action(request, f"Vazifa o'chirildi: {title}", "Assignment", ass_id)
            messages.success(request, f"'{title}' vazifasi o'chirildi.")
            return redirect('admin_assignments')

    assignments = Assignment.objects.select_related('subject', 'created_by').prefetch_related('classrooms').order_by('-due_date')
    subjects = Subject.objects.filter(is_active=True).order_by('name')
    classrooms = Classroom.objects.filter(is_active=True).order_by('grade_level', 'name')
    form = AssignmentForm()

    return render(request, 'admin_panel/assignments.html', {
        'assignments': assignments,
        'subjects': subjects,
        'classrooms': classrooms,
        'form': form,
        'is_read_only': False,
    })


@admin_required
def submissions_view(request):
    class_id = request.GET.get('classroom_id')
    status_filter = request.GET.get('status')
    subject_id = request.GET.get('subject_id')
    query = request.GET.get('q', '').strip()

    qs = StudentAssignment.objects.select_related(
        'student', 'student__classroom', 'assignment', 'assignment__subject', 'submission'
    ).prefetch_related('submission__attachments').order_by('-updated_at')

    if class_id:
        qs = qs.filter(student__classroom_id=class_id)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if subject_id:
        qs = qs.filter(assignment__subject_id=subject_id)
    if query:
        qs = qs.filter(
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(assignment__title__icontains=query)
        )

    classrooms = Classroom.objects.filter(is_active=True)
    subjects = Subject.objects.filter(is_active=True)

    return render(request, 'admin_panel/submissions.html', {
        'submissions': qs[:100],
        'classrooms': classrooms,
        'subjects': subjects,
        'selected_class': class_id,
        'selected_status': status_filter,
        'selected_subject': subject_id,
        'search_query': query,
        'is_read_only': is_admin_user(request.user),
    })


@admin_required
def review_submission_view(request, task_id):
    """
    Topshiriqni tekshirish oynasi:
    - O'qituvchi yoki administrator javobni ko'rib baholaydi, status belgilaydi va izoh yozadi.
    """
    task = get_object_or_404(
        StudentAssignment.objects.select_related('student', 'student__classroom', 'assignment', 'assignment__subject'),
        id=task_id
    )
    submission, _ = Submission.objects.get_or_create(student_assignment=task)
    attachments = submission.attachments.all()
    history = task.history.all()

    if request.method == 'POST':
        new_status = request.POST.get('status')
        feedback = request.POST.get('teacher_feedback', '').strip()

        old_status = task.status
        task.status = new_status
        task.save()

        submission.review_status = 'approved' if new_status == 'approved' else ('needs_work' if new_status == 'needs_work' else 'under_review')
        submission.teacher_feedback = feedback
        submission.reviewed_at = timezone.now()
        submission.reviewed_by = request.user
        submission.save()

        # Log history
        SubmissionHistory.objects.create(
            student_assignment=task,
            action=f"Tekshirildi va baholandi: {task.get_status_display()}",
            changed_by=request.user,
            old_status=old_status,
            new_status=new_status,
            notes=feedback
        )

        log_action(
            request,
            f"Vazifa tekshirildi: {task.student.full_name} -> {task.assignment.title} ({new_status})",
            "StudentAssignment",
            task.id,
            details=feedback
        )
        messages.success(request, f"{task.student.full_name}ning vazifasi baholandi!")
        return redirect('admin_submissions')

    return render(request, 'admin_panel/review_detail.html', {
        'task': task,
        'submission': submission,
        'attachments': attachments,
        'history': history,
        'is_read_only': False,
    })


@admin_required
def audit_logs_view(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:200]
    return render(request, 'admin_panel/audit_logs.html', {'logs': logs})
