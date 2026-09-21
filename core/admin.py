from django.contrib import admin
from core.models import (
    AdminProfile, Classroom, Subject, StudentProfile,
    Assignment, AssignmentAttachment, StudentAssignment,
    Submission, SubmissionAttachment, SubmissionHistory,
    ProfileChangeRequest, AuditLog, PhoneVerificationOTP
)


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'role', 'created_at')


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade_level', 'academic_year', 'student_count', 'is_active')
    list_filter = ('grade_level', 'is_active')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'classroom', 'phone_number', 'is_active', 'last_active')
    list_filter = ('classroom', 'is_active')
    search_fields = ('first_name', 'last_name', 'phone_number')


class AssignmentAttachmentInline(admin.TabularInline):
    model = AssignmentAttachment
    extra = 1


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'assigned_date', 'due_date', 'is_active', 'created_by')
    list_filter = ('subject', 'classrooms', 'is_active')
    inlines = [AssignmentAttachmentInline]


class SubmissionAttachmentInline(admin.TabularInline):
    model = SubmissionAttachment
    extra = 0


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student_assignment', 'review_status', 'submitted_at', 'reviewed_by')
    inlines = [SubmissionAttachmentInline]


@admin.register(StudentAssignment)
class StudentAssignmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'status', 'marked_done_at', 'completed_without_files')
    list_filter = ('status', 'assignment__subject', 'student__classroom')


@admin.register(SubmissionHistory)
class SubmissionHistoryAdmin(admin.ModelAdmin):
    list_display = ('student_assignment', 'action', 'old_status', 'new_status', 'timestamp')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'target_model', 'target_id', 'ip_address', 'timestamp')
    list_filter = ('action', 'target_model')
    search_fields = ('action', 'details')


@admin.register(PhoneVerificationOTP)
class PhoneVerificationOTPAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'otp_code', 'is_used', 'attempts', 'expires_at')
