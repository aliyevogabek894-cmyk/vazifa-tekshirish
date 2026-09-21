import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.http import JsonResponse

from core.models import (
    Classroom, StudentProfile, Assignment, Subject,
    StudentAssignment, Submission, SubmissionAttachment, SubmissionHistory, AuditLog
)
from core.forms import AssignmentForm, StudentAdminForm, ClassroomForm, SubjectForm
from core.permissions import admin_required
from core.utils.audit import log_action
from core.utils.excel_importer import import_students_from_excel


@admin_required
def admin_dashboard(request):
    total_classrooms = Classroom.objects.filter(is_active=True).count()
    total_students = StudentProfile.objects.filter(is_active=True).count()
    total_assignments = Assignment.objects.filter(is_active=True).count()

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

    # Chart 2: Completion rate by classroom
    class_labels = []
    class_completion_rates = []
    for c in Classroom.objects.filter(is_active=True)[:8]:
        c_tasks = StudentAssignment.objects.filter(student__classroom=c)
        c_total = c_tasks.count()
        c_done = c_tasks.filter(status__in=['completed', 'approved']).count()
        rate = round((c_done / c_total * 100), 1) if c_total > 0 else 0
        class_labels.append(c.name)
        class_completion_rates.append(rate)

    context = {
        'total_classrooms': total_classrooms,
        'total_students': total_students,
        'total_assignments': total_assignments,
        'completed_count': completed_count,
        'not_started_count': not_started_count,
        'pending_review_count': pending_review_count,
        'approved_count': approved_count,
        'recent_submissions': recent_submissions,
        'status_chart_json': json.dumps(status_chart_data),
        'class_chart_labels_json': json.dumps(class_labels),
        'class_chart_data_json': json.dumps(class_completion_rates),
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def classrooms_view(request):
    classrooms = Classroom.objects.annotate(
        students_total=Count('students', filter=Q(students__is_active=True))
    ).order_by('grade_level', 'name')

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
    return render(request, 'admin_panel/classrooms.html', {'classrooms': classrooms, 'form': form})


@admin_required
def students_view(request):
    query = request.GET.get('q', '').strip()
    class_id = request.GET.get('classroom_id')

    students_qs = StudentProfile.objects.select_related('classroom', 'user')

    if class_id:
        students_qs = students_qs.filter(classroom_id=class_id)
    if query:
        students_qs = students_qs.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query)
        )

    students = students_qs.order_by('classroom__grade_level', 'classroom__name', 'last_name')
    classrooms = Classroom.objects.filter(is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            form = StudentAdminForm(request.POST)
            if form.is_valid():
                from django.contrib.auth.models import User
                phone = form.cleaned_data['phone_number']
                fn = form.cleaned_data['first_name']
                ln = form.cleaned_data['last_name']
                cls_obj = form.cleaned_data['classroom']

                # Create user
                import re
                username = f"std_{re.sub(r'[^0-9]', '', phone)[-9:]}"
                user = User.objects.create_user(username=username, first_name=fn, last_name=ln)
                user.set_unusable_password()
                user.save()

                student = form.save(commit=False)
                student.user = user
                student.save()

                # Sync assignments
                if cls_obj:
                    for ass in cls_obj.assignments.filter(is_active=True):
                        StudentAssignment.objects.get_or_create(assignment=ass, student=student)

                log_action(request, f"O'quvchi qo'shildi: {student.full_name}", "StudentProfile", student.id)
                messages.success(request, f"O'quvchi {student.full_name} muvaffaqiyatli qo'shildi!")
                return redirect('admin_students')
            else:
                messages.error(request, "Xatolik! Telefon raqami band bo'lishi mumkin.")
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
    assignments = Assignment.objects.select_related('subject', 'created_by').prefetch_related('classrooms').order_by('-due_date')
    subjects = Subject.objects.filter(is_active=True)
    classrooms = Classroom.objects.filter(is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            form = AssignmentForm(request.POST, request.FILES)
            if form.is_valid():
                ass = form.save(commit=False)
                ass.created_by = request.user
                ass.save()
                form.save_m2m() # Saves classrooms

                # Automatically enroll all active students of selected classrooms
                for cls_obj in ass.classrooms.all():
                    for st in cls_obj.students.filter(is_active=True):
                        StudentAssignment.objects.get_or_create(assignment=ass, student=st)

                log_action(request, f"Yangi uy vazifasi yaratildi: {ass.title}", "Assignment", ass.id)
                messages.success(request, f"'{ass.title}' vazifasi muvaffaqiyatli yaratildi va o'quvchilarga biriktirildi!")
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

    form = AssignmentForm()
    return render(request, 'admin_panel/assignments.html', {
        'assignments': assignments,
        'subjects': subjects,
        'classrooms': classrooms,
        'form': form
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
    })


@admin_required
def review_submission_view(request, task_id):
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
            action=f"O'qituvchi tekshirdi va baholadi: {task.get_status_display()}",
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
    })


@admin_required
def audit_logs_view(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:200]
    return render(request, 'admin_panel/audit_logs.html', {'logs': logs})
