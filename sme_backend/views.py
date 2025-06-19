from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import path
from .models import Record
import json
from django.core.files.storage import default_storage
import requests
import os
from django.conf import settings
from django.core.files.base import ContentFile
import magic
from .services import translate_text, analyze_business_transaction, format_response

# Initialize Sunbird client
sunbird_client = None
if settings.SUNBIRD_API_KEY:
    sunbird_client = requests.Session()
    sunbird_client.headers.update({
        'Authorization': f'Bearer {settings.SUNBIRD_API_KEY}',
        'Content-Type': 'application/json'
    })

def process_audio_with_sunbird(audio_file_path, language):
    """Process audio file using Sunbird API"""
    try:
        # Check file type
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(audio_file_path)
        if 'audio' not in file_type:
            raise ValueError('Invalid audio file type')

        # Read audio file
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()

        # Prepare request
        files = {
            'audio': ('audio_file', audio_data, file_type)
        }
        data = {
            'language': language
        }

        # Send to Sunbird API
        response = sunbird_client.post(
            f'{settings.SUNBIRD_API_URL}/process_audio',
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('transcription', '')
        else:
            raise Exception(f'Sunbird API error: {response.text}')

    except Exception as e:
        raise Exception(f'Error processing audio: {str(e)}')

def process_business_transaction(text, language):
    """Process business transaction text"""
    try:
        # Translate to English for analysis
        english_text = translate_text(text, target_lang='en')
        
        # Analyze the transaction
        analysis = analyze_business_transaction(english_text)
        
        # Create or update record
        record = Record.objects.create(
            text=english_text,
            original_text=text,
            original_language=language,
            product_name=analysis.get('product_name', ''),
            quantity=analysis.get('quantity'),
            unit_price=analysis.get('unit_price'),
            total_price=analysis.get('total_price'),
            missing_info=analysis.get('missing_info'),
            status='COMPLETED' if not analysis.get('missing_info') else 'INCOMPLETE'
        )
        
        # Format response in original language
        response_text = format_response(analysis, language)
        
        return {
            "id": record.id,
            "status": record.status,
            "response": response_text,
            "original_text": text,
            "analyzed_text": english_text,
            "product_name": record.product_name,
            "quantity": record.quantity,
            "unit_price": str(record.unit_price),
            "total_price": str(record.total_price),
            "missing_info": record.missing_info
        }
        
    except Exception as e:
        Record.objects.create(
            text=text,
            status='ERROR',
            error_message=str(e)
        )
        raise Exception(f"Transaction processing failed: {str(e)}")

@require_http_methods(["POST"])
def create_record(request):
    try:
        # Handle text record
        if request.body:
            data = json.loads(request.body)
            if 'text' in data:
                language = data.get('language', '')
                result = process_business_transaction(data['text'], language)
                return JsonResponse(result)
        
        # Handle audio upload
        elif request.FILES.get('audio_file'):
            audio_file = request.FILES['audio_file']
            language = request.POST.get('language', '')
            
            # Save the audio file
            file_path = f'audio_uploads/{audio_file.name}'
            with default_storage.open(file_path, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)
            
            # Process audio with Sunbird if API is configured
            transcription = ''
            if sunbird_client:
                try:
                    transcription = process_audio_with_sunbird(file_path, language)
                    result = process_business_transaction(transcription, language)
                    return JsonResponse(result)
                except Exception as e:
                    return JsonResponse({
                        "error": f"Failed to process audio with Sunbird: {str(e)}",
                        "status": "error"
                    }, status=400)
            
            return JsonResponse({
                "error": "Sunbird API not configured",
                "status": "error"
            }, status=400)
        
        return JsonResponse({"error": "Invalid request"}, status=400)
    
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "status": "error"
        }, status=400)

@require_http_methods(["GET"])
def get_records(request):
    records = Record.objects.all().order_by('-created_at')
    data = []
    for record in records:
        record_data = {
            "id": record.id,
            "text": record.text,
            "product_name": record.product_name,
            "quantity": record.quantity,
            "unit_price": str(record.unit_price),
            "total_price": str(record.total_price),
            "language": record.language,
            "created_at": record.created_at.isoformat()
        }
        if record.audio_file:
            record_data["audio_file"] = record.audio_file.url
        data.append(record_data)
    
    return JsonResponse({"records": data})

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('records/', create_record, name='create_record'),
    path('records/list/', get_records, name='get_records'),
]
