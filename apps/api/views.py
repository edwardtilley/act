from django.http import JsonResponse
from django.utils import timezone


def health(request):
    return JsonResponse({
        "app": "advance",
        "status": "up",
        "version": "1.0.0",
        "datetime_utc": timezone.now().isoformat()
    })
