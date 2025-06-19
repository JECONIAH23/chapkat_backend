# Chapkat Backend API Documentation

## Overview

The Chapkat Backend API provides endpoints for processing business transactions through audio and text inputs, with support for multiple languages. The system uses AI to analyze business transactions and store them in a structured format.

## Environment Variables

Before using the API, ensure these environment variables are set:

```bash
export SUNBIRD_API_KEY=your_sunbird_api_key
export OPENROUTER_API_KEY=your_openai_api_key
export SECRET_KEY=your_django_secret_key
```

## Available Endpoints

### 1. Health Check

```
GET /health/
```

**Description**: Check if the API is running and healthy.

**Response**:
```json
{
    "status": "healthy"
}
```

### 2. Create Record (Text or Audio)

```
POST /records/
```

**Description**: Create a new record by either sending text or uploading an audio file.

**Request Types**:

1. **Text Input**:
```http
POST /records/
Content-Type: application/json

{
    "text": "Your text here",
    "language": "sw"  # Optional, defaults to system language
}
```

2. **Audio Upload**:
```http
POST /records/
Content-Type: multipart/form-data

audio_file: your_audio_file.mp3
language: sw  # Optional, defaults to system language
```

**Response**:
```json
{
    "id": "record_id",
    "status": "COMPLETED|INCOMPLETE|ERROR",
    "response": "Formatted response in original language",
    "original_text": "Original text",
    "analyzed_text": "Translated text in English",
    "product_name": "Extracted product name",
    "quantity": "Extracted quantity",
    "unit_price": "Extracted unit price",
    "total_price": "Extracted total price",
    "missing_info": ["List of missing information"]
}
```

### 3. List Records

```
GET /records/list/
```

**Description**: Get a list of all records in the system.

**Response**:
```json
{
    "records": [
        {
            "id": "record_id",
            "text": "Original text",
            "product_name": "Extracted product name",
            "quantity": "Extracted quantity",
            "unit_price": "Extracted unit price",
            "total_price": "Extracted total price",
            "missing_info": ["List of missing information"],
            "status": "COMPLETED|INCOMPLETE|ERROR",
            "error_message": "Error message if any",
            "created_at": "Creation timestamp",
            "processed_at": "Processing timestamp"
        }
    ]
}
```

## Status Codes

- `200 OK`: Request was successful
- `400 Bad Request`: Invalid request format or missing required fields
- `500 Internal Server Error`: Server encountered an error

## Response Statuses

- `COMPLETED`: Transaction was successfully processed and all information was extracted
- `INCOMPLETE`: Transaction was processed but some information is missing
- `ERROR`: An error occurred during processing

## Error Responses

All error responses will include:
```json
{
    "error": "Error message",
    "status": "error"
}
```

## Supported Languages

The system supports multiple languages for both input and output. The following languages are currently supported:

- `en`: English
- `sw`: Swahili
- `fr`: French
- `es`: Spanish

## Example Usage

### Example 1: Text Input in Swahili

```http
POST /records/
Content-Type: application/json

{
    "text": "Nina kuni 20 kilo ya machungwa kwa shilingi 5000",
    "language": "sw"
}
```

### Example 2: Audio Upload

```http
POST /records/
Content-Type: multipart/form-data

audio_file: your_audio_file.mp3
language: sw
```

### Example Response

```json
{
    "id": "123",
    "status": "COMPLETED",
    "response": "Uhusiano umebingwa kwa makini. Umepewa machungwa 20 kilo kwa shilingi 5000",
    "original_text": "Nina kuni 20 kilo ya machungwa kwa shilingi 5000",
    "analyzed_text": "I have 20 kilos of oranges for 5000 shillings",
    "product_name": "machungwa",
    "quantity": 20,
    "unit_price": "5000",
    "total_price": "100000",
    "missing_info": []
}
```

## Error Handling

The API includes comprehensive error handling that will:
1. Return appropriate error messages in the original language
2. Store error information in the database
3. Mark records with error status
4. Provide detailed error context in responses

## Security

- All endpoints are protected against CSRF attacks
- Input validation is performed on all requests
- Error messages are sanitized to prevent information leakage
- API keys are stored securely in environment variables
