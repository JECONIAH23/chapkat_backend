import requests
import json
import os
from django.conf import settings
from users.models import FinancialRecord

def call_openrouter_and_parse(user, text, source_entry=None):
    prompt = f"""
You are a financial assistant. A user has just recorded this transaction using voice:
"{text}"

Please extract structured financial records from it in the following JSON format:
[
  {{
    "product_name": "string",
    "quantity": integer,
    "unit_price": float,
    "transaction_type": "Sold" or "Bought"
  }}
]

Only return valid JSON. Do not add any text or explanation.
"""

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "SME-Voice-App"
    }

    payload = {
        "model": "mistralai/devstral-small:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        data = response.json()
        reply = data["choices"][0]["message"]["content"]

        # Clean markdown-style code block
        reply = reply.strip()
        if reply.startswith("```json"):
            reply = reply.replace("```json", "").strip()
        if reply.endswith("```"):
            reply = reply[:-3].strip()

        records = json.loads(reply)

        saved = []
        for rec in records:
            saved.append(FinancialRecord.objects.create(
                user=user,
                product_name=rec["product_name"],
                quantity=rec["quantity"],
                unit_price=rec["unit_price"],
                total_price=rec["quantity"] * rec["unit_price"],
                source_text=source_entry
            ))
        return saved

    except Exception as e:
        print("LLM error:", e)
        return []
