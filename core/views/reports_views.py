from django.shortcuts import render
from django.http import JsonResponse
from core.models import Classroom, StudentProfile, Subject, StudentAssignment
from core.permissions import admin_required


@admin_required
def reports_view(request):
    report_type = request.GET.get('report_type', 'all')
    classroom_id = request.GET.get('classroom_id')
    student_id = request.GET.get('student_id')
    subject_id = request.GET.get('subject_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status_filter = request.GET.get('status')

    classrooms = Classroom.objects.filter(is_active=True)
    subjects = Subject.objects.filter(is_active=True)
    students = StudentProfile.objects.filter(is_active=True)
    if classroom_id:
        students = students.filter(classroom_id=classroom_id)

    # Base query for preview
    qs = StudentAssignment.objects.select_related(
        'student', 'student__classroom', 'assignment', 'assignment__subject', 'submission'
    )

    if report_type == 'single_class' and classroom_id:
        qs = qs.filter(student__classroom_id=classroom_id)
    elif report_type == 'single_student' and student_id:
        qs = qs.filter(student_id=student_id)
    elif classroom_id:
        qs = qs.filter(student__classroom_id=classroom_id)

    if subject_id:
        qs = qs.filter(assignment__subject_id=subject_id)
    if start_date:
        qs = qs.filter(assignment__assigned_date__gte=start_date)
    if end_date:
        qs = qs.filter(assignment__assigned_date__lte=end_date)
    if status_filter and status_filter != 'all':
        qs = qs.filter(status=status_filter)

    records = list(qs.order_by('student__classroom__name', 'student__last_name', '-assignment__due_date'))

    total_records = len(records)
    distinct_students = len({r.student_id for r in records})
    completed_count = sum(1 for r in records if r.status in ['completed', 'approved'])
    not_completed_count = sum(1 for r in records if r.status in ['not_started', 'overdue'])
    pct = (completed_count / total_records * 100) if total_records > 0 else 0

    context = {
        'classrooms': classrooms,
        'subjects': subjects,
        'students': students,
        'report_type': report_type,
        'classroom_id': classroom_id,
        'student_id': student_id,
        'subject_id': subject_id,
        'start_date': start_date,
        'end_date': end_date,
        'status_filter': status_filter,
        # Summary preview cards
        'total_records': total_records,
        'distinct_students': distinct_students,
        'completed_count': completed_count,
        'not_completed_count': not_completed_count,
        'completion_rate': f"{pct:.1f}%",
        'preview_records': records[:50], # first 50 preview
    }
    return render(request, 'admin_panel/reports.html', context)


@admin_required
def get_students_by_class(request):
    """AJAX endpoint for dynamic student dropdown in reports"""
    class_id = request.GET.get('classroom_id')
    if not class_id:
        students = StudentProfile.objects.filter(is_active=True).values('id', 'first_name', 'last_name')
    else:
        students = StudentProfile.objects.filter(classroom_id=class_id, is_active=True).values('id', 'first_name', 'last_name')
    
    data = [{'id': s['id'], 'name': f"{s['first_name']} {s['last_name']}"} for s in students]
    return JsonResponse({'students': data})
