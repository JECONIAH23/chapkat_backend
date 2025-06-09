from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SMEUserSerializer
from django.contrib.auth import login
from .serializers import LoginSerializer
from rest_framework.permissions import IsAuthenticated
from .models import VoiceTextEntry
from .serializers import VoiceTextEntrySerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import authentication_classes, permission_classes, api_view
from .llm_utils import call_openrouter_and_parse
from .models import FinancialRecord, SMEUser, AudioUpload
from .serializers import FinancialRecordSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
import os
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import parser_classes
from django.utils.html import escape
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings


class FinancialRecordsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = FinancialRecord.objects.filter(user=request.user).order_by('-id')
        serializer = FinancialRecordSerializer(records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class RegisterView(APIView):
    def post(self, request):
        serializer = SMEUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# legacy view
# class LoginView(APIView):
#     def post(self, request):
#         serializer = LoginSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.validated_data['user']
#             login(request, user)  # create session
#             return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# new login view
@api_view(['POST'])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# transcribe, translate, extract financial record
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def audio_process_view(request):
    # language = request.data.get("language")
    # audio_file = request.FILES.get("audio")

    audio_file = request.FILES.get("audio")
    language = request.data.get("language")
    user = request.user
    
    if not language or not audio_file:
        return Response({"error": "Please provide both 'language' and 'audio' file."},
                        status=status.HTTP_400_BAD_REQUEST)

    # Save the audio file to the DB
    audio_record = AudioUpload.objects.create(
        user=user,
        audio_file=audio_file,
        language=language
    )
    
    # Sunbird STT API
    stt_url = "https://api.sunbird.ai/tasks/stt"
    stt_headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {os.getenv('AUTH_TOKEN')}",
    }

    stt_data = {
        "language": language,
        "adapter": language,
        "whisper": True,
    }

    stt_files = {
        "audio": (audio_record.audio_file.name, audio_record.audio_file.file, audio_record.audio_file.file.content_type)
    }

    try:
        stt_response = requests.post(stt_url, headers=stt_headers, data=stt_data, files=stt_files)
        stt_result = stt_response.json()
        transcription = stt_result["audio_transcription"]
    except Exception as e:
        return Response({"error": "Failed to transcribe audio", "details": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Sunbird Translation API
    translation_url = "https://api.sunbird.ai/tasks/nllb_translate"
    translation_headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {os.getenv('AUTH_TOKEN')}",
        "Content-Type": "application/json",
    }

    translation_payload = {
        "source_language": language,
        "target_language": "eng",
        "text": transcription,
    }

    try:
        translation_response = requests.post(
            translation_url, headers=translation_headers, json=translation_payload
        )
        translated_text = translation_response.json()["output"]["translated_text"]
    except Exception as e:
        return Response({"error": "Failed to translate text", "details": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Save transcription
    from .models import VoiceTextEntry
    voice_entry = VoiceTextEntry.objects.create(user=request.user, text=translated_text)

    # Call OpenRouter for financial record parsing
    from .llm_utils import call_openrouter_and_parse
    records = call_openrouter_and_parse(request.user, translated_text, voice_entry)

    # Prepare structured output
    return Response({
        "original_transcription": transcription,
        "translated_text": translated_text,
        "financial_records": [{
            "product_name": r.product_name,
            "quantity": r.quantity,
            "unit_price": float(r.unit_price),
            "total_price": float(r.total_price),
            "transaction_type": r.transaction_type
        } for r in records]
    }, status=status.HTTP_201_CREATED)


def user_sales_view(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'sales.html', {'error': 'Missing token'})

    try:
        validated_token = JWTAuthentication().get_validated_token(token)
        user = JWTAuthentication().get_user(validated_token)
    except Exception:
        return render(request, 'sales.html', {'error': 'Invalid or expired token'})

    records = FinancialRecord.objects.filter(user=user).order_by('-created_at')

    return render(request, 'sales.html', {
        'user': user,
        'records': records,
        'error': None
    })


class VoiceTextEntryView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VoiceTextEntrySerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data['text']
            user = request.user

            # Save the raw text
            VoiceTextEntry.objects.create(
                user=request.user,
                text=text
            )

            # Try extract a financial record
            records = call_openrouter_and_parse(request.user, text)

            if records:
                return Response({
                    "message": "Text saved and financial records extracted",
                    "records": [{
                        "product_name": records.product_name,
                        "quantity": records.quantity,
                        "price": records.price,
                        "total": records.total,
                        "transaction_type": records.transaction_type
                    } for r in records]
                }, status=status.HTTP_201_CREATED)
            return Response({"message": "Text saved successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
