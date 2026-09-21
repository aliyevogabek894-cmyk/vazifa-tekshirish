from django.http import HttpResponse
from core.permissions import admin_required
from core.utils.excel_exporter import generate_homework_excel_report
from core.utils.audit import log_action


@admin_required
def export_excel_report_view(request):
    """
    Generates and downloads the 6-sheet Excel report.
    Only accessible by Admin / Teacher.
    """
    report_type = request.GET.get('report_type', 'all')
    classroom_id = request.GET.get('classroom_id')
    student_id = request.GET.get('student_id')
    subject_id = request.GET.get('subject_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status_filter = request.GET.get('status')

    # Convert empty strings to None / int
    cid = int(classroom_id) if classroom_id and classroom_id.isdigit() else None
    sid = int(student_id) if student_id and student_id.isdigit() else None
    sub_id = int(subject_id) if subject_id and subject_id.isdigit() else None

    buffer, filename = generate_homework_excel_report(
        report_type=report_type,
        classroom_id=cid,
        student_id=sid,
        subject_id=sub_id,
        start_date=start_date or None,
        end_date=end_date or None,
        status_filter=status_filter or None
    )

    log_action(
        request,
        action=f"Excel hisobot yuklab olindi ({report_type})",
        target_model="Report",
        details=f"Fayl nomi: {filename}"
    )

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
