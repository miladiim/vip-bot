from flask import Flask, request
import json
import telebot
import time
import threading

API_TOKEN = '494613530:AAHQFmKNzgoehLf9i35mIPn1Z8WhtkrBZa4'
CHANNEL_ID = -1002891641618
CHANNEL_LINK = 'https://t.me/+Bnko8vYkvcRkYjdk'
ADMIN_ID = 368422936
ZARINPAL_URL = 'https://zarinp.al/634382'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

users = {}

def save_users():
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def load_users():
    global users
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except:
        users = {}

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return 'ok'

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    users[str(user_id)] = {
        'phone': phone,
        'timestamp': int(time.time()),
        'active': True
    }
    save_users()

    bot.send_message(ADMIN_ID, f"📥 کاربر جدید ثبت شد\nآیدی: {user_id}\nشماره: {phone}")

    # حذف کیبورد شماره موبایل و ارسال کیبورد تیکت به پشتیبانی
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn_ticket = telebot.types.KeyboardButton('🎫 تیکت به پشتیبانی')
    markup.add(btn_ticket)

    bot.send_message(message.chat.id, f"✅ شماره شما ثبت شد.\nبرای پرداخت، روی لینک زیر کلیک کنید:\n{ZARINPAL_URL}", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    users[str(user_id)] = {
        'phone': phone,
        'timestamp': int(time.time()),
        'active': True
    }
    save_users()

    bot.send_message(ADMIN_ID, f"📥 کاربر جدید ثبت شد\nآیدی: {user_id}\nشماره: {phone}")
    bot.send_message(message.chat.id, f"✅ شماره شما ثبت شد.\nبرای پرداخت، روی لینک زیر کلیک کنید:\n{ZARINPAL_URL}")

@bot.message_handler(func=lambda m: m.text == '🎫 تیکت به پشتیبانی')
def ask_support(message):
    bot.send_message(message.chat.id, "📝 لطفاً پیام خود را بنویسید و ارسال کنید.")
    bot.register_next_step_handler(message, forward_to_admin)

def forward_to_admin(message):
    bot.send_message(ADMIN_ID, f"📩 پیام از {message.from_user.id}:\n{message.text}")
    bot.send_message(message.chat.id, "✅ پیام شما ارسال شد. منتظر پاسخ باشید.")

def check_expiry():
    while True:
        now = int(time.time())
        for user_id, data in list(users.items()):
            if data.get('active') and now - data['timestamp'] > 30 * 86400:
                try:
                    bot.kick_chat_member(CHANNEL_ID, int(user_id))
                    bot.send_message(int(user_id), "⛔️ اشتراک شما به پایان رسیده و از کانال VIP حذف شدید.")
                except:
                    pass
                users[user_id]['active'] = False
                save_users()
        time.sleep(3600)  # Check every hour

if __name__ == '__main__':
    load_users()
    threading.Thread(target=check_expiry).start()
    app.run(host='0.0.0.0', port=10000)
