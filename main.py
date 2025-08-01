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

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return 'ok'

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn = telebot.types.KeyboardButton('📱 ارسال شماره موبایل', request_contact=True)
    markup.add(btn)
    bot.send_message(message.chat.id, "سلام 👋 لطفاً شماره موبایلت رو با دکمه زیر ارسال کن:", reply_markup=markup)

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

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

def load_users():
    global users
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        users = {}

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
        time.sleep(3600)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ شما اجازه دسترسی به این بخش را ندارید.")
        return

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📜 لیست کاربران", "✅ فعال‌سازی اشتراک")
    markup.add("⛔ حذف از کانال", "🔄 بررسی اعتبار")
    bot.send_message(message.chat.id, "🛠 پنل مدیریت:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📜 لیست کاربران")
def list_users(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not users:
        bot.send_message(message.chat.id, "❗ هیچ کاربری ثبت نشده.")
        return
    msg = "📋 لیست کاربران:\n\n"
    for uid, data in users.items():
        remain_days = max(0, 30 - (int(time.time()) - data['timestamp']) // 86400)
        msg += f"🧑‍💻 {uid} - 📱 {data['phone']} - ⏳ {remain_days} روز\n"
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == "✅ فعال‌سازی اشتراک")
def ask_user_for_activate(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "📌 لطفاً آیدی عددی یا شماره موبایل کاربر را ارسال کنید:")
    bot.register_next_step_handler(message, handle_activate_manual)

def handle_activate_manual(message):
    identifier = message.text.strip()
    if identifier in users:
        users[identifier]['timestamp'] = int(time.time())
        users[identifier]['active'] = True
        save_users()
        bot.send_message(int(identifier), "✅ اشتراک شما فعال شد.")
        bot.send_message(message.chat.id, "👌 کاربر با موفقیت فعال شد.")
    else:
        found = False
        for uid, data in users.items():
            if data['phone'] == identifier:
                users[uid]['timestamp'] = int(time.time())
                users[uid]['active'] = True
                save_users()
                bot.send_message(int(uid), "✅ اشتراک شما فعال شد.")
                bot.send_message(message.chat.id, "👌 کاربر با موفقیت فعال شد.")
                found = True
                break
        if not found:
            bot.send_message(message.chat.id, "❌ کاربر یافت نشد.")

@bot.message_handler(func=lambda m: m.text == "⛔ حذف از کانال")
def ask_user_for_removal(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "❗ لطفاً آیدی عددی یا شماره موبایل کاربر را ارسال کنید:")
    bot.register_next_step_handler(message, handle_manual_remove)

def handle_manual_remove(message):
    identifier = message.text.strip()
    if identifier in users:
        try:
            bot.kick_chat_member(CHANNEL_ID, int(identifier))
            users[identifier]['active'] = False
            save_users()
            bot.send_message(int(identifier), "⛔ اشتراک شما حذف شد و از کانال خارج شدید.")
            bot.send_message(message.chat.id, "✅ کاربر حذف شد.")
        except:
            bot.send_message(message.chat.id, "⚠ خطا در حذف کاربر.")
    else:
        found = False
        for uid, data in users.items():
            if data['phone'] == identifier:
                try:
                    bot.kick_chat_member(CHANNEL_ID, int(uid))
                    users[uid]['active'] = False
                    save_users()
                    bot.send_message(int(uid), "⛔ اشتراک شما حذف شد و از کانال خارج شدید.")
                    bot.send_message(message.chat.id, "✅ کاربر حذف شد.")
                    found = True
                    break
                except:
                    bot.send_message(message.chat.id, "⚠ خطا در حذف کاربر.")
        if not found:
            bot.send_message(message.chat.id, "❌ کاربر یافت نشد.")

@bot.message_handler(func=lambda m: m.text == "🔄 بررسی اعتبار")
def ask_user_for_check(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "📞 شماره موبایل یا آیدی عددی کاربر را ارسال کنید:")
    bot.register_next_step_handler(message, handle_check_subscription)

def handle_check_subscription(message):
    identifier = message.text.strip()
    uid = identifier if identifier in users else None
    if not uid:
        for k, v in users.items():
            if v.get("phone") == identifier:
                uid = k
                break
    if uid and uid in users:
        data = users[uid]
        remain = max(0, 30 - (int(time.time()) - data['timestamp']) // 86400)
        bot.send_message(message.chat.id, f"📱 {data['phone']}\n⏳ {remain} روز اعتبار دارد.")
    else:
        bot.send_message(message.chat.id, "❌ کاربر یافت نشد.")

if __name__ == '__main__':
    load_users()
    threading.Thread(target=check_expiry).start()
    app.run(host='0.0.0.0', port=10000)
