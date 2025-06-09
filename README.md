# Sme Backend API Documentation

This document provides detailed instructions for integrating the Sme Backend API with your Flutter application.

## API Endpoints

### Authentication

#### Register User
- **Endpoint**: `/api/register/`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "your_password",
    "first_name": "John",
    "last_name": "Doe"
  }
  ```
- **Response**:
  ```json
  {
    "message": "User registered successfully"
  }
  ```

#### Login
- **Endpoint**: `/api/login/`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "your_password"
  }
  ```
- **Response**:
  ```json
  {
    "refresh": "refresh_token_string",
    "access": "access_token_string"
  }
  ```

### Audio Processing
- **Endpoint**: `/api/audio/`
- **Method**: POST
- **Headers**:
  ```
  Authorization: Bearer <your_access_token>
  ```
- **Request Body**:
  ```json
  {
    "language": "swa"  // Supported languages: swa (Swahili)
  }
  ```
- **Request Files**:
  - `audio`: Audio file (max size: 10MB)
- **Response**:
  ```json
  {
    "transcription": "Transcribed text",
    "translation": "Translated text",
    "financial_records": [
      {
        "date": "2025-06-09",
        "amount": 10000,
        "description": "Description of transaction"
      }
    ]
  }
  ```

### Financial Records
- **Endpoint**: `/api/records/`
- **Method**: GET
- **Headers**:
  ```
  Authorization: Bearer <your_access_token>
  ```
- **Response**:
  ```json
  [
    {
      "id": 1,
      "date": "2025-06-09",
      "amount": 10000,
      "description": "Description of transaction"
    }
  ]
  ```

### User Sales
- **Endpoint**: `/api/user-sales/`
- **Method**: GET
- **Headers**:
  ```
  Authorization: Bearer <your_access_token>
  ```
- **Response**:
  ```json
  {
    "total_sales": 10000,
    "records": [
      {
        "date": "2025-06-09",
        "amount": 10000,
        "description": "Description of sale"
      }
    ]
  }
  ```

## Flutter Integration Guide

### 1. Add Dependencies
Add these dependencies to your `pubspec.yaml`:
```yaml
dependencies:
  http: ^1.1.0
  dio: ^5.3.0
  shared_preferences: ^2.2.0
```

### 2. API Client Setup
Create an API client class:
```dart
class ApiClient {
  static const String baseUrl = 'https://chapkat-backend.onrender.com';
  static String? _accessToken;

  static Future<void> setAccessToken(String token) async {
    _accessToken = token;
    await SharedPreferences.getInstance().then((prefs) => 
      prefs.setString('access_token', token)
    );
  }

  static Future<String?> getAccessToken() async {
    if (_accessToken == null) {
      final prefs = await SharedPreferences.getInstance();
      _accessToken = prefs.getString('access_token');
    }
    return _accessToken;
  }

  static Map<String, String> getHeaders() {
    final headers = {
      'Content-Type': 'application/json',
    };
    
    final token = _accessToken;
    if (token != null) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  static Future<Map<String, dynamic>> registerUser(Map<String, dynamic> userData) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/register/'),
      headers: getHeaders(),
      body: jsonEncode(userData),
    );
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/login/'),
      headers: getHeaders(),
      body: jsonEncode({'email': email, 'password': password}),
    );
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> processAudio(File audioFile, String language) async {
    final token = await getAccessToken();
    if (token == null) {
      throw Exception('No access token available');
    }

    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/api/audio/'),
    )
    ..headers.addAll({
      'Authorization': 'Bearer $token',
      'Content-Type': 'multipart/form-data',
    })
    ..fields['language'] = language
    ..files.add(
      await http.MultipartFile.fromPath(
        'audio',
        audioFile.path,
      ),
    );

    final response = await request.send();
    return jsonDecode(await response.stream.bytesToString());
  }
}
```

### 3. Usage Example

```dart
// Register a new user
final Map<String, dynamic> userData = {
  'email': 'user@example.com',
  'password': 'your_password',
  'first_name': 'John',
  'last_name': 'Doe',
};
final registerResponse = await ApiClient.registerUser(userData);

// Login and store token
final loginResponse = await ApiClient.login('user@example.com', 'your_password');
await ApiClient.setAccessToken(loginResponse['access']);

// Process audio file
final audioFile = File('path_to_audio_file.mp3');
final audioResponse = await ApiClient.processAudio(audioFile, 'swa');
```

### Error Handling

- **401 Unauthorized**: Invalid or expired token
- **400 Bad Request**: Invalid request data
- **429 Too Many Requests**: Maximum audio uploads reached (100 per user)
- **500 Internal Server Error**: Server processing error

### Rate Limits

- Maximum 100 audio uploads per user
- Audio file size limit: 10MB
- Supported languages: Swahili (swa)

## Security Notes

1. Always store tokens securely using SharedPreferences
2. Use HTTPS for all API requests
3. Implement proper error handling for network requests
4. Validate all API responses before using the data

## Error Codes

