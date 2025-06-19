import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import default_storage
import requests
import json

@csrf_exempt
def process_voice(request):
    if request.method == 'POST':
        # Check if file was uploaded
        if 'voice_file' not in request.FILES:
            return JsonResponse({'error': 'No voice file provided'}, status=400)
        
        # Get the uploaded file
        voice_file = request.FILES['voice_file']
        
        # Check file type
        allowed_types = ['.mp3', '.aac']
        file_extension = os.path.splitext(voice_file.name)[1].lower()
        if file_extension not in allowed_types:
            return JsonResponse({'error': 'Invalid file type. Only MP3 and AAC are supported.'}, status=400)
        
        # Get language parameter
        language = request.POST.get('language')
        if not language:
            return JsonResponse({'error': 'Language parameter is required'}, status=400)
        
        # Save the file temporarily
        file_path = default_storage.save('temp/' + voice_file.name, voice_file)
        
        try:
            # Convert file to base64 for Sunbird API
            with open(os.path.join(settings.MEDIA_ROOT, file_path), 'rb') as f:
                audio_data = f.read()
                audio_base64 = audio_data.encode('base64')
            
            # Prepare Sunbird API request
            sunbird_url = "https://api.sunbird.ai/v1/transcribe"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {os.getenv("SUNBIRD_API_KEY")}'
            }
            
            payload = {
                'audio': audio_base64,
                'language': language,
                'format': 'text'
            }
            
            # Call Sunbird API
            response = requests.post(sunbird_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return JsonResponse({
                    'success': True,
                    'transcription': result.get('transcription', ''),
                    'language': language
                })
            else:
                return JsonResponse({
                    'error': f'Sunbird API error: {response.text}',
                    'status_code': response.status_code
                }, status=500)
            
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'status_code': 500
            }, status=500)
        
        finally:
            # Clean up temporary file
            if os.path.exists(os.path.join(settings.MEDIA_ROOT, file_path)):
                os.remove(os.path.join(settings.MEDIA_ROOT, file_path))
                
    return JsonResponse({'error': 'Method not allowed'}, status=405)
