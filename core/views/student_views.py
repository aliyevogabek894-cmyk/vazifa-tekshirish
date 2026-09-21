import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.http import Http404

from core.models import (
    StudentProfile, StudentAssignment, Assignment,
    Submission, SubmissionAttachment, SubmissionHistory, ProfileChangeRequest, Classroom
)
from core.permissions import student_required, verify_student_owns_assignment
from core.utils.audit import log_action


@student_required
def student_dashboard(request):
    student = request.user.student_profile

    # Auto sync any active assignments for this student's classroom
    if student.classroom:
        classroom_assignments = Assignment.objects.filter(classrooms=student.classroom, is_active=True)
        for ass in classroom_assignments:
            StudentAssignment.objects.get_or_create(assignment=ass, student=student)

    # Base tasks queryset - strictly limited to CURRENT student only!
    tasks_qs = StudentAssignment.objects.filter(student=student).select_related(
        'assignment', 'assignment__subject', 'submission'
    ).order_by('-assignment__due_date')

    # Metrics calculation
    all_tasks = list(tasks_qs)
    total_count = len(all_tasks)
    completed_count = sum(1 for t in all_tasks if t.current_status in ['completed', 'approved'])
    under_review_count = sum(1 for t in all_tasks if t.current_status in ['submitted', 'under_review'])
    approved_count = sum(1 for t in all_tasks if t.current_status == 'approved')
    overdue_count = sum(1 for t in all_tasks if t.current_status == 'overdue')
    not_started_count = sum(1 for t in all_tasks if t.current_status == 'not_started')

    # Filter tab
    tab = request.GET.get('tab', 'all')
    if tab == 'pending':
        tasks = [t for t in all_tasks if t.current_status in ['not_started', 'needs_work']]
    elif tab == 'completed':
        tasks = [t for t in all_tasks if t.current_status in ['completed', 'approved']]
    elif tab == 'submitted':
        tasks = [t for t in all_tasks if t.current_status in ['submitted', 'under_review']]
    elif tab == 'overdue':
        tasks = [t for t in all_tasks if t.current_status == 'overdue']
    else:
        tasks = all_tasks

    # Calculate aggregate classroom progress for each assignment (anonymized!)
    tasks_with_stats = []
    total_class_students = student.classroom.students.filter(is_active=True).count() if student.classroom else 1

    for t in tasks:
        # Count how many students in the same class completed this assignment
        class_completed_count = StudentAssignment.objects.filter(
            assignment=t.assignment,
            student__classroom=student.classroom,
            status__in=['completed', 'submitted', 'under_review', 'approved']
        ).count()

        tasks_with_stats.append({
            'item': t,
            'class_completed_count': class_completed_count,
            'total_class_students': total_class_students,
            'class_percentage': int((class_completed_count / total_class_students) * 100) if total_class_students > 0 else 0
        })

    context = {
        'student': student,
        'tasks_with_stats': tasks_with_stats,
        'tab': tab,
        'total_count': total_count,
        'completed_count': completed_count,
        'under_review_count': under_review_count,
        'approved_count': approved_count,
        'overdue_count': overdue_count,
        'not_started_count': not_started_count,
    }
    return render(request, 'student/dashboard.html', context)