- **400**: Bad Request - Invalid request data
- **401**: Unauthorized - Invalid or missing token
- **403**: Forbidden - Insufficient permissions
- **404**: Not Found - Resource not found
- **429**: Too Many Requests - Rate limit exceeded
- **500**: Internal Server Error - Server processing error

## cURL Examples

### Register User
```bash
curl -X POST https://chapkat-backend.onrender.com/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Login
```bash
curl -X POST https://chapkat-backend.onrender.com/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password"
  }'
```

### Process Audio
```bash
# First, get your access token from login response
ACCESS_TOKEN="your_access_token_here"

curl -X POST https://chapkat-backend.onrender.com/api/audio/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "language=swa" \
  -F "audio=@/path/to/your/audio/file.mp3"
```

### Get Financial Records
```bash
# Using the same access token from login
curl -X GET https://chapkat-backend.onrender.com/api/records/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### Get User Sales
```bash
# Using the same access token from login
curl -X GET https://chapkat-backend.onrender.com/api/user-sales/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## PHP Examples

### Using cURL

```php
<?php
// Register User
$ch = curl_init();

curl_setopt_array($ch, [
    CURLOPT_URL => 'https://chapkat-backend.onrender.com/api/register/',
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode([
        'email' => 'user@example.com',
        'password' => 'your_password',
        'first_name' => 'John',
        'last_name' => 'Doe'
    ]),
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json'
    ]
]);

$response = curl_exec($ch);
$err = curl_error($ch);
curl_close($ch);

if ($err) {
    echo "cURL Error: " . $err;
} else {
    echo "Response: " . $response;
}
```

```php
<?php
// Login
$ch = curl_init();

curl_setopt_array($ch, [
    CURLOPT_URL => 'https://chapkat-backend.onrender.com/api/login/',
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode([
        'email' => 'user@example.com',
        'password' => 'your_password'
    ]),
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json'
    ]
]);

$response = curl_exec($ch);
$err = curl_error($ch);
curl_close($ch);

if ($err) {
    echo "cURL Error: " . $err;
} else {
    $result = json_decode($response, true);
    $accessToken = $result['access'];
    echo "Access Token: " . $accessToken;
}
```

```php
<?php
// Process Audio
$ch = curl_init();
$accessToken = 'your_access_token_here';
$audioFile = '/path/to/your/audio/file.mp3';

// Create multipart form data
$postData = [
    'language' => 'swa',
    'audio' => new CURLFile($audioFile)
];

curl_setopt_array($ch, [
    CURLOPT_URL => 'https://chapkat-backend.onrender.com/api/audio/',
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => $postData,
    CURLOPT_HTTPHEADER => [
        'Authorization: Bearer ' . $accessToken,
        'Content-Type: multipart/form-data'
    ]
]);

$response = curl_exec($ch);
$err = curl_error($ch);
curl_close($ch);

if ($err) {
    echo "cURL Error: " . $err;
} else {
    echo "Response: " . $response;
}
```

### Using Guzzle

```php
<?php
require 'vendor/autoload.php';
use GuzzleHttp\Client;
use GuzzleHttp\Psr7\MultipartStream;

// Register User
$client = new Client(['base_uri' => 'https://chapkat-backend.onrender.com']);

try {
    $response = $client->post('/api/register/', [
        'headers' => [
            'Content-Type' => 'application/json'
        ],
        'json' => [
            'email' => 'user@example.com',
            'password' => 'your_password',
            'first_name' => 'John',
            'last_name' => 'Doe'
        ]
    ]);
    
    echo "Response: " . $response->getBody();
} catch (Exception $e) {
    echo "Error: " . $e->getMessage();
}
```

```php
<?php
// Login
$client = new Client(['base_uri' => 'https://chapkat-backend.onrender.com']);

try {
    $response = $client->post('/api/login/', [
        'headers' => [
            'Content-Type' => 'application/json'
        ],
        'json' => [
            'email' => 'user@example.com',
            'password' => 'your_password'
        ]
    ]);
    
    $result = json_decode($response->getBody(), true);
    $accessToken = $result['access'];
    echo "Access Token: " . $accessToken;
} catch (Exception $e) {
    echo "Error: " . $e->getMessage();
}
```

```php
<?php
// Process Audio
$client = new Client(['base_uri' => 'https://chapkat-backend.onrender.com']);
$accessToken = 'your_access_token_here';
$audioFile = '/path/to/your/audio/file.mp3';

try {
    $response = $client->post('/api/audio/', [
        'headers' => [
            'Authorization' => 'Bearer ' . $accessToken
        ],
        'multipart' => [
            [
                'name' => 'language',
                'contents' => 'swa'
            ],
            [
                'name' => 'audio',
                'contents' => fopen($audioFile, 'r')
            ]
        ]
    ]);
    
    echo "Response: " . $response->getBody();
} catch (Exception $e) {
    echo "Error: " . $e->getMessage();
}
```

## Support

For any issues or questions, please contact the development team through the support channels provided.
