import mimetypes
import os
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponseForbidden, Http404
from django.contrib.auth.decorators import login_required
from core.models import SubmissionAttachment, Assignment, AssignmentAttachment
from core.permissions import verify_student_owns_attachment


@login_required
def secure_submission_media_view(request, attachment_id):
    """
    Securely serves submission attachments (photos, videos, documents).
    Strictly verifies that ONLY the student owner or staff can access.
    Other students will get 403 Forbidden.
    """
    attachment = get_object_or_404(
        SubmissionAttachment.objects.select_related('submission__student_assignment__student'),
        id=attachment_id
    )

    if not verify_student_owns_attachment(request.user, attachment):
        return HttpResponseForbidden("Kechirasiz, ushbu fayl maxfiy va unga kirish huquqiga ega emassiz!")

    if not attachment.file or not os.path.exists(attachment.file.path):
        raise Http404("Fayl topilmadi.")

    content_type, _ = mimetypes.guess_type(attachment.file.path)
    content_type = content_type or 'application/octet-stream'

    response = FileResponse(open(attachment.file.path, 'rb'), content_type=content_type)
    # Inline viewing for images and videos, attachment download for others
    if attachment.file_type in ['image', 'video']:
        response['Content-Disposition'] = f'inline; filename="{attachment.file_name}"'
    else:
        response['Content-Disposition'] = f'attachment; filename="{attachment.file_name}"'
    return response


@login_required
def secure_assignment_media_view(request, assignment_id):
    """
    Serves assignment primary attachments.
    Only students whose classroom has this assignment or staff can access.
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if not (request.user.is_staff or request.user.is_superuser):
        if not hasattr(request.user, 'student_profile'):
            return HttpResponseForbidden("Kirish taqiqlangan.")
        student = request.user.student_profile
        if not assignment.classrooms.filter(id=student.classroom_id).exists():
            return HttpResponseForbidden("Ushbu vazifa sizning sinfingizga tegishli emas!")

    if not assignment.attachment or not os.path.exists(assignment.attachment.path):
        raise Http404("Fayl topilmadi.")

    content_type, _ = mimetypes.guess_type(assignment.attachment.path)
    content_type = content_type or 'application/octet-stream'

    response = FileResponse(open(assignment.attachment.path, 'rb'), content_type=content_type)
    filename = os.path.basename(assignment.attachment.name)
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
