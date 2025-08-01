from flask import Flask, request
import json
import telebot
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

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

def admin_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('📋 لیست کاربران', '🗑️ حذف اشتراک')
    markup.row('✅ فعال‌سازی اعتبار', '🔍 بررسی اعتبار')
    markup.row('📢 ارسال پیام همگانی', '❌ خروج')
    bot.send_message(message.chat.id, "لطفا یک گزینه را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id == ADMIN_ID:
        admin_menu(message)
    else:
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
        'active': False
    }
    save_users()
    bot.send_message(ADMIN_ID, f"📥 کاربر جدید ثبت شد\nآیدی: {user_id}\nشماره: {phone}")
    bot.send_message(message.chat.id, f"✅ شماره شما ثبت شد.\nبرای پرداخت، روی لینک زیر کلیک کنید:\n{ZARINPAL_URL}")

@bot.message_handler(func=lambda m: m.text == '🎫 تیکت به پشتیبانی')
def ask_support(message):
    bot.send_message(message.chat.id, "📝 لطفاً پیام خود را بنویسید و ارسال کنید.")
    bot.register_next_step_handler(message, forward_to_admin)

def forward_to_admin(message):
    user_id = message.from_user.id
    user_msg = message.text

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📤 پاسخ به این پیام", callback_data=f"reply_to:{user_id}"))

    bot.send_message(ADMIN_ID, f"📩 پیام از {user_id}:\n{user_msg}", reply_markup=markup)
    bot.send_message(message.chat.id, "✅ پیام شما ارسال شد. منتظر پاسخ باشید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_to:'))
def handle_reply_button(call):
    user_id = call.data.split(':')[1]
    msg = bot.send_message(call.message.chat.id, f"✏️ پاسخ خود را برای کاربر {user_id} بنویس:")
    bot.register_next_step_handler(msg, send_reply_message, user_id)

def send_reply_message(message, user_id):
    try:
        bot.send_message(int(user_id), f"📩 پاسخ پشتیبانی:\n\n{message.text}")
        bot.send_message(message.chat.id, "✅ پیام شما برای کاربر ارسال شد.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا در ارسال پیام: {e}")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_commands(message):
    text = message.text
    if text == '📋 لیست کاربران':
        if users:
            msg = "لیست کاربران:\n"
            for uid, data in users.items():
                active = "✅ فعال" if data.get('active') else "❌ غیرفعال"
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['timestamp']))
                msg += f"ID: {uid} - شماره: {data['phone']} - وضعیت: {active} - ثبت: {timestamp}\n"
        else:
            msg = "لیست کاربران خالی است."
        bot.send_message(message.chat.id, msg)

    elif text == '🗑️ حذف اشتراک':
        bot.send_message(message.chat.id, "لطفا آیدی عددی کاربر را برای حذف اشتراک ارسال کنید:")
        bot.register_next_step_handler(message, delete_subscription)

    elif text == '✅ فعال‌سازی اعتبار':
        bot.send_message(message.chat.id, "لطفا آیدی عددی کاربر را برای فعال‌سازی ارسال کنید:")
        bot.register_next_step_handler(message, activate_subscription)

    elif text == '🔍 بررسی اعتبار':
        bot.send_message(message.chat.id, "لطفا آیدی عددی کاربر را برای بررسی اعتبار ارسال کنید:")
        bot.register_next_step_handler(message, check_subscription)

    elif text == '📢 ارسال پیام همگانی':
        bot.send_message(message.chat.id, "متن پیام همگانی را ارسال کنید:")
        bot.register_next_step_handler(message, broadcast_message)

    elif text == '❌ خروج':
        bot.send_message(message.chat.id, "خروج از پنل مدیریت انجام شد.")
        bot.send_message(message.chat.id, "برای شروع مجدد /start را بزنید.")
        
    else:
        bot.send_message(message.chat.id, "دستور نامعتبر است. لطفا یکی از گزینه‌ها را انتخاب کنید.")
        admin_menu(message)

def delete_subscription(message):
    uid = message.text.strip()
    if uid in users:
        try:
            bot.kick_chat_member(CHANNEL_ID, int(uid))
        except Exception as e:
            bot.send_message(ADMIN_ID, f"خطا در حذف از کانال: {e}")
        users[uid]['active'] = False
        save_users()
        bot.send_message(ADMIN_ID, f"اشتراک کاربر {uid} حذف شد.")
    else:
        bot.send_message(ADMIN_ID, "کاربر یافت نشد.")
    admin_menu(message)

def activate_subscription(message):
    uid = message.text.strip()
    if uid in users:
        users[uid]['active'] = True
        users[uid]['timestamp'] = int(time.time())
        save_users()
        try:
            bot.unban_chat_member(CHANNEL_ID, int(uid))
            bot.send_message(int(uid), f"اشتراک شما فعال شد.\nبرای ورود به کانال VIP روی دکمه زیر بزنید.", 
                             reply_markup=telebot.types.InlineKeyboardMarkup().add(
                                 telebot.types.InlineKeyboardButton("ورود به کانال VIP", url=CHANNEL_LINK)
                             ))
        except Exception as e:
            bot.send_message(ADMIN_ID, f"خطا در ارسال لینک کانال: {e}")
        bot.send_message(ADMIN_ID, f"اشتراک کاربر {uid} فعال شد و لینک کانال ارسال شد.")
    else:
        bot.send_message(ADMIN_ID, "کاربر یافت نشد.")
    admin_menu(message)

def check_subscription(message):
    uid = message.text.strip()
    if uid in users:
        active = users[uid].get('active', False)
        timestamp = users[uid]['timestamp']
        days_passed = (int(time.time()) - timestamp) // 86400
        remaining = max(0, 30 - days_passed)
        status = "فعال" if active else "غیرفعال"
        bot.send_message(ADMIN_ID, f"کاربر {uid}\nوضعیت اشتراک: {status}\nروزهای باقی‌مانده: {remaining}")
    else:
        bot.send_message(ADMIN_ID, "کاربر یافت نشد.")
    admin_menu(message)

def broadcast_message(message):
    text = message.text
    count = 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 پیام همگانی:\n\n{text}")
            count += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"پیام به {count} کاربر ارسال شد.")
    admin_menu(message)

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
            elif data.get('active') and 30 * 86400 - (now - data['timestamp']) <= 86400:
                try:
                    bot.send_message(int(user_id), "⏳ اشتراک شما فردا به پایان می‌رسد. لطفا برای تمدید اقدام کنید.")
                except:
                    pass
        time.sleep(3600)

if __name__ == '__main__':
    load_users()
    threading.Thread(target=check_expiry, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
