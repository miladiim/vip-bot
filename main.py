from flask import Flask, request
import json, requests
import os

app = Flask(__name__)

TOKEN = "494613530:AAHQFmKNzgoehLf9i35mIPn1Z8WhtkrBZa4"
CHANNEL_ID = "https://t.me/+Bnko8vYkvcRkYjdk"
ZARINPAL_URL = "https://zarinp.al/634382"
DISCOUNT_CODE = "test50"

users = {}

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        return "ok"

    message = data.get("message")
    if not message:
        return "ok"

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return "ok"

    text = message.get("text", "")
    contact = message.get("contact")

    if text == "/start":
        keyboard = {
            "keyboard": [[{"text": "📱 ارسال شماره موبایل", "request_contact": True}]],
            "one_time_keyboard": True,
            "resize_keyboard": True
        }
        send_message(chat_id, "لطفاً شماره موبایل خود را ارسال کنید 👇", keyboard)
    elif contact:
        phone = contact.get("phone_number")
        if phone:
            users[str(chat_id)] = phone
            save_users()
            send_message(chat_id, f"شماره {phone} ثبت شد ✅\nکد تخفیف داری؟ بزن یا بفرست /skip", None)
        else:
            send_message(chat_id, "شماره موبایل پیدا نشد. لطفا دوباره ارسال کنید.", None)
    elif text.lower() == DISCOUNT_CODE:
        send_message(chat_id, f"✅ کد تخفیف '{text}' پذیرفته شد!\nبرای پرداخت روی لینک زیر بزن:\n{ZARINPAL_URL}", None)
    elif text == "/skip":
        send_message(chat_id, f"باشه!\nبرای پرداخت روی لینک زیر بزن:\n{ZARINPAL_URL}", None)
    else:
        send_message(chat_id, "دستور ناشناخته است. لطفاً /start بزنید.", None)

    return "ok"

def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if keyboard:
        payload["reply_markup"] = keyboard
    requests.post(url, json=payload)

def save_users():
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
