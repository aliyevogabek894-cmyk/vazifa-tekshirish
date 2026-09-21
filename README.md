# Maktab O‘quvchilari Uchun Uy Vazifalarini Nazorat Qilish va Excel Hisobot Tizimi

Zamonaviy, professional, xavfsiz va mobil qurilmalarga to‘liq moslashtirilgan **School Homework Management System** platformasi. Ushbu tizim maktab ma’muriyati, o‘qituvchilar va o‘quvchilar o‘rtasida uy vazifalarini samarali boshqarish, topshirish, tekshirish hamda ko‘p varaqli Excel hisobotlarini shakllantirish imkonini beradi.

---

## 🌟 Asosiy Imkoniyatlar

### 1. O‘quvchilar Maxfiyligi va Xavfsizlik (Privacy-First)
- **IDOR himoyasi:** O‘quvchilar bir-birining shaxsiy profili, telefon raqami, yuborgan javoblari yoki fayllarini mutlaqo ko‘ra olmaydi.
- **Himoyalangan Media:** Barcha yuklangan fayllar (rasmlar, videolar, hujjatlar) bevosita ochiq URL orqali tarqatilmaydi. Fayllarga kirish backend darajasida (`SecureMediaView`) tekshirilib, faqat topshiriq egasi yoki admin/o‘qituvchiga ruxsat etiladi.
- **Anonim Sinf Statistikasi:** O‘quvchi sinfdoshlari orasida qancha o‘quvchi vazifani bajarganini umumiy foiz/son sifatida ko‘ra oladi, ammo hech kimning shaxsi oshkor etilmaydi.

### 2. Telefon Raqami va OTP Orqali Kirish
- O‘quvchilar login va parolsiz, o‘z telefon raqamlari (`+998 XX XXX XX XX`) orqali tizimga kiradi.
- 6 xonali OTP tasdiqlash kodi orqali autentifikatsiya qilinadi (5 daqiqa amal qilish muddati, urinishlar chegarasi).
- Birinchi marta kirgan o‘quvchi o‘z ismi, familiyasi va sinfini kiritib tezkor profil yaratadi.

### 3. Mobile-First Foydalanuvchi Interfeysi
- Smartfonlar uchun moslashtirilgan pastki navigatsiya paneli (Bottom Nav).
- Kamera orqali daftarni bevosita rasmga olib yuklash (`capture="environment"`).
- Galereyadan bir nechta rasm, video, PDF, Word hujjatlari tanlash va matnli izoh yozish.
- "Vazifani bajardim" tezkor bir martalik belgilash (faylsiz bajarilganda alohida qayd etiladi).
- Tungi rejim (Dark Mode) va yorug' rejimni saqlab qolish.

### 4. Admin va O‘qituvchi Boshqaruv Paneli
- **Dashboard:** Sinflar, o‘quvchilar, topshiriqlar statistikasi, Chart.js grafiklari (sinflar faolligi, vazifa holatlari).
- **Vazifalar yaratish:** Bitta, bir nechta yoki barcha sinflarga biriktirish, muddat belgilash, fayl/video ilova qilish.
- **Sinflar va O‘quvchilar:** Sinflar yaratish, o‘quvchilarni qo‘lda qo‘shish, tahrirlash, faollikni o‘zgartirish.
- **Excel orqali ommaviy import:** O‘quvchilarni `.xlsx` fayl orqali bir vaqtning o‘zida yuklash.
- **Topshiriqlarni tekshirish:** Yuborilgan javoblarni ko‘rish, "Qabul qilindi", "Qayta ishlash kerak" deb baholash, izoh yozish.
- **Audit Log:** Tizimdagi har bir muhim amalning xronologik jurnali.

### 5. 6 Varaqli Mukammal Excel Hisobot Moduli (openpyxl)
Admin interfeysida:
- **Variantlar:** Bitta o‘quvchi, Bitta sinf yoki Barcha sinflar bo‘yicha hisobot.
- **Filtrlar:** Sinf, O‘quvchi (sinf tanlanganda avtomatik yangilanadi), Fan, Sana oralig‘i, Vazifa holati.
- **Ekranda ko‘rish (Preview):** Jami o‘quvchilar, jami vazifalar, bajarilganlar, bajarilmaganlar va foizlar.
- **Eksport qilinadigan Excel fayli varaqlari:**
  1. `Umumiy hisobot` — Barcha ko‘rsatkichlar, parametrlar va foizlar.
  2. `O'quvchilar statistikasi` — Har bir o‘quvchining jami, bajarilgan, qabul qilingan vazifalari va bajarish foizi.
  3. `Vazifalar batafsil` — Har bir topshiriq, berilgan sana, muddat, holat, tekshiruv va izohlar.
  4. `Bajarilgan vazifalar` — Faqat muvaffaqiyatli bajarilgan topshiriqlar.
  5. `Bajarilmagan vazifalar` — Bajarilmagan va muddati o‘tgan topshiriqlar.
  6. `Fayllar va topshiriqlar` — Yuklangan barcha fayllar, turlari, hajmlari va izohlar.