@student_required
def student_assignment_detail(request, task_id):
    student = request.user.student_profile
    # Strictly fetch task for this student to prevent IDOR
    task = get_object_or_404(
        StudentAssignment.objects.select_related('assignment', 'assignment__subject'),
        id=task_id,
        student=student
    )

    submission, _ = Submission.objects.get_or_create(student_assignment=task)
    attachments = submission.attachments.all()
    history = task.history.all()

    if request.method == 'POST':
        action_type = request.POST.get('action_type', '')

        # Action 1: Quick "Vazifani bajardim" toggle
        if action_type == 'mark_done':
            task.status = 'completed'
            task.marked_done_at = timezone.now()
            task.completed_without_files = True
            task.save()

            SubmissionHistory.objects.create(
                student_assignment=task,
                action="O'quvchi vazifani bajardi deb belgiladi (faylsiz)",
                changed_by=request.user,
                old_status=task.status,
                new_status='completed'
            )
            messages.success(request, "Vazifa 'Bajarildi' deb belgilandi! Agar kerak bo'lsa javob matni yoki fayl ham yuborishingiz mumkin.")
            return redirect('student_assignment_detail', task_id=task.id)

        # Action 2: Submit answer with text and/or files
        elif action_type == 'submit_work':
            submission_text = request.POST.get('submission_text', '').strip()
            files = request.FILES.getlist('files')

            submission.submission_text = submission_text
            submission.submitted_at = timezone.now()
            submission.review_status = 'pending'
            submission.save()

            # Process uploaded files
            allowed_extensions = {
                'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'],
                'video': ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.3gp'],
                'document': ['.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx', '.xls', '.xlsx']
            }

            for uploaded_file in files:
                # Basic size check (50MB max per file)
                if uploaded_file.size > 52428800:
                    messages.error(request, f"{uploaded_file.name} fayli hajmi 50MB dan katta bo'lishi mumkin emas!")
                    continue

                ext = os.path.splitext(uploaded_file.name)[1].lower()
                f_type = 'other'
                for cat, exts in allowed_extensions.items():
                    if ext in exts:
                        f_type = cat
                        break

                SubmissionAttachment.objects.create(
                    submission=submission,
                    file=uploaded_file,
                    file_name=uploaded_file.name,
                    file_type=f_type,
                    file_size=uploaded_file.size
                )

            task.status = 'submitted'
            task.marked_done_at = timezone.now()
            task.completed_without_files = (len(files) == 0 and not attachments.exists())
            task.save()

            SubmissionHistory.objects.create(
                student_assignment=task,
                action=f"O'quvchi topshiriq javobini yubordi ({len(files)} ta yangi fayl)",
                changed_by=request.user,
                old_status=task.status,
                new_status='submitted'
            )
            messages.success(request, "Vazifa javobi muvaffaqiyatli yuborildi! O'qituvchi tez orada tekshiradi.")
            return redirect('student_assignment_detail', task_id=task.id)

    # Class aggregate progress for this task
    total_class_students = student.classroom.students.filter(is_active=True).count() if student.classroom else 1
    class_completed_count = StudentAssignment.objects.filter(
        assignment=task.assignment,
        student__classroom=student.classroom,
        status__in=['completed', 'submitted', 'under_review', 'approved']
    ).count()

    context = {
        'task': task,
        'submission': submission,
        'attachments': attachments,
        'history': history,
        'class_completed_count': class_completed_count,
        'total_class_students': total_class_students,
        'class_percentage': int((class_completed_count / total_class_students) * 100) if total_class_students > 0 else 0
    }
    return render(request, 'student/assignment_detail.html', context)


@student_required
def student_profile_view(request):
    student = request.user.student_profile
    change_requests = student.change_requests.all()

    if request.method == 'POST':
        # Request change in name or classroom
        req_fn = request.POST.get('first_name', '').strip()
        req_ln = request.POST.get('last_name', '').strip()
        class_id = request.POST.get('classroom_id')
        req_class = Classroom.objects.filter(id=class_id).first() if class_id else None

        if req_fn or req_ln or req_class:
            ProfileChangeRequest.objects.create(
                student=student,
                requested_first_name=req_fn or student.first_name,
                requested_last_name=req_ln or student.last_name,
                requested_classroom=req_class or student.classroom
            )
            messages.success(request, "Profilingizni o'zgartirish bo'yicha so'rov adminga yuborildi.")
            return redirect('student_profile')

    classrooms = Classroom.objects.filter(is_active=True)
    return render(request, 'student/profile.html', {
        'student': student,
        'change_requests': change_requests,
        'classrooms': classrooms
    })
