from django.urls import path
from .views import RegisterView, login_view, VoiceTextEntryView
from .views import audio_process_view, FinancialRecordsView, user_sales_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', login_view, name='login'),
    path('voice-text/', VoiceTextEntryView.as_view(), name='voice-text'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/records/', FinancialRecordsView.as_view(), name='financial-records'),
    path('audio-process/', audio_process_view, name='audio-process'),
    path('sales/', user_sales_view, name='user-sales'),
]
