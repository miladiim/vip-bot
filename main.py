import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from pymongo import MongoClient
from datetime import datetime
import pytz

# ---------- اطلاعات ربات ----------
BOT_TOKEN = "494613530:AAHQFmKNzgoehLf9i35mIPn1Z8WhtkrBZa4"
ADMIN_ID = 368422936
CHANNEL_ID = -1002891641618
CHANNEL_LINK = "https://t.me/+Bnko8vYkvcRkYjdk"
ZARINPAL_LINK = "https://zarinp.al/634382"

# ---------- اتصال به MongoDB Atlas ----------
client = MongoClient("mongodb+srv://vipadmin:milad137555@cluster0.g6mqucj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["vip_bot"]
users_col = db["users"]
tickets_col = db["tickets"]

# ---------- راه‌اندازی لاگ ----------
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# ---------- توابع ----------

def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = users_col.find_one({"user_id": user_id})
    if user and user.get("phone"):
        update.message.reply_text("شماره شما قبلاً ثبت شده است. اگر نیاز دارید، از دکمه‌های موجود استفاده کنید.")
    else:
        keyboard = [[KeyboardButton("ارسال شماره موبایل", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text("برای ادامه لطفاً شماره موبایل خود را ارسال کنید:", reply_markup=reply_markup)

def remove_channel_button(context: CallbackContext):
    job = context.job
    chat_id = job.context["chat_id"]
    message_id = job.context["message_id"]
    try:
        context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
        logging.info(f"دکمه کانال از پیام {message_id} حذف شد")
    except Exception as e:
        logging.error(f"خطا در حذف دکمه: {e}")

def handle_contact(update: Update, context: CallbackContext):
    contact = update.message.contact
    user_id = contact.user_id
    phone_number = contact.phone_number

    existing = users_col.find_one({"user_id": user_id})
    if not existing:
        users_col.insert_one({
            "user_id": user_id,
            "phone": phone_number,
            "joined": False,
            "expire_at": None
        })
    else:
        users_col.update_one({"user_id": user_id}, {"$set": {"phone": phone_number}})

    # ارسال پیام با دکمه لینک پرداخت
    keyboard = [[InlineKeyboardButton("پرداخت و دریافت لینک عضویت", url=ZARINPAL_LINK)]]
    sent_msg = update.message.reply_text("✅ شماره شما ثبت شد. برای عضویت VIP، ابتدا پرداخت انجام دهید:", reply_markup=InlineKeyboardMarkup(keyboard))

    # حذف دکمه لینک پرداخت پس از 10 دقیقه
    context.job_queue.run_once(remove_channel_button, 600, context={"chat_id": sent_msg.chat_id, "message_id": sent_msg.message_id})

    # ارسال دکمه پشتیبانی
    support_button = [[InlineKeyboardButton("📩 تیکت به پشتیبانی", callback_data="support")]]
    update.message.reply_text("در صورت سوال یا مشکل، از طریق دکمه زیر با پشتیبانی در ارتباط باشید:", reply_markup=InlineKeyboardMarkup(support_button))

def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    if data == "support":
        context.bot.send_message(chat_id=user_id, text="✏️ لطفاً پیام خود را برای پشتیبانی ارسال کنید.")
        context.user_data['awaiting_ticket'] = True
        query.answer()

def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if context.user_data.get('awaiting_ticket'):
        text = update.message.text
        timestamp = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M")
        ticket = {
            "from": user_id,
            "text": text,
            "time": timestamp
        }
        tickets_col.insert_one(ticket)

        full_name = update.message.from_user.full_name
        user = users_col.find_one({"user_id": user_id})
        phone = user.get("phone") if user else "نامشخص"

        # ارسال پیام تیکت به ادمین
        msg = (
            f"📨 تیکت جدید از کاربر:\n"
            f"👤 نام: {full_name}\n"
            f"📞 شماره: {phone}\n"
            f"🆔 آیدی: {user_id}\n\n"
            f"📨 پیام:\n{text}"
        )
        context.bot.send_message(chat_id=ADMIN_ID, text=msg)

        update.message.reply_text("✅ تیکت شما با موفقیت ارسال شد.")
        context.user_data['awaiting_ticket'] = False
    else:
        update.message.reply_text("برای شروع، دستور /start را ارسال کنید.")

# ---------- راه‌اندازی ربات ----------
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

print("ربات اجرا شد...")
app.run_polling()
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
