import random
import re
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from core.models import PhoneVerificationOTP


def normalize_phone(phone: str) -> str:
    """Normalize phone to format +998901234567"""
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('998') and len(digits) == 12:
        return f"+{digits}"
    elif len(digits) == 9:
        return f"+998{digits}"
    elif digits.startswith('8') and len(digits) == 10:
        return f"+998{digits[1:]}"
    return f"+{digits}" if not phone.startswith('+') else phone


def generate_otp_code() -> str:
    """Generate 6-digit verification code"""
    return f"{random.randint(100000, 999999)}"


def send_otp(phone_number: str) -> tuple[bool, str, str]:
    """
    Creates and 'sends' OTP. In development, returns the code for easy login.
    Returns: (success: bool, message: str, otp_code: str)
    """
    clean_phone = normalize_phone(phone_number)
    
    # Invalidate previous unused OTPs for this phone
    PhoneVerificationOTP.objects.filter(phone_number=clean_phone, is_used=False).update(is_used=True)
    
    otp_code = generate_otp_code()
    # For local test convenience, if specific test phone, standard code can also work
    expires_at = timezone.now() + timedelta(minutes=5)
    
    otp_obj = PhoneVerificationOTP.objects.create(
        phone_number=clean_phone,
        otp_code=otp_code,
        expires_at=expires_at
    )
    
    # Here, real SMS API (Eskiz, PlayMobile, etc.) can be called.
    # In development mode, we log and return the code:
    print(f"[SMS OTP DEV] Telefon: {clean_phone} uchun tasdiqlash kodi: {otp_code}")
    
    return True, f"Tasdiqlash kodi yuborildi.", otp_code


def verify_otp(phone_number: str, code: str) -> tuple[bool, str]:
    """
    Verifies the provided OTP code.
    Returns: (is_valid: bool, error_or_success_message: str)
    """
    clean_phone = normalize_phone(phone_number)
    
    # Check master test code for instant evaluation/testing if DEBUG is True
    if settings.DEBUG and code == "123456":
        return True, "Muvaffaqiyatli tasdiqlandi (Test OTP)."
        
    otp_obj = PhoneVerificationOTP.objects.filter(
        phone_number=clean_phone,
        is_used=False
    ).order_by('-created_at').first()
    
    if not otp_obj:
        return False, "Tasdiqlash kodi topilmadi yoki muddati o'tgan. Iltimos, qaytadan yuboring."
        
    if timezone.now() > otp_obj.expires_at:
        otp_obj.is_used = True
        otp_obj.save()
        return False, "Tasdiqlash kodining amal qilish muddati (5 daqiqa) tugagan."
        
    if otp_obj.attempts >= 5:
        otp_obj.is_used = True
        otp_obj.save()
        return False, "Urinishlar soni oshib ketdi. Yangi kod so'rang."
        
    if otp_obj.otp_code != code.strip():
        otp_obj.attempts += 1
        otp_obj.save()
        return False, f"Noto'g'ri kod kiritildi! Qolgan urinishlar: {5 - otp_obj.attempts}"
        
    # Valid code
    otp_obj.is_used = True
    otp_obj.save()
    return True, "Muvaffaqiyatli tasdiqlandi."
