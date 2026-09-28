from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Classroom, StudentProfile, AdminProfile, Subject, Assignment, StudentAssignment


class RolesAndPasswordsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.classroom = Classroom.objects.create(name="5-A", grade_level=5)
        self.subject = Subject.objects.create(name="Matematika", code="MATH-05")

        # 1. Bosh administrator yaratamiz
        self.admin_user = User.objects.create_superuser(
            username='admin_boss',
            password='AdminPassword123'
        )
        self.admin_profile = AdminProfile.objects.create(
            user=self.admin_user,
            full_name="Bosh Administrator",
            role='admin'
        )

        # 2. O'qituvchi yaratamiz
        self.teacher_user = User.objects.create_user(
            username='teacher_ali',
            password='TeacherPassword123',
            is_staff=True
        )
        self.teacher_profile = AdminProfile.objects.create(
            user=self.teacher_user,
            full_name="Aliyev Vali O'qituvchi",
            role='teacher',
            subject=self.subject,
            raw_password='TeacherPassword123'
        )
        self.teacher_profile.classrooms.add(self.classroom)

        # 3. O'quvchi yaratamiz
        self.student_user = User.objects.create_user(
            username='std_901234567',
            password='StudentPass123'
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            first_name="Jasur",
            last_name="Toshmatov",
            phone_number="+998901234567",
            classroom=self.classroom,
            raw_password='StudentPass123'
        )

    def test_student_login_with_phone_and_password(self):
        """O'quvchi telefon raqami va paroli bilan tizimga muvaffaqiyatli kirishi kerak"""
        response = self.client.post(reverse('login'), {
            'action': 'login',
            'phone': '+998901234567',
            'password': 'StudentPass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('student_dashboard'))

    def test_student_wrong_password_fails(self):
        """Noto'g'ri parol kiritilganda xatolik berishi kerak"""
        response = self.client.post(reverse('login'), {
            'action': 'login',
            'phone': '+998901234567',
            'password': 'WrongPassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kiritilgan parol noto&#x27;g&#x27;ri")

    def test_student_get_password_generation(self):
        """Telefon raqam orqali 1 martalik parol olish va parolni saqlash"""
        response = self.client.post(reverse('login'), {
            'action': 'get_password',
            'phone': '+998901234567'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('student_password_issued'))

        # O'quvchining paroli bazada yangilangan bo'lishi kerak
        self.student_profile.refresh_from_db()
        self.assertEqual(len(self.student_profile.raw_password), 6)
        # Shu yangi parol bilan kirish mumkin bo'lishi kerak
        self.assertTrue(self.student_profile.user.check_password(self.student_profile.raw_password))

    def test_admin_creates_teacher_with_login_and_password(self):
        """Bosh admin o'qituvchiga login va parol berib yarata olishi kerak"""
        self.client.login(username='admin_boss', password='AdminPassword123')
        response = self.client.post(reverse('admin_teachers'), {
            'action': 'create',
            'full_name': "Karimova Ziyoda",
            'phone_number': "+998905554433",
            'subject': self.subject.id,
            'username': 'ustoz_ziyoda',
            'password': 'ZiyodaSecretPassword2026',
            'classrooms': [self.classroom.id]
        })
        self.assertEqual(response.status_code, 302)

        # O'qituvchi bazada paydo bo'lishi kerak
        new_teacher = AdminProfile.objects.filter(role='teacher', user__username='ustoz_ziyoda').first()
        self.assertIsNotNone(new_teacher)
        self.assertEqual(new_teacher.raw_password, 'ZiyodaSecretPassword2026')
        self.assertTrue(new_teacher.user.check_password('ZiyodaSecretPassword2026'))

    def test_admin_can_manage_assignments(self):
        """Bosh admin ham o'qituvchilar kabi vazifa yarata va o'chira olishi kerak"""
        # Vazifa yaratamiz
        ass = Assignment.objects.create(
            title="Uyga vazifa 1",
            subject=self.subject,
            due_date="2026-10-01 18:00:00+05:00",
            created_by=self.teacher_user
        )

        # Admin sifatida kiramiz
        self.client.login(username='admin_boss', password='AdminPassword123')

        # Admin sahifani ko'ra oladi va vazifa yaratish tugmasi chiqadi
        get_res = self.client.get(reverse('admin_assignments'))
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, "Yangi vazifa yaratish")

        # Admin vazifa o'chirishga ruxsat olgan
        post_res = self.client.post(reverse('admin_assignments'), {
            'action': 'delete',
            'assignment_id': ass.id
        })
        self.assertEqual(post_res.status_code, 302)
        # Vazifa o'chirilgan bo'lishi kerak!
        self.assertFalse(Assignment.objects.filter(id=ass.id).exists())

    def test_teacher_can_create_and_delete_assignment(self):
        """O'qituvchi esa vazifa yarata oladi va o'chira oladi"""
        self.client.login(username='teacher_ali', password='TeacherPassword123')

        # O'qituvchi sahifani ko'radi
        get_res = self.client.get(reverse('admin_assignments'))
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, "Yangi vazifa yaratish")
