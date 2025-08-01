
from flask import Flask, request
import json, requests

app = Flask(__name__)

TOKEN = "توکن_ربات_اینجا"
CHANNEL_ID = "@کانال_شما"
ZARINPAL_URL = "https://zarinp.al/634382"
DISCOUNT_CODE = "test50"

users = {}

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        if text == "/start":
            keyboard = {
                "keyboard": [[{"text": "📱 ارسال شماره موبایل", "request_contact": True}]],
                "one_time_keyboard": True,
                "resize_keyboard": True
            }
            send_message(chat_id, "لطفاً شماره موبایل خود را ارسال کنید 👇", keyboard)
        elif "contact" in data["message"]:
            phone = data["message"]["contact"]["phone_number"]
            users[str(chat_id)] = phone
            save_users()
            send_message(chat_id, f"شماره {phone} ثبت شد ✅\nکد تخفیف داری؟ بزن یا بفرست /skip", None)
        elif text.lower() == DISCOUNT_CODE:
            send_message(chat_id, f"✅ کد تخفیف '{text}' پذیرفته شد!\nبرای پرداخت روی لینک زیر بزن:
{ZARINPAL_URL}", None)
        elif text == "/skip":
            send_message(chat_id, f"باشه!\nبرای پرداخت روی لینک زیر بزن:
{ZARINPAL_URL}", None)
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
        payload["reply_markup"] = json.dumps(keyboard)
    requests.post(url, data=payload)

def save_users():
    with open("data.json", "w") as f:
        json.dump(users, f)

if __name__ == "__main__":
    app.run()
