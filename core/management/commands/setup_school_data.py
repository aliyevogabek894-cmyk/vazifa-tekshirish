from django.core.management.base import BaseCommand
from core.models import Classroom, Subject


class Command(BaseCommand):
    help = "Barcha maktab sinflari (1-6 harfli, 7-11 yo'nalishli) va fanlarini yaratadi yoki yangilaydi"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Sinflar va fanlarni yaratish boshlandi..."))

        # 1. Sinflarni yaratish
        # 1-6 sinflar: A, B, C, D, F
        letters = ['A', 'B', 'C', 'D', 'F']
        classrooms_created = 0
        classrooms_updated = 0

        for grade in range(1, 7):
            for letter in letters:
                name = f"{grade}-{letter}"
                obj, created = Classroom.objects.get_or_create(
                    name=name,
                    defaults={
                        'grade_level': grade,
                        'academic_year': '2025-2026',
                        'is_active': True,
                    }
                )
                if created:
                    classrooms_created += 1
                else:
                    if obj.grade_level != grade or not obj.is_active:
                        obj.grade_level = grade
                        obj.is_active = True
                        obj.save()
                        classrooms_updated += 1

        # 7-11 sinflar: Ijtimoiy, Aniq, Tabiiy
        specialties = ['Ijtimoiy', 'Aniq', 'Tabiiy']
        for grade in range(7, 12):
            for spec in specialties:
                name = f"{grade}-{spec}"
                obj, created = Classroom.objects.get_or_create(
                    name=name,
                    defaults={
                        'grade_level': grade,
                        'academic_year': '2025-2026',
                        'is_active': True,
                    }
                )
                if created:
                    classrooms_created += 1
                else:
                    if obj.grade_level != grade or not obj.is_active:
                        obj.grade_level = grade
                        obj.is_active = True
                        obj.save()
                        classrooms_updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Sinflar: {classrooms_created} ta yangi yaratildi, {classrooms_updated} ta yangilandi. Jami faol sinflar: {Classroom.objects.filter(is_active=True).count()} ta"
        ))

        # 2. Maktab darsliklari va fanlari
        subjects_data = [
            ("Ona tili", "UZB", "book-open"),
            ("Adabiyot", "LIT", "book"),
            ("Matematika", "MATH", "calculator"),
            ("Algebra", "ALG", "percent"),
            ("Geometriya", "GEOM", "triangle"),
            ("Informatika va AT", "IT", "monitor"),
            ("Ingliz tili", "ENG", "globe"),
            ("Rus tili", "RUS", "languages"),
            ("Fizika", "PHYS", "zap"),
            ("Kimyo", "CHEM", "flask-conical"),
            ("Biologiya", "BIO", "dna"),
            ("Tabiiy fanlar (Science)", "SCI", "leaf"),
            ("O'zbekiston tarixi", "HIST_UZ", "landmark"),
            ("Jahon tarixi", "HIST_W", "compass"),
            ("Davlat va huquq asoslari", "LAW", "scale"),
            ("Geografiya", "GEO", "map"),
            ("Tarbiya", "ETHICS", "heart-handshake"),
            ("Texnologiya", "TECH", "wrench"),
            ("Tasviriy san'at", "ART", "palette"),
            ("Musiqa madaniyati", "MUSIC", "music"),
            ("Jismoniy tarbiya", "PE", "activity"),
            ("CHQBT (Harbiy tayyorgarlik)", "MIL", "shield"),
            ("Iqtisodiy bilim asoslari", "ECON", "trending-up"),
        ]

        subjects_created = 0
        for name, code, icon in subjects_data:
            s_obj, created = Subject.objects.get_or_create(
                name=name,
                defaults={'code': code, 'icon': icon, 'is_active': True}
            )
            if created:
                subjects_created += 1
            else:
                s_obj.is_active = True
                s_obj.code = code
                s_obj.icon = icon
                s_obj.save()

        self.stdout.write(self.style.SUCCESS(
            f"Fanlar: {subjects_created} ta yangi yaratildi. Jami fanlar: {Subject.objects.filter(is_active=True).count()} ta"
        ))
