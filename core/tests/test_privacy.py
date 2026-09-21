from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import (
    Classroom, Subject, StudentProfile, Assignment,
    StudentAssignment, Submission, SubmissionAttachment
)


class PrivacyAndPermissionsTest(TestCase):
    def setUp(self):
        self.classroom = Classroom.objects.create(name="1-A", grade_level=1)
        self.subject = Subject.objects.create(name="Matematika", code="MATH")

        # Student A
        self.user_a = User.objects.create_user(username="std_a", first_name="Ali", last_name="Aliyev")
        self.student_a = StudentProfile.objects.create(
            user=self.user_a, first_name="Ali", last_name="Aliyev",
            classroom=self.classroom, phone_number="+998901111111"
        )

        # Student B
        self.user_b = User.objects.create_user(username="std_b", first_name="Vali", last_name="Valiyev")
        self.student_b = StudentProfile.objects.create(
            user=self.user_b, first_name="Vali", last_name="Valiyev",
            classroom=self.classroom, phone_number="+998902222222"
        )

        # Admin
        self.admin_user = User.objects.create_superuser(username="teacher", password="password123")

        # Assignment
        from django.utils import timezone
        from datetime import timedelta
        self.assignment = Assignment.objects.create(
            title="Misollar", subject=self.subject,
            due_date=timezone.now() + timedelta(days=2),
            created_by=self.admin_user
        )
        self.assignment.classrooms.add(self.classroom)

        # Student Assignments
        self.task_a = StudentAssignment.objects.create(assignment=self.assignment, student=self.student_a)
        self.task_b = StudentAssignment.objects.create(assignment=self.assignment, student=self.student_b)

        # Student B submits a private file
        self.sub_b = Submission.objects.create(student_assignment=self.task_b, submission_text="Valining javobi")
        dummy_file = SimpleUploadedFile("uyga_vazifa.jpg", b"fake image bytes", content_type="image/jpeg")
        self.att_b = SubmissionAttachment.objects.create(
            submission=self.sub_b, file=dummy_file, file_name="uyga_vazifa.jpg", file_type="image"
        )

    def test_student_a_cannot_view_student_b_task_detail(self):
        """Student A cannot access Student B's assignment page (IDOR protection)"""
        client = Client()
        client.force_login(self.user_a)

        # Attempt to access Student B's task_id
        url = reverse('student_assignment_detail', kwargs={'task_id': self.task_b.id})
        response = client.get(url)
        # Should return 404 Not Found since task is filtered by student=student_a
        self.assertEqual(response.status_code, 404)

    def test_student_a_cannot_access_student_b_uploaded_media(self):
        """Student A cannot access or download Student B's uploaded file"""
        client = Client()
        client.force_login(self.user_a)

        media_url = reverse('secure_submission_media', kwargs={'attachment_id': self.att_b.id})
        response = client.get(media_url)
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)

    def test_student_b_can_access_their_own_uploaded_media(self):
        """Student B CAN access their own uploaded file"""
        client = Client()
        client.force_login(self.user_b)

        media_url = reverse('secure_submission_media', kwargs={'attachment_id': self.att_b.id})
        response = client.get(media_url)
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_student_uploaded_media(self):
        """Admin/Teacher CAN access student uploaded files for grading"""
        client = Client()
        client.force_login(self.admin_user)

        media_url = reverse('secure_submission_media', kwargs={'attachment_id': self.att_b.id})
        response = client.get(media_url)
        self.assertEqual(response.status_code, 200)
