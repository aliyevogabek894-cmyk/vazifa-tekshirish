from core.models import AuditLog


def get_client_ip(request):
    """Safely extract client IP from Django request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_action(request, action: str, target_model: str = "", target_id: str = "", details: str = ""):
    """Helper to record an audit trail event"""
    user = request.user if request and request.user.is_authenticated else None
    ip_addr = get_client_ip(request) if request else None
    
    return AuditLog.objects.create(
        user=user,
        action=action,
        target_model=target_model,
        target_id=str(target_id),
        details=details,
        ip_address=ip_addr
    )
