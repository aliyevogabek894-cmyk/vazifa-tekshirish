import mimetypes
import os
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponseForbidden, Http404
from django.contrib.auth.decorators import login_required
from core.models import SubmissionAttachment, Assignment
from core.permissions import verify_student_owns_attachment


@login_required
def secure_submission_media_view(request, attachment_id):
    """
    Securely serves submission attachments (photos, videos, documents).
    Strictly verifies that ONLY the student owner, teachers, or administrators can access.
    """
    attachment = get_object_or_404(
        SubmissionAttachment.objects.select_related('submission__student_assignment__student'),
        id=attachment_id
    )

    if not verify_student_owns_attachment(request.user, attachment):
        return HttpResponseForbidden("Kechirasiz, ushbu fayl maxfiy va unga kirish huquqiga ega emassiz!")

    if not attachment.file:
        raise Http404("Fayl topilmadi.")

    file_obj = None
    try:
        file_obj = attachment.file.open('rb')
    except Exception:
        try:
            if hasattr(attachment.file, 'path') and os.path.exists(attachment.file.path):
                file_obj = open(attachment.file.path, 'rb')
            else:
                raise Http404("Fayl topilmadi.")
        except Exception:
            raise Http404("Fayl topilmadi.")

    file_name = attachment.file_name or os.path.basename(attachment.file.name)
    content_type, _ = mimetypes.guess_type(file_name)

    ext = os.path.splitext(file_name)[1].lower()
    if not content_type:
        if ext in ['.jpg', '.jpeg', '.jfif']:
            content_type = 'image/jpeg'
        elif ext in ['.png']:
            content_type = 'image/png'
        elif ext in ['.webp']:
            content_type = 'image/webp'
        elif ext in ['.heic', '.heif']:
            content_type = 'image/heic'
        elif ext in ['.mp4']:
            content_type = 'video/mp4'
        elif ext in ['.pdf']:
            content_type = 'application/pdf'
        elif attachment.file_type == 'image':
            content_type = 'image/jpeg'
        else:
            content_type = 'application/octet-stream'

    response = FileResponse(file_obj, content_type=content_type)
    is_media = (
        attachment.file_type in ['image', 'video'] or 
        (content_type and (content_type.startswith('image/') or content_type.startswith('video/')))
    )
    # ASCII-safe filename for Content-Disposition header
    safe_file_name = file_name.encode('ascii', 'ignore').decode('ascii') or f"file_{attachment.id}.jpg"
    if is_media:
        response['Content-Disposition'] = f'inline; filename="{safe_file_name}"'
    else:
        response['Content-Disposition'] = f'attachment; filename="{safe_file_name}"'
    response['Cache-Control'] = 'private, max-age=3600'
    return response


@login_required
def secure_assignment_media_view(request, assignment_id):
    """
    Serves assignment primary attachments.
    Only students whose classroom has this assignment or staff/teachers can access.
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if not (request.user.is_staff or request.user.is_superuser or hasattr(request.user, 'admin_profile')):
        if not hasattr(request.user, 'student_profile'):
            return HttpResponseForbidden("Kirish taqiqlangan.")
        student = request.user.student_profile
        if not assignment.classrooms.filter(id=student.classroom_id).exists():
            return HttpResponseForbidden("Ushbu vazifa sizning sinfingizga tegishli emas!")

    if not assignment.attachment:
        raise Http404("Fayl topilmadi.")

    file_obj = None
    try:
        file_obj = assignment.attachment.open('rb')
    except Exception:
        try:
            if hasattr(assignment.attachment, 'path') and os.path.exists(assignment.attachment.path):
                file_obj = open(assignment.attachment.path, 'rb')
            else:
                raise Http404("Fayl topilmadi.")
        except Exception:
            raise Http404("Fayl topilmadi.")

    filename = os.path.basename(assignment.attachment.name)
    content_type, _ = mimetypes.guess_type(filename)
    content_type = content_type or 'application/octet-stream'

    response = FileResponse(file_obj, content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
