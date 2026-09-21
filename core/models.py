import os
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    full_name = models.CharField(max_length=200, verbose_name="F.I.O")
    phone_number = models.CharField(max_length=20, verbose_name="Telefon raqami", blank=True)
    role = models.CharField(max_length=100, default="O'qituvchi / Administrator", verbose_name="Lavozimi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    class Meta:
        verbose_name = "Administrator profili"
        verbose_name_plural = "Administrator profillari"


class Classroom(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Sinf nomi (masalan: 1-A)")
    grade_level = models.PositiveSmallIntegerField(default=1, verbose_name="Sinf bosqichi (1-11)")
    academic_year = models.CharField(max_length=20, default="2025-2026", verbose_name="O'quv yili")
    is_active = models.BooleanField(default=True, verbose_name="Faol holatda")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    def __str__(self):
        return self.name

    @property
    def student_count(self):
        return self.students.filter(is_active=True).count()

    class Meta:
        ordering = ['grade_level', 'name']
        verbose_name = "Sinf"
        verbose_name_plural = "Sinflar"


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Fan nomi")
    code = models.CharField(max_length=30, blank=True, verbose_name="Fan kodi")
    icon = models.CharField(max_length=50, default="book-open", verbose_name="Lucide icon nomi")
    is_active = models.BooleanField(default=True, verbose_name="Faol holatda")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Fan"
        verbose_name_plural = "Fanlar"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    first_name = models.CharField(max_length=100, verbose_name="Ismi")
    last_name = models.CharField(max_length=100, verbose_name="Familiyasi")
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="Sinfi")
    phone_number = models.CharField(max_length=20, unique=True, verbose_name="Telefon raqami")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Profil rasmi")
    is_active = models.BooleanField(default=True, verbose_name="Faol holatda")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ro'yxatdan o'tgan sana")
    last_active = models.DateTimeField(null=True, blank=True, verbose_name="Oxirgi faollik")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.classroom.name if self.classroom else 'Sinf tanlanmagan'})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['classroom__grade_level', 'classroom__name', 'last_name', 'first_name']
        verbose_name = "O'quvchi profili"
        verbose_name_plural = "O'quvchilar profillari"


class Assignment(models.Model):
    title = models.CharField(max_length=255, verbose_name="Vazifa nomi")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments', verbose_name="Fan")
    classrooms = models.ManyToManyField(Classroom, related_name='assignments', verbose_name="Biriktirilgan sinflar")
    description = models.TextField(blank=True, verbose_name="Vazifa tavsifi")
    content = models.TextField(blank=True, verbose_name="Vazifa to'liq matni")
    attachment = models.FileField(upload_to='assignments/', blank=True, null=True, verbose_name="Asosiy fayl (ixtiyoriy)")
    video_url = models.URLField(blank=True, verbose_name="Video havola (YouTube / video link)")
    assigned_date = models.DateField(default=timezone.now, verbose_name="Berilgan sana")
    start_time = models.TimeField(null=True, blank=True, verbose_name="Boshlanish vaqti")
    due_date = models.DateTimeField(verbose_name="Topshirish muddati")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_assignments', verbose_name="Yaratgan o'qituvchi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    def __str__(self):
        return f"{self.title} - {self.subject.name}"

    @property
    def is_overdue(self):
        return timezone.now() > self.due_date

    class Meta:
        ordering = ['-due_date', '-created_at']
        verbose_name = "Uy vazifasi"
        verbose_name_plural = "Uy vazifalari"


class AssignmentAttachment(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='assignments/attachments/')
    file_name = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=50, default="document")  # image, video, document, other
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.file_name and self.file:
            self.file_name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.file_name or f"Attachment #{self.id}"


