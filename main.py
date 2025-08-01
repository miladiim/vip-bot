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
        time.sleep(3600)  # Check every hour

# ===== دستورات جدید ادمین =====

@bot.message_handler(commands=['remove'])
def remove_user(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ شما اجازه این دستور را ندارید.")
        return
    
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "❗️ لطفاً دستور را به صورت زیر وارد کنید:\n/remove USER_ID یا /remove PHONE_NUMBER")
        return
    
    identifier = args[1]
    user_id_to_remove = None
    
    # اول تلاش می‌کنیم با آیدی تلگرام پیدا کنیم
    if identifier.isdigit():
        # اگر به عنوان آیدی بود
        if identifier in users:
            user_id_to_remove = identifier
        else:
            # جستجو بر اساس شماره موبایل
            for uid, data in users.items():
                if data.get('phone') == identifier:
                    user_id_to_remove = uid
                    break
    
    if not user_id_to_remove:
        bot.reply_to(message, "❗️ کاربر یافت نشد.")
        return
    
    try:
        bot.kick_chat_member(CHANNEL_ID, int(user_id_to_remove))
        users[user_id_to_remove]['active'] = False
        save_users()
        bot.reply_to(message, f"✅ کاربر با آیدی {user_id_to_remove} از کانال حذف شد.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا در حذف کاربر: {e}")



@bot.message_handler(commands=['status'])
def check_status(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ شما اجازه این دستور را ندارید.")
        return
    
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "❗️ لطفاً دستور را به صورت زیر وارد کنید:\n/status USER_ID یا /status PHONE_NUMBER")
        return
    
    identifier = args[1]
    user_id_to_check = None
    
    if identifier.isdigit():
        if identifier in users:
            user_id_to_check = identifier
        else:
            for uid, data in users.items():
                if data.get('phone') == identifier:
                    user_id_to_check = uid
                    break
    
    if not user_id_to_check:
        bot.reply_to(message, "❗️ کاربر یافت نشد.")
        return
    
    data = users[user_id_to_check]
    timestamp = data.get('timestamp')
    if not timestamp:
        bot.reply_to(message, "❗️ اطلاعات اشتراک این کاربر ناقص است.")
        return
    
    now = int(time.time())
    days_passed = (now - timestamp) // 86400
    days_left = 30 - days_passed
    if days_left < 0:
        days_left = 0
    
    active = data.get('active', False)
    status_text = "فعال" if active else "غیرفعال"
    
    bot.reply_to(message,
                 f"وضعیت اشتراک کاربر:\nآیدی: {user_id_to_check}\nشماره: {data.get('phone')}\nوضعیت: {status_text}\nروزهای باقی‌مانده: {days_left} روز")
@bot.message_handler(commands=['activate'])
def activate_user(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ شما اجازه این دستور را ندارید.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "❗️ لطفاً دستور را به صورت زیر وارد کنید:\n/activate USER_ID یا /activate PHONE_NUMBER")
        return

    identifier = args[1]
    user_id_to_activate = None

    if identifier.isdigit():
        if identifier in users:
            user_id_to_activate = identifier
        else:
            for uid, data in users.items():
                if data.get('phone') == identifier:
                    user_id_to_activate = uid
                    break

    if not user_id_to_activate:
        bot.reply_to(message, "❗️ کاربر یافت نشد.")
        return

    try:
        bot.unban_chat_member(CHANNEL_ID, int(user_id_to_activate))  # برای اطمینان از اینکه عضو بشه
        users[user_id_to_activate]['active'] = True
        users[user_id_to_activate]['timestamp'] = int(time.time())
        save_users()
        bot.send_message(int(user_id_to_activate),
                         f"✅ اشتراک شما فعال شد! برای عضویت وارد کانال زیر شوید:\n{CHANNEL_LINK}")
        bot.reply_to(message, f"✅ کاربر {user_id_to_activate} با موفقیت فعال شد.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا در فعال‌سازی کاربر: {e}")

if __name__ == '__main__':
    load_users()
    threading.Thread(target=check_expiry).start()
    app.run(host='0.0.0.0', port=10000)
