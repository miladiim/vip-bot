import telebot
from telebot import types
from flask import Flask, request
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz
import threading
import time
import os

# --- تنظیمات اصلی ---
TOKEN = '494613530:AAHQFmKNzgoehLf9i35mIPn1Z8WhtkrBZa4'
ADMIN_ID = 368422936
CHANNEL_ID = -1002891641618
CHANNEL_LINK = 'https://t.me/+Bnko8vYkvcRkYjdk'
ZARINPAL_URL = 'https://zarinp.al/634382'

# --- MongoDB Atlas ---
client = MongoClient("mongodb+srv://vipadmin:milad137555@cluster0.g6mqucj.mongodb.net")
db = client["vip_bot"]
users_collection = db["users"]
tickets_collection = db["tickets"]

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
app = Flask(__name__)

# --- حذف پیام بعد از 2 دقیقه ---
def delete_message_later(chat_id, message_id, delay=120):
    def job():
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Timer(delay, job).start()

# --- /start ---
@bot.message_handler(commands=['start'])
def start(message):
    user = users_collection.find_one({"user_id": message.from_user.id})
    if not user:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn = types.KeyboardButton("📱 ارسال شماره", request_contact=True)
        markup.add(btn)
        bot.send_message(message.chat.id, "👋 سلام! لطفاً شماره موبایل خود را ارسال کنید:", reply_markup=markup)
    else:
        send_main_menu(message.chat.id)

# --- ثبت شماره تلفن ---
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    phone = message.contact.phone_number
    users_collection.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"phone": phone, "user_id": message.from_user.id, "registered_at": datetime.utcnow()}},
        upsert=True
    )
    bot.send_message(message.chat.id, "✅ شماره شما ثبت شد.")
    send_main_menu(message.chat.id)

# --- منوی اصلی ---
def send_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💳 خرید عضویت VIP", "📢 لینک کانال VIP")
    markup.add("🎫 تیکت به پشتیبانی")
    bot.send_message(chat_id, "منوی اصلی:", reply_markup=markup)

# --- خرید عضویت VIP ---
@bot.message_handler(func=lambda m: m.text == "💳 خرید عضویت VIP")
def buy_vip(message):
    bot.send_message(message.chat.id, f"برای خرید، روی لینک زیر کلیک کنید:\n{ZARINPAL_URL}")

# --- لینک کانال VIP ---
@bot.message_handler(func=lambda m: m.text == "📢 لینک کانال VIP")
def send_channel(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌟 ورود به کانال", url=CHANNEL_LINK))
    bot.send_message(message.chat.id, "برای ورود به کانال VIP، روی دکمه زیر کلیک کنید:", reply_markup=markup)

# --- تیکت پشتیبانی ---
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

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 پاسخ به کاربر", callback_data=f"reply_{message.from_user.id}"))

    sent = bot.send_message(
        ADMIN_ID,
        f"📩 پیام از {message.from_user.id}:\n{message.text}\n\n🔗 کانال VIP:",
        reply_markup=markup
    )

    # لینک کانال به‌صورت شیشه‌ای
    channel_button = types.InlineKeyboardMarkup()
    channel_button.add(types.InlineKeyboardButton("🌟 کانال VIP", url=CHANNEL_LINK))
    bot.send_message(ADMIN_ID, "لینک کانال:", reply_markup=channel_button)

    # حذف بعد از ۲ دقیقه
    delete_message_later(ADMIN_ID, sent.message_id, 120)

# --- پاسخ به کاربر توسط ادمین ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_"))
def callback_reply(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ دسترسی ندارید")
        return

    user_id = int(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "🛠 لطفاً پیام خود را برای پاسخ به کاربر ارسال کنید.")
    bot.send_message(ADMIN_ID, f"📝 لطفاً پیام خود را برای پاسخ به کاربر {user_id} بنویسید:")

    bot.register_next_step_handler_by_chat_id(ADMIN_ID, lambda msg: send_reply_to_user(msg, user_id))

def send_reply_to_user(message, user_id):
    try:
        bot.send_message(user_id, f"📩 پاسخ ادمین:\n{message.text}")
        bot.send_message(ADMIN_ID, "✅ پیام شما برای کاربر ارسال شد.")
    except:
        bot.send_message(ADMIN_ID, "❗️ ارسال پیام به کاربر ناموفق بود.")

# --- وبهوک Flask ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است."

# --- راه‌اندازی وبهوک ---
if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url="https://vip-bot-s9p9.onrender.com/" + TOKEN)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