class StudentAssignment(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Bajarilmagan'),
        ('completed', 'Bajarildi'),
        ('submitted', 'Javob yuborildi'),
        ('under_review', 'Tekshirilmoqda'),
        ('approved', 'Qabul qilindi'),
        ('needs_work', 'Qayta ishlash kerak'),
        ('overdue', 'Muddati o‘tgan'),
    ]

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='student_assignments')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='assigned_tasks')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='not_started', verbose_name="Holat")
    marked_done_at = models.DateTimeField(null=True, blank=True, verbose_name="Bajarilgan vaqt")
    completed_without_files = models.BooleanField(default=False, verbose_name="Faylsiz bajarildi deb belgilangan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-assignment__due_date']
        verbose_name = "O'quvchi topshirig'i"
        verbose_name_plural = "O'quvchilar topshiriqlari"

    def __str__(self):
        return f"{self.student.full_name} -> {self.assignment.title} ({self.get_status_display()})"

    @property
    def current_status(self):
        # Auto-compute overdue if past due_date and not completed/submitted/approved
        if self.status in ['not_started'] and self.assignment.is_overdue:
            return 'overdue'
        return self.status

    @property
    def badge_color(self):
        mapping = {
            'not_started': 'bg-gray-100 text-gray-800 border-gray-300 dark:bg-gray-700 dark:text-gray-300',
            'completed': 'bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-900/40 dark:text-emerald-300',
            'submitted': 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900/40 dark:text-blue-300',
            'under_review': 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-900/40 dark:text-amber-300',
            'approved': 'bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-900/40 dark:text-emerald-300',
            'needs_work': 'bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-900/40 dark:text-rose-300',
            'overdue': 'bg-red-100 text-red-800 border-red-300 dark:bg-red-900/40 dark:text-red-300',
        }
        return mapping.get(self.current_status, 'bg-gray-100 text-gray-800')


class Submission(models.Model):
    REVIEW_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('under_review', 'Tekshirilmoqda'),
        ('approved', 'Qabul qilindi'),
        ('needs_work', 'Qayta ishlash kerak'),
    ]

    student_assignment = models.OneToOneField(StudentAssignment, on_delete=models.CASCADE, related_name='submission')
    submission_text = models.TextField(blank=True, verbose_name="O'quvchi matnli javobi")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan sana va vaqt")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan vaqt")
    review_status = models.CharField(max_length=30, choices=REVIEW_CHOICES, default='pending', verbose_name="O'qituvchi xulosasi")
    teacher_feedback = models.TextField(blank=True, verbose_name="O'qituvchi izohi")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Tekshirilgan sana")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions', verbose_name="Tekshirgan o'qituvchi")

    def __str__(self):
        return f"Javob: {self.student_assignment}"

    class Meta:
        verbose_name = "Yuborilgan topshiriq javobi"
        verbose_name_plural = "Yuborilgan topshiriq javoblari"


class SubmissionAttachment(models.Model):
    TYPE_CHOICES = [
        ('image', 'Rasm'),
        ('video', 'Video'),
        ('document', 'Hujjat (PDF/Word)'),
        ('other', 'Boshqa'),
    ]

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='submissions/files/')
    file_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='image')
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(default=0, help_text="Baytlarda")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.file_name and self.file:
            self.file_name = os.path.basename(self.file.name)
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    @property
    def size_display(self):
        kb = self.file_size / 1024
        if kb < 1024:
            return f"{kb:.1f} KB"
        mb = kb / 1024
        return f"{mb:.2f} MB"

    def __str__(self):
        return self.file_name or f"File #{self.id}"

    class Meta:
        verbose_name = "Topshiriq fayli"
        verbose_name_plural = "Topshiriq fayllari"


class SubmissionHistory(models.Model):
    student_assignment = models.ForeignKey(StudentAssignment, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=255, verbose_name="Harakat nomi")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="O'zgartiruvchi")
    old_status = models.CharField(max_length=50, blank=True)
    new_status = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True, verbose_name="Qo'shimcha izoh")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Vaqti")

    def __str__(self):
        return f"{self.action} ({self.timestamp:%Y-%m-%d %H:%M})"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Topshiriq tarixi"
        verbose_name_plural = "Topshiriqlar tarixi"


class ProfileChangeRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('approved', 'Tasdiqlandi'),
        ('rejected', 'Rad etildi'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='change_requests')
    requested_first_name = models.CharField(max_length=100, blank=True, verbose_name="Yangi ism")
    requested_last_name = models.CharField(max_length=100, blank=True, verbose_name="Yangi familiya")
    requested_classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Yangi sinf")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"O'zgartirish so'rovi: {self.student.full_name}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Profil o'zgartirish so'rovi"
        verbose_name_plural = "Profil o'zgartirish so'rovlari"


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Foydalanuvchi")
    action = models.CharField(max_length=255, verbose_name="Amal")
    target_model = models.CharField(max_length=100, blank=True, verbose_name="Obyekt modeli")
    target_id = models.CharField(max_length=100, blank=True, verbose_name="Obyekt ID")
    details = models.TextField(blank=True, verbose_name="Batafsil ma'lumot")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP manzil")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Vaqti")

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.user}: {self.action}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Audit jurnali"
        verbose_name_plural = "Audit jurnallari"


class PhoneVerificationOTP(models.Model):
    phone_number = models.CharField(max_length=20, db_index=True, verbose_name="Telefon raqami")
    otp_code = models.CharField(max_length=6, verbose_name="OTP kodi")
    is_used = models.BooleanField(default=False, verbose_name="Ishlatilgan")
    attempts = models.PositiveSmallIntegerField(default=0, verbose_name="Urinishlar soni")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at and self.attempts < 5

    def __str__(self):
        return f"{self.phone_number} -> {self.otp_code} ({'Ishlatilgan' if self.is_used else 'Faol'})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Telefon OTP kodi"
        verbose_name_plural = "Telefon OTP kodlari"
