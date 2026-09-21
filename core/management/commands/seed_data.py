from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import (
    AdminProfile, Classroom, Subject, StudentProfile, Assignment,
    StudentAssignment, Submission, SubmissionHistory, AuditLog
)


class Command(BaseCommand):
    help = "Boshlang'ich maktab, sinflar, fanlar, o'quvchilar va test vazifalarini yaratadi"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Test ma'lumotlarini yaratish boshlandi..."))

        # 1. Superuser / Admin
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={'first_name': "Bosh", 'last_name': "Administrator", 'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin_user.set_password("admin12345")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Admin yaratildi: admin / admin12345"))

        admin_profile, _ = AdminProfile.objects.get_or_create(
            user=admin_user,
            defaults={'full_name': "Bosh Administrator", 'phone_number': "+998900000001", 'role': "Bosh O'qituvchi"}
        )

        # 2. Classrooms
        classes_data = [
            ("1-A", 1, "2025-2026"),
            ("1-B", 1, "2025-2026"),
            ("2-A", 2, "2025-2026"),
            ("3-B", 3, "2025-2026"),
        ]
        created_classes = {}
        for name, grade, year in classes_data:
            c_obj, _ = Classroom.objects.get_or_create(
                name=name,
                defaults={'grade_level': grade, 'academic_year': year, 'is_active': True}
            )
            created_classes[name] = c_obj

        # 3. Subjects
        subjects_data = [
            ("Matematika", "MATH", "calculator"),
            ("Ona tili", "UZB", "book-open"),
            ("Ingliz tili", "ENG", "globe"),
            ("Tabiiy fanlar", "SCI", "leaf"),
            ("Informatika", "IT", "monitor"),
        ]
        created_subjects = {}
        for name, code, icon in subjects_data:
            s_obj, _ = Subject.objects.get_or_create(
                name=name,
                defaults={'code': code, 'icon': icon, 'is_active': True}
            )
            created_subjects[name] = s_obj

        # 4. Students
        students_data = [
            ("Sardor", "Aliyev", "+998901112233", "1-A"),
            ("Madina", "Karimova", "+998902223344", "1-A"),
            ("Jasur", "Toshmatov", "+998903334455", "1-A"),
            ("Bobur", "Valiyev", "+998904445566", "1-B"),
            ("Rayhon", "Sobirova", "+998905556677", "1-B"),
            ("Dilshod", "Ergashev", "+998906667788", "2-A"),
        ]
        created_students = []
        for fn, ln, phone, c_name in students_data:
            st = StudentProfile.objects.filter(phone_number=phone).first()
            if not st:
                u = User.objects.create_user(
                    username=f"std_{phone[-9:]}",
                    first_name=fn,
                    last_name=ln
                )
                u.set_unusable_password()
                u.save()
                st = StudentProfile.objects.create(
                    user=u,
                    first_name=fn,
                    last_name=ln,
                    classroom=created_classes[c_name],
                    phone_number=phone,
                    is_active=True
                )
            created_students.append(st)

        # 5. Assignments
        now = timezone.now()
        ass1, _ = Assignment.objects.get_or_create(
            title="10 ichida sonlarni qo'shish va ayirish",
            subject=created_subjects["Matematika"],
            defaults={
                'description': "Darslikning 45-betidagi 1-5 topshiriqlarni daftarga yozish.",
                'content': "1. 5 + 3 = ?\n2. 9 - 4 = ?\n3. 7 + 2 = ?\n4. 10 - 6 = ?\n5. 8 + 1 = ?",
                'assigned_date': (now - timedelta(days=2)).date(),
                'due_date': now + timedelta(days=2),
                'is_active': True,
                'created_by': admin_user
            }
        )
        ass1.classrooms.set([created_classes["1-A"], created_classes["1-B"]])

        ass2, _ = Assignment.objects.get_or_create(
            title="Harakat bildiruvchi so'zlar (Fe'l)",
            subject=created_subjects["Ona tili"],
            defaults={
                'description': "Harakat bildiruvchi 5 ta so'z ishtirokida gaplar tuzing.",
                'content': "O'qidi, yozdi, bordi, keldi, o'ynadi so'zlari yordamida gaplar yozib daftaringizni rasmga olib yuklang.",
                'assigned_date': (now - timedelta(days=1)).date(),
                'due_date': now + timedelta(days=3),
                'is_active': True,
                'created_by': admin_user
            }
        )
        ass2.classrooms.set([created_classes["1-A"]])

        ass3, _ = Assignment.objects.get_or_create(
            title="Family Members - Oila a'zolari",
            subject=created_subjects["Ingliz tili"],
            defaults={
                'description': "Mother, Father, Brother, Sister so'zlarini daftarga yozib yod oling.",
                'content': "Ingliz tilida oilangiz haqida 3 ta gap yozing va topshiring.",
                'assigned_date': (now - timedelta(days=3)).date(),
                'due_date': now - timedelta(hours=5), # overdue for testing
                'is_active': True,
                'created_by': admin_user
            }
        )
        ass3.classrooms.set([created_classes["1-A"], created_classes["2-A"]])

        # 6. StudentAssignments and Submissions
        for st in created_students:
            for ass in Assignment.objects.filter(classrooms=st.classroom):
                task, _ = StudentAssignment.objects.get_or_create(assignment=ass, student=st)

                # Set distinct statuses for rich demo
                if st.first_name == "Sardor" and ass == ass1:
                    task.status = "approved"
                    task.marked_done_at = now - timedelta(days=1)
                    task.save()
                    sub, _ = Submission.objects.get_or_create(
                        student_assignment=task,
                        defaults={
                            'submission_text': "Hamma misollarni daftarga to'liq yechdim. Javoblar to'g'ri chiqdi.",
                            'review_status': 'approved',
                            'teacher_feedback': "Barakalla Sardor! Hamma misollar to'g'ri ishlangan. 5 baho!",
                            'reviewed_at': now - timedelta(hours=12),
                            'reviewed_by': admin_user
                        }
                    )
                elif st.first_name == "Madina" and ass == ass1:
                    task.status = "submitted"
                    task.marked_done_at = now - timedelta(hours=6)
                    task.save()
                    Submission.objects.get_or_create(
                        student_assignment=task,
                        defaults={
                            'submission_text': "Misollar yechildi. Rasm sifatli olindi.",
                            'review_status': 'pending',
                        }
                    )
                elif st.first_name == "Jasur" and ass == ass1:
                    task.status = "completed"
                    task.marked_done_at = now - timedelta(hours=4)
                    task.completed_without_files = True
                    task.save()
                elif st.first_name == "Sardor" and ass == ass3:
                    task.status = "needs_work"
                    task.marked_done_at = now - timedelta(days=1)
                    task.save()
                    Submission.objects.get_or_create(
                        student_assignment=task,
                        defaults={
                            'submission_text': "I have a mother and father.",
                            'review_status': 'needs_work',
                            'teacher_feedback': "Gaplar soni 3 ta bo'lishi kerak edi. Iltimos yana bitta gap qo'shib yubor!",
                            'reviewed_at': now - timedelta(hours=5),
                            'reviewed_by': admin_user
                        }
                    )

        # 7. Audit log
        AuditLog.objects.create(
            user=admin_user,
            action="Tizim boshlang'ich ma'lumotlar bilan to'ldirildi (seed_data)",
            target_model="System",
            details="4 ta sinf, 5 ta fan, 6 ta o'quvchi, 3 ta vazifa yaratildi."
        )

        self.stdout.write(self.style.SUCCESS("Barcha test ma'lumotlari muvaffaqiyatli yaratildi!"))
        self.stdout.write(self.style.NOTICE("Admin login: admin / admin12345"))
        self.stdout.write(self.style.NOTICE("Test o'quvchi telefoni: +998901112233 (OTP: 123456 yoki ekranda chiqadi)"))
