import telebot
import json
import time

API_TOKEN = 'توکن_تو'
CHANNEL_ID = -1002891641618
ADMIN_ID = 368422936
CHANNEL_LINK = "https://t.me/+Bnko8vYkvcRkYjdk"  # لینک کانال به صورت شیشه‌ای
ZARINPAL_URL = 'https://zarinp.al/634382'

bot = telebot.TeleBot(API_TOKEN)
users = {}

# --- بارگذاری کاربران از فایل ---
def load_users():
    global users
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        users = {}

# --- ذخیره کاربران در فایل ---
def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

# --- ارسال منوی ادمین فارسی ---
def admin_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("لیست کاربران", "فعال سازی اشتراک")
    markup.row("حذف اشتراک", "بررسی اعتبار")
    markup.row("ارسال پیام همگانی")
    bot.send_message(chat_id, "📋 منوی مدیریت ربات:", reply_markup=markup)

# --- استارت ربات ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn = telebot.types.KeyboardButton('📱 ارسال شماره موبایل', request_contact=True)
    markup.add(btn)
    bot.send_message(message.chat.id, "سلام! لطفاً شماره موبایل خود را ارسال کنید:", reply_markup=markup)

# --- دریافت شماره موبایل ---
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = str(message.from_user.id)
    phone = message.contact.phone_number
    users[user_id] = {
        "phone": phone,
        "timestamp": int(time.time()),
        "active": False  # پیش فرض غیرفعال
    }
    save_users()
    bot.send_message(ADMIN_ID, f"کاربر جدید ثبت شد:\nآیدی: {user_id}\nشماره: {phone}")
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("🎫 تیکت به پشتیبانی"))
    bot.send_message(message.chat.id, "✅ شماره شما ثبت شد. منتظر تایید اشتراک باشید.", reply_markup=markup)

# --- منوی ادمین فارسی ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        admin_menu(message.chat.id)
    else:
        bot.send_message(message.chat.id, "شما دسترسی مدیریت ندارید.")

# --- پردازش دستورات ادمین ---
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
def admin_commands(message):
    text = message.text
    if text == "لیست کاربران":
        if not users:
            bot.send_message(ADMIN_ID, "هیچ کاربری ثبت نشده است.")
            return
        msg = "لیست کاربران:\n"
        for uid, data in users.items():
            status = "فعال" if data.get("active") else "غیرفعال"
            msg += f"آیدی: {uid} | شماره: {data['phone']} | وضعیت: {status}\n"
        bot.send_message(ADMIN_ID, msg)

    elif text == "فعال سازی اشتراک":
        bot.send_message(ADMIN_ID, "لطفاً آیدی عددی کاربر را ارسال کنید تا اشتراک فعال شود.")
        bot.register_next_step_handler(message, activate_subscription)

    elif text == "حذف اشتراک":
        bot.send_message(ADMIN_ID, "لطفاً آیدی عددی کاربر را ارسال کنید تا اشتراک حذف شود.")
        bot.register_next_step_handler(message, deactivate_subscription)

    elif text == "بررسی اعتبار":
        bot.send_message(ADMIN_ID, "لطفاً آیدی عددی کاربر را ارسال کنید برای بررسی اعتبار.")
        bot.register_next_step_handler(message, check_subscription)

    elif text == "ارسال پیام همگانی":
        bot.send_message(ADMIN_ID, "متن پیام همگانی را ارسال کنید:")
        bot.register_next_step_handler(message, broadcast_message)

# --- فعال سازی اشتراک و ارسال لینک شیشه‌ای ---
def activate_subscription(message):
    user_id = message.text.strip()
    if user_id not in users:
        bot.send_message(ADMIN_ID, "کاربر یافت نشد!")
        return
    users[user_id]["active"] = True
    users[user_id]["timestamp"] = int(time.time())
    save_users()

    try:
        # افزودن به کانال (اگر لازم بود)
        bot.unban_chat_member(CHANNEL_ID, int(user_id))
    except:
        pass

    # ارسال پیام با لینک شیشه‌ای (Inline Keyboard)
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton(text="عضویت در کانال VIP", url=CHANNEL_LINK)
    markup.add(btn)
    bot.send_message(int(user_id), "✅ اشتراک شما فعال شد. لطفاً روی دکمه زیر برای عضویت در کانال کلیک کنید:", reply_markup=markup)
    bot.send_message(ADMIN_ID, f"اشتراک کاربر {user_id} فعال شد.")

# --- حذف اشتراک و حذف کاربر از کانال ---
def deactivate_subscription(message):
    user_id = message.text.strip()
    if user_id not in users:
        bot.send_message(ADMIN_ID, "کاربر یافت نشد!")
        return
    users[user_id]["active"] = False
    save_users()

    try:
        bot.kick_chat_member(CHANNEL_ID, int(user_id))
        bot.send_message(int(user_id), "⛔️ اشتراک شما لغو و از کانال حذف شدید.")
    except:
        pass
    bot.send_message(ADMIN_ID, f"اشتراک کاربر {user_id} حذف شد.")

# --- بررسی اعتبار اشتراک ---
def check_subscription(message):
    user_id = message.text.strip()
    if user_id not in users:
        bot.send_message(ADMIN_ID, "کاربر یافت نشد!")
        return
    active = users[user_id].get("active", False)
    if active:
        ts = users[user_id].get("timestamp", 0)
        remain = 30*86400 - (int(time.time()) - ts)
        days = remain // 86400
        bot.send_message(ADMIN_ID, f"کاربر {user_id} فعال است.\nمدت باقی‌مانده: {days} روز")
    else:
        bot.send_message(ADMIN_ID, f"کاربر {user_id} فعال نیست.")

# --- ارسال پیام همگانی ---
def broadcast_message(message):
    text = message.text
    count = 0
    for uid, data in users.items():
        if data.get("active"):
            try:
                bot.send_message(int(uid), text)
                count += 1
            except:
                pass
    bot.send_message(ADMIN_ID, f"پیام به {count} کاربر ارسال شد.")

# --- تیکت به پشتیبانی ---
@bot.message_handler(func=lambda m: m.text == "🎫 تیکت به پشتیبانی")
def ticket_support(message):
    bot.send_message(message.chat.id, "📝 لطفاً پیام خود را بنویسید:")
    bot.register_next_step_handler(message, forward_to_admin)

def forward_to_admin(message):
    bot.send_message(ADMIN_ID, f"پیام پشتیبانی از {message.from_user.id}:\n{message.text}")
    bot.send_message(message.chat.id, "✅ پیام شما ارسال شد. منتظر پاسخ باشید.")

# --- چک کردن خودکار انقضا اشتراک هر ساعت ---
def check_expiry():
    while True:
        now = int(time.time())
        for uid, data in list(users.items()):
            if data.get("active") and now - data["timestamp"] > 30 * 86400:
                try:
                    bot.kick_chat_member(CHANNEL_ID, int(uid))
                    bot.send_message(int(uid), "⛔️ اشتراک شما منقضی شده و از کانال حذف شدید.")
                except:
                    pass
                users[uid]["active"] = False
                save_users()
        time.sleep(3600)

import threading
import time

if __name__ == '__main__':
    load_users()
    threading.Thread(target=check_expiry, daemon=True).start()
    bot.infinity_polling()