- **Formatlash:** Sarlavhalar quyuq rangda, muzlatilgan 1-qator (`freeze_panes`), ustun kengliklari avtomatik moslangan, statuslar rangli (Yashil, Sariq, Qizil), formulalar kiritilgan.

---

## 🛠 Texnologiyalar

- **Backend:** Python 3.14, Django 6.1, Django REST Framework
- **Baza:** SQLite (lokal rivojlantirish uchun tayyor), PostgreSQL ga oson ulanish
- **Frontend:** HTML5, Tailwind CSS, Lucide Icons, Chart.js
- **Eksport/Import:** `openpyxl`, `pandas`

---

## 🚀 Loyihani Ishga Tushirish Bo‘yicha Qo‘llanma

### 1. Talablar
Kompyuteringizda Python (3.10+) o‘rnatilgan bo‘lishi lozim.

### 2. Kutubxonalarni o‘rnatish
```bash
pip install -r requirements.txt
```

### 3. Ma'lumotlar bazasi migratsiyasini bajarish
```bash
python manage.py migrate
```

### 4. Boshlang'ich test ma'lumotlarini yuklash (Seed Data)
Tizimni sinflar, fanlar, o‘quvchilar, namunaviy topshiriqlar va admin akkaunti bilan to‘ldirish uchun quyidagi buyruqni ishga tushiring:
```bash
python manage.py seed_data
```

### 5. Serverni ishga tushirish
```bash
python manage.py runserver
```
Brauzeringizda quyidagi manzilni oching:
`http://127.0.0.1:8000/`

---

## 🔑 Test Akkauntlari va Kirish Ma’lumotlari

### A. Admin / O‘qituvchi Kabineti
- **Kirish manzili:** `http://127.0.0.1:8000/admin-login/`
- **Login:** `admin`
- **Parol:** `admin12345`

### B. O‘quvchi Kabineti
- **Kirish manzili:** `http://127.0.0.1:8000/login/`
- **Test o‘quvchi telefon raqamlari:**
  - `+998901112233` (Sardor Aliyev, 1-A sinf)
  - `+998902223344` (Madina Karimova, 1-A sinf)
  - `+998903334455` (Jasur Toshmatov, 1-A sinf)
  - `+998904445566` (Bobur Valiyev, 1-B sinf)
- **Tasdiqlash kodi (OTP):** Lokal/dev rejimda ekranda ko‘rsatiladi yoki standart `123456` test kodi ishlaydi.

---

## 🧪 Avtomatlashtirilgan Testlarni Ishga Tushirish

Barcha testlarni (Autentifikatsiya, IDOR va Maxfiylik, 6 varaqli Excel generatsiyasi va import) tekshirish:
```bash
python manage.py test core
```
Natijada barcha 10 ta test muvaffaqiyatli (`OK`) bajariladi.

---

## 📁 Loyiha Arxitekturasi

```text
uyga vazifa/
├── manage.py
├── requirements.txt
├── README.md
├── school_homework/          # Django asosiy sozlamalari
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                     # Asosiy ilova
│   ├── models.py             # 14 ta to'liq modellar
│   ├── admin.py              # Django admin ro'yxatdan o'tkazish
│   ├── forms.py              # Formalar va validatsiyalar
│   ├── permissions.py        # IDOR va ruxsatlar tekshiruvi
│   ├── views/                # Modulli ko'rinishlar
│   │   ├── auth_views.py     # OTP va kirish
│   │   ├── student_views.py  # O'quvchi kabineti
│   │   ├── admin_views.py    # Admin boshqaruv
│   │   ├── reports_views.py  # Hisobotlar interfeysi
│   │   ├── export_views.py   # Excel generator
│   │   └── media_views.py    # Maxfiy fayllarni tarqatish
│   ├── utils/
│   │   ├── excel_exporter.py # 6 varaqli openpyxl eksport
│   │   ├── excel_importer.py # O'quvchilar importi
│   │   ├── otp_service.py    # SMS OTP xizmati
│   │   └── audit.py          # Harakatlar jurnali
│   └── tests/                # Test to'plami
├── templates/                # Tailwind CSS shablonlari
└── media/                    # Xavfsiz saqlanuvchi fayllar
```
