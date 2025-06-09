from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import path

def health_check(request):
    return JsonResponse({"status": "healthy"})

urlpatterns = [
    path('health/', health_check, name='health_check'),
]
