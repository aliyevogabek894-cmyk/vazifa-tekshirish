from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.models import Classroom, StudentProfile, AdminProfile, Subject, Assignment, StudentAssignment, Submission, SubmissionAttachment


class SchoolClassesAndAssignmentsTests(TestCase):
    def setUp(self):
        self.client = Client()

        # 1. 1-A va 7-Aniq sinflarini yaratamiz
        self.class_1a = Classroom.objects.create(name="1-A", grade_level=1, academic_year="2025-2026")
        self.class_7aniq = Classroom.objects.create(name="7-Aniq", grade_level=7, academic_year="2025-2026")

        # 2. Fanlar
        self.sub_ona_tili = Subject.objects.create(name="Ona tili", code="UZB")
        self.sub_matematika = Subject.objects.create(name="Matematika", code="MATH")

        # 3. Admin user
        self.admin_user = User.objects.create_superuser(
            username='maktab_admini',
            password='AdminPassword123'
        )
        self.admin_profile = AdminProfile.objects.create(
            user=self.admin_user,
            full_name="Maktab Bosh Administratori",
            role='admin'
        )

        # 4. Ustoz (Teacher)
        self.teacher_user = User.objects.create_user(
            username='ustoz_ona_tili',
            password='UstozPassword123',
            is_staff=True
        )
        self.teacher_profile = AdminProfile.objects.create(
            user=self.teacher_user,
            full_name="Nodira Rahimova",
            role='teacher',
            subject=self.sub_ona_tili,
            raw_password='UstozPassword123'
        )
        self.teacher_profile.classrooms.add(self.class_1a)

    def test_student_registration_selects_class_and_receives_tasks(self):
        """O'quvchi ro'yxatdan o'tganda 1-A sinfini tanlaydi va o'sha sinfdagi faol vazifalar unga birikadi"""
        # Avval 1-A sinfiga vazifa yaratamiz
        due = timezone.now() + timedelta(days=2)
        ass1 = Assignment.objects.create(
            title="Husnixat mashqi",
            subject=self.sub_ona_tili,
            assigned_date=timezone.now().date(),
            due_date=due,
            is_active=True,
            created_by=self.teacher_user
        )
        ass1.classrooms.add(self.class_1a)

        # Yangi o'quvchi telefon raqami bilan kiradi
        session = self.client.session
        session['auth_phone'] = "+998909876543"
        session['auth_pin'] = "123456"
        session.save()

        # Profilni to'ldirish formasi orqali 1-A sinfini tanlaydi
        res = self.client.post(reverse('register_profile'), {
            'first_name': "Ali",
            'last_name': "Valiyev",
            'classroom': self.class_1a.id
        })
        self.assertEqual(res.status_code, 302)

        # O'quvchi yaratilgan bo'lishi kerak va unga 1-A dagi vazifa biriktirilgan bo'lishi kerak
        student = StudentProfile.objects.filter(phone_number="+998909876543").first()
        self.assertIsNotNone(student)
        self.assertEqual(student.classroom, self.class_1a)

        # Vazifa biriktirilganini tekshiramiz
        task = StudentAssignment.objects.filter(student=student, assignment=ass1).first()
        self.assertIsNotNone(task)
        self.assertEqual(task.status, 'not_started')

    def test_assignment_created_by_admin_is_distributed_to_all_1a_students(self):
        """Admin yoki o'qituvchi 1-A ga vazifa jo'natganda barcha 1-A o'quvchilariga borishi kerak"""
        # 1-A ga 2 ta o'quvchi qo'shamiz
        u1 = User.objects.create_user(username='std1', password='pass')
        s1 = StudentProfile.objects.create(user=u1, first_name="Olim", last_name="Karimov", phone_number="+998901110001", classroom=self.class_1a)

        u2 = User.objects.create_user(username='std2', password='pass')
        s2 = StudentProfile.objects.create(user=u2, first_name="Zilola", last_name="Azimova", phone_number="+998901110002", classroom=self.class_1a)

        # Bosh admin tizimga kiradi va 1-A uchun yangi vazifa yuklaydi
        self.client.login(username='maktab_admini', password='AdminPassword123')
        due_str = (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')
        res = self.client.post(reverse('admin_assignments'), {
            'action': 'create',
            'title': "Matematika 1-dars",
            'subject': self.sub_matematika.id,
            'classrooms': [self.class_1a.id],
            'assigned_date': timezone.now().date().strftime('%Y-%m-%d'),
            'due_date': due_str,
            'description': "1-5 misollar",
            'content': "Misollarni daftarga yozing",
            'is_active': True
        })
        self.assertEqual(res.status_code, 302)

        # Vazifa yaratilganini tekshiramiz
        ass = Assignment.objects.filter(title="Matematika 1-dars").first()
        self.assertIsNotNone(ass)

        # Ikkala 1-A o'quvchisiga ham vazifa birikkan bo'lishi kerak!
        self.assertTrue(StudentAssignment.objects.filter(student=s1, assignment=ass).exists())
        self.assertTrue(StudentAssignment.objects.filter(student=s2, assignment=ass).exists())

    def test_student_submits_homework_and_admin_reviews_it(self):
        """O'quvchi vazifani bajarib javob yuborganda, admin yoki o'qituvchida ko'rinadi va tekshirib baholanadi"""
        # O'quvchi va vazifa
        u = User.objects.create_user(username='std_test', password='TestPassword123')
        student = StudentProfile.objects.create(
            user=u, first_name="Kamol", last_name="Rasulov",
            phone_number="+998909990001", classroom=self.class_1a
        )
        ass = Assignment.objects.create(
            title="Misollarni yechish",
            subject=self.sub_matematika,
            due_date=timezone.now() + timedelta(days=1),
            created_by=self.teacher_user
        )
        ass.classrooms.add(self.class_1a)

        task = StudentAssignment.objects.create(assignment=ass, student=student)

        # O'quvchi tizimga kiradi
        self.client.login(username='std_test', password='TestPassword123')

        # Vazifa oynasida javob matnini yuboradi
        sub_res = self.client.post(reverse('student_assignment_detail', kwargs={'task_id': task.id}), {
            'action_type': 'submit_work',
            'submission_text': "Misollarni to'liq yechdim. Javob: 42"
        })
        self.assertEqual(sub_res.status_code, 302)

        task.refresh_from_db()
        self.assertEqual(task.status, 'submitted')
        self.assertEqual(task.submission.submission_text, "Misollarni to'liq yechdim. Javob: 42")

        # Admin yoki ustoz ko'rib tekshiradi
        self.client.login(username='maktab_admini', password='AdminPassword123')
        rev_res = self.client.post(reverse('admin_review_submission', kwargs={'task_id': task.id}), {
            'status': 'approved',
            'teacher_feedback': "Barakalla, 5 baho!"
        })
        self.assertEqual(rev_res.status_code, 302)

        task.refresh_from_db()
        self.assertEqual(task.status, 'approved')
        self.assertEqual(task.submission.review_status, 'approved')
        self.assertEqual(task.submission.teacher_feedback, "Barakalla, 5 baho!")

    def test_student_photo_submission_and_admin_view(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        # Yangi o'quvchi
        user_std = User.objects.create_user(username='std_photo', password='TestPassword123')
        student = StudentProfile.objects.create(
            user=user_std,
            first_name='Fotima',
            last_name='Xoliqova',
            classroom=self.class_1a,
            phone_number='+998901112233'
        )
        ass = Assignment.objects.create(
            title="Daftardagi yozuv vazifasi",
            subject=self.sub_matematika,
            due_date=timezone.now() + timedelta(days=2),
            created_by=self.teacher_user
        )
        ass.classrooms.add(self.class_1a)
        task = StudentAssignment.objects.create(assignment=ass, student=student)

        # O'quvchi login qiladi
        self.client.login(username='std_photo', password='TestPassword123')

        # O'quvchi daftarning 2 ta sahifasini rasmga olib yuboradi
        img1 = SimpleUploadedFile("daftar_sahifa1.jpg", b"image data 1", content_type="image/jpeg")
        img2 = SimpleUploadedFile("daftar_sahifa2.jpg", b"image data 2", content_type="image/jpeg")

        sub_res = self.client.post(
            reverse('student_assignment_detail', kwargs={'task_id': task.id}),
            {
                'action_type': 'submit_work',
                'submission_text': "Daftarning 2 ta betini rasmga tushirdim",
                'files': [img1, img2]
            }
        )
        self.assertEqual(sub_res.status_code, 302)

        task.refresh_from_db()
        self.assertEqual(task.status, 'submitted')
        self.assertFalse(task.completed_without_files)
        self.assertEqual(task.submission.attachments.count(), 2)

        # Admin tekshiradi va rasmlarni ko'ra oladi
        self.client.login(username='maktab_admini', password='AdminPassword123')
        rev_page = self.client.get(reverse('admin_review_submission', kwargs={'task_id': task.id}))
        self.assertEqual(rev_page.status_code, 200)
        self.assertContains(rev_page, "Daftarning 2 ta betini rasmga tushirdim")
        self.assertContains(rev_page, "secure-media/submission")

        # Rasm URL-iga kirib ko'radi
        first_att = task.submission.attachments.first()
        media_res = self.client.get(reverse('secure_submission_media', kwargs={'attachment_id': first_att.id}))
        self.assertEqual(media_res.status_code, 200)
        self.assertEqual(media_res['Content-Type'], 'image/jpeg')

