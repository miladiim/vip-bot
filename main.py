from flask import Flask, request
import telebot
import time
import threading
import pymongo
import pytz

# --- تنظیمات ---
API_TOKEN = '494613530:AAHQFmKNzgoehLf9i35mIPn1Z8WhtkrBZa4'
CHANNEL_ID = -1002891641618
CHANNEL_LINK = 'https://t.me/+Bnko8vYkvcRkYjdk'
ADMIN_ID = 368422936
ZARINPAL_URL = 'https://zarinp.al/634382'
MONGO_URI = 'mongodb+srv://vipadmin:milad137555@cluster0.g6mqucj.mongodb.net/?retryWrites=true&w=majority'

# --- اتصال به MongoDB ---
client = pymongo.MongoClient(MONGO_URI)
db = client['vip_bot']
users_col = db['users']

# --- ربات و اپلیکیشن وب ---
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return '✅ Bot is Running'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return 'OK'

# --- شروع ربات ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user = users_col.find_one({'_id': user_id})
    
    if user and user.get('phone'):
        # اگر قبلاً شماره داده، دکمه تیکت نشون بده
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton('🎫 تیکت به پشتیبانی'))
        bot.send_message(user_id, "✅ شماره شما قبلاً ثبت شده است.", reply_markup=markup)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        btn = telebot.types.KeyboardButton('📱 ارسال شماره موبایل', request_contact=True)
        markup.add(btn)
        bot.send_message(user_id, "سلام 👋 لطفاً شماره موبایلت رو با دکمه زیر ارسال کن:", reply_markup=markup)

# --- ذخیره شماره موبایل ---
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number

    users_col.update_one(
        {'_id': user_id},
        {
            '$set': {
                'phone': phone,
                'timestamp': int(time.time()),
                'active': True
            }
        },
        upsert=True
    )

    # ارسال به ادمین
    bot.send_message(ADMIN_ID, f"📥 کاربر جدید ثبت شد\nآیدی: {user_id}\nشماره: {phone}")

    # نمایش دکمه تیکت
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('🎫 تیکت به پشتیبانی'))

    bot.send_message(user_id, f"✅ شماره شما ثبت شد.\nبرای پرداخت، روی لینک زیر کلیک کنید:\n{ZARINPAL_URL}", reply_markup=markup)

# --- تیکت پشتیبانی ---
@bot.message_handler(func=lambda m: m.text == '🎫 تیکت به پشتیبانی')
def ask_support(message):
    bot.send_message(message.chat.id, "📝 لطفاً پیام خود را بنویسید و ارسال کنید.")
    bot.register_next_step_handler(message, forward_to_admin)

def forward_to_admin(message):
    bot.send_message(ADMIN_ID, f"📩 پیام از {message.from_user.id}:\n{message.text}")
    bot.send_message(message.chat.id, "✅ پیام شما ارسال شد. منتظر پاسخ باشید.")

# --- چک انقضای اشتراک ---
def check_expiry():
    while True:
        now = int(time.time())
        for user in users_col.find({'active': True}):
            user_id = user['_id']
            join_time = user.get('timestamp', 0)
            if now - join_time > 30 * 86400:
                try:
                    bot.ban_chat_member(CHANNEL_ID, user_id)
                    bot.send_message(user_id, "⛔️ اشتراک شما به پایان رسیده و از کانال VIP حذف شدید.")
                except:
                    pass
                users_col.update_one({'_id': user_id}, {'$set': {'active': False}})
        time.sleep(3600)  # هر یک ساعت بررسی

# --- اجرای Flask و ترد جداگانه بررسی انقضا ---
if __name__ == '__main__':
    threading.Thread(target=check_expiry).start()
    app.run(host='0.0.0.0', port=10000)
