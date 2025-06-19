import openai
from googletrans import Translator
from django.conf import settings
import json
from datetime import datetime

# Initialize OpenAI client
openai.api_key = settings.OPENROUTER_API_KEY

# Initialize Google Translator
translator = Translator()

def translate_text(text, target_lang='en'):
    """Translate text to target language"""
    try:
        translation = translator.translate(text, dest=target_lang)
        return translation.text
    except Exception as e:
        raise Exception(f"Translation failed: {str(e)}")

def analyze_business_transaction(text):
    """Analyze text for business transaction information using OpenAI"""
    try:
        # Define the system prompt
        system_prompt = """
        You are a business transaction analyzer. Extract the following information from the text:
        - Product name
        - Quantity
        - Unit price
        - Total price
        
        Return the information in JSON format with these fields:
        {
            "product_name": "",
            "quantity": null,
            "unit_price": null,
            "total_price": null,
            "missing_info": []
        }
        
        If any information is missing, add it to the missing_info array.
        """

        # Create the chat completion
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        )

        # Parse the response
        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        raise Exception(f"AI analysis failed: {str(e)}")

def format_response(transaction_data, original_language):
    """Format the response in original language"""
    try:
        # Create response message based on transaction status
        if transaction_data.get('status') == 'COMPLETED':
            response_text = f"Transaction completed successfully:\n"
            response_text += f"Product: {transaction_data['product_name']}\n"
            response_text += f"Quantity: {transaction_data['quantity']}\n"
            response_text += f"Unit Price: {transaction_data['unit_price']}\n"
            response_text += f"Total: {transaction_data['total_price']}"
        else:
            response_text = "Transaction could not be completed. Missing information:\n"
            for info in transaction_data.get('missing_info', []):
                response_text += f"- {info}\n"

        # Translate response back to original language
        translated_response = translate_text(response_text, target_lang=original_language)
        return translated_response

    except Exception as e:
        raise Exception(f"Response formatting failed: {str(e)}")
