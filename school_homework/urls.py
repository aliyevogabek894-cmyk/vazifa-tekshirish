from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.utils import timezone


def health_check(request):
    """Saytni uyquga ketmasligi uchun ping endpoint. UptimeRobot shu URLga murojaat qiladi."""
    return JsonResponse({
        'status': 'ok',
        'message': 'Maktab tizimi ishlayapti!',
        'time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
    })


urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Media is routed via secure media views, but standard avatar media can also be served in DEBUG
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
