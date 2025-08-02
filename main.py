from flask import Flask, request
import telebot
import time
import threading
import json
from pymongo import MongoClient

# ==== اطلاعات شخصی ====
API_TOKEN = '494613530:AAHQFmKNzgoehLf9i35mIPn1Z8WhtkrBZa4'
CHANNEL_ID = -1002891641618
CHANNEL_LINK = 'https://t.me/+Bnko8vYkvcRkYjdk'
ADMIN_ID = 368422936
ZARINPAL_URL = 'https://zarinp.al/634382'

# ==== MongoDB Atlas ====
client = MongoClient("mongodb+srv://vipadmin:milad137555@cluster0.g6mqucj.mongodb.net")
db = client["vip_bot"]
users_collection = db["users"]
tickets_collection = db["tickets"]

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return 'ok'

# ارسال منوی اصلی فارسی
def send_main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('💳 پرداخت'), telebot.types.KeyboardButton('🎫 تیکت به پشتیبانی'))
    bot.send_message(chat_id, "📋 منوی اصلی:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user = users_collection.find_one({"_id": user_id})

    if user and "phone" in user:
        send_main_menu(chat_id)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn = telebot.types.KeyboardButton('📱 ارسال شماره موبایل', request_contact=True)
        markup.add(btn)
        bot.send_message(chat_id, "سلام 👋 لطفاً شماره موبایلت رو با دکمه زیر ارسال کن:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number

    users_collection.update_one(
        {"_id": user_id},
        {"$set": {"phone": phone, "timestamp": int(time.time()), "active": False}},
        upsert=True
    )

    bot.send_message(ADMIN_ID, f"""📥 کاربر جدید ثبت شد
آیدی: {user_id}
شماره: {phone}""")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('💳 پرداخت'), telebot.types.KeyboardButton('🎫 تیکت به پشتیبانی'))
    bot.send_message(message.chat.id, f"✅ شماره شما ثبت شد.\n\nتا دو دقیقه دیگر این پیام حذف می‌شود.\n\nبرای پرداخت، روی لینک زیر کلیک کنید:\n{ZARINPAL_URL}", reply_markup=markup)

    # حذف پیام پس از 120 ثانیه
    def delete_message_later(chat_id, message_id):
        time.sleep(120)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass

    threading.Thread(target=delete_message_later, args=(message.chat.id, message.message_id)).start()

@bot.message_handler(func=lambda m: m.text == '💳 پرداخت')
def payment_link(message):
    bot.send_message(message.chat.id, f"💳 برای پرداخت، روی لینک زیر کلیک کنید:\n{ZARINPAL_URL}")

@bot.message_handler(func=lambda m: m.text == '🎫 تیکت به پشتیبانی')
def ask_support(message):
    bot.send_message(message.chat.id, "📝 لطفاً پیام خود را بنویسید و ارسال کنید.")
    bot.register_next_step_handler(message, forward_to_admin)

def forward_to_admin(message):
    tickets_collection.insert_one({
        "user_id": message.from_user.id,
        "text": message.text,
        "timestamp": int(time.time())
    })
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("💬 پاسخ خصوصی", callback_data=f"reply_{message.from_user.id}"))
    bot.send_message(ADMIN_ID, f"📩 پیام از {message.from_user.id}:\n{message.text}", reply_markup=markup)
    bot.send_message(message.chat.id, "✅ پیام شما ارسال شد. منتظر پاسخ باشید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def handle_admin_reply(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "شما دسترسی ندارید.")
        return
    user_id = int(call.data.split('_')[1])
    bot.send_message(ADMIN_ID, "پیام پاسخ خود را ارسال کنید:")
    bot.register_next_step_handler_by_chat_id(ADMIN_ID, lambda msg: send_private_reply(msg, user_id))

def send_private_reply(message, user_id):
    try:
        bot.send_message(user_id, f"📩 پاسخ پشتیبانی:\n{message.text}")
        bot.send_message(ADMIN_ID, "✅ پاسخ با موفقیت ارسال شد.")
    except:
        bot.send_message(ADMIN_ID, "❗️خطا در ارسال پاسخ.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📋 لیست کاربران", callback_data='list_users'))
    markup.add(telebot.types.InlineKeyboardButton("🟢 فعال‌سازی دستی", callback_data='confirm_user'))
    markup.add(telebot.types.InlineKeyboardButton("❌ حذف اشتراک", callback_data='remove_user'))
    markup.add(telebot.types.InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data='broadcast'))
    bot.send_message(message.chat.id, "🛠 پنل مدیریت:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "list_users":
        users = users_collection.find()
        text = "📋 لیست کاربران:\n"
        for u in users:
            phone = u.get("phone", "-")
            active = "✅" if u.get("active") else "❌"
            text += f"{u['_id']} | {phone} | {active}\n"
        bot.send_message(ADMIN_ID, text or "❗️کاربری یافت نشد.")
    elif call.data == "confirm_user":
        bot.send_message(ADMIN_ID, "لطفاً آیدی عددی کاربر را بفرستید تا فعال شود.")
        bot.register_next_step_handler(call.message, confirm_user_step)
    elif call.data == "remove_user":
        bot.send_message(ADMIN_ID, "آیدی عددی کاربر برای حذف را بفرستید:")
        bot.register_next_step_handler(call.message, remove_user_step)
    elif call.data == "broadcast":
        bot.send_message(ADMIN_ID, "پیامی که باید به همه ارسال شود را بفرستید:")
        bot.register_next_step_handler(call.message, broadcast_step)

def confirm_user_step(message):
    try:
        user_id = int(message.text)
        users_collection.update_one({"_id": user_id}, {"$set": {"active": True, "timestamp": int(time.time())}})
        bot.send_message(user_id, f"✅ اشتراک شما فعال شد.\n\n📥 [عضویت در کانال VIP]({CHANNEL_LINK})", parse_mode='Markdown')
        bot.send_message(ADMIN_ID, "✅ کاربر با موفقیت فعال شد.")
    except:
        bot.send_message(ADMIN_ID, "❗️ خطا در فعال‌سازی.")

def remove_user_step(message):
    try:
        user_id = int(message.text)
        users_collection.update_one({"_id": user_id}, {"$set": {"active": False}})
        bot.send_message(user_id, "⛔️ اشتراک شما غیرفعال شد.")
        bot.send_message(ADMIN_ID, "✅ اشتراک کاربر حذف شد.")
    except:
        bot.send_message(ADMIN_ID, "❗️ خطا در حذف.")

def broadcast_step(message):
    text = message.text
    users = users_collection.find()
    count = 0
    for u in users:
        try:
            bot.send_message(u['_id'], text)
            count += 1
        except:
            continue
    bot.send_message(ADMIN_ID, f"📤 پیام به {count} کاربر ارسال شد.")

def check_expiry():
    while True:
        now = int(time.time())
        users = users_collection.find({"active": True})
        for user in users:
            if now - user['timestamp'] > 30 * 86400:
                try:
                    bot.kick_chat_member(CHANNEL_ID, user['_id'])
                    bot.send_message(user['_id'], "⛔️ اشتراک شما به پایان رسیده و از کانال VIP حذف شدید.")
                except:
                    pass
                users_collection.update_one({"_id": user['_id']}, {"$set": {"active": False}})
        time.sleep(3600)

if __name__ == '__main__':
    threading
