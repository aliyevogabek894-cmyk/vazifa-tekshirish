from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import StudentProfile, Classroom, PhoneVerificationOTP
from core.utils.otp_service import send_otp, verify_otp, normalize_phone


class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.classroom = Classroom.objects.create(name="1-A", grade_level=1)

    def test_phone_normalization(self):
        self.assertEqual(normalize_phone("901234567"), "+998901234567")
        self.assertEqual(normalize_phone("+998 90 123 45 67"), "+998901234567")
        self.assertEqual(normalize_phone("998901234567"), "+998901234567")

    def test_send_and_verify_otp(self):
        phone = "+998901234567"
        success, msg, code = send_otp(phone)
        self.assertTrue(success)
        self.assertEqual(len(code), 6)

        # Correct OTP
        is_valid, _ = verify_otp(phone, code)
        self.assertTrue(is_valid)

        # Used OTP should fail
        is_valid_again, _ = verify_otp(phone, code)
        self.assertFalse(is_valid_again)

    from django.test import override_settings

    @override_settings(DEBUG=True)
    def test_master_test_otp_in_debug(self):
        phone = "+998909998877"
        send_otp(phone)
        is_valid, _ = verify_otp(phone, "123456")
        self.assertTrue(is_valid)
