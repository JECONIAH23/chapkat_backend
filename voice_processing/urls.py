from django.urls import path
from . import views

urlpatterns = [
    path('process-voice/', views.process_voice, name='process_voice'),
]
