import requests
from django.conf import settings

def send_telegram_message(chat_id, text, reply_markup=None):
    token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    if reply_markup:
        data["reply_markup"] = reply_markup
        
    try:
        requests.post(url, json=data)
    except Exception as e:
        print(f"Telegram send error: {e}")