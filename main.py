import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from pymongo import MongoClient
from datetime import datetime
import pytz

# ---------------- تنظیمات ربات ----------------
BOT_TOKEN = "توکن‌رباتت"
ADMIN_ID = 368422936
CHANNEL_ID = -1002891641618
CHANNEL_LINK = "https://t.me/+Bnko8vYkvcRkYjdk"
ZARINPAL_LINK = "https://zarinp.al/634382"

# ---------------- اتصال به MongoDB ----------------
client = MongoClient("mongodb+srv://vipadmin:milad137555@cluster0.g6mqucj.mongodb.net/?retryWrites=true&w=majority")
db = client["vip_bot"]
users_col = db["users"]
tickets_col = db["tickets"]

# ---------------- لاگ ----------------
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# ---------------- توابع ----------------
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = users_col.find_one({"user_id": user_id})
    if user and user.get("phone"):
        update.message.reply_text("شماره شما قبلاً ثبت شده. برای پشتیبانی می‌تونی از دکمه زیر استفاده کنی.")
        show_support_button(update)
    else:
        keyboard = [[KeyboardButton("ارسال شماره موبایل", request_contact=True)]]
        update.message.reply_text(
            "لطفاً شماره موبایل خودت رو برای ادامه ارسال کن:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )

def show_support_button(update: Update):
    support_btn = [[InlineKeyboardButton("📩 تیکت به پشتیبانی", callback_data="support")]]
    update.message.reply_text("در صورت سوال، از طریق دکمه زیر پیام بده:", reply_markup=InlineKeyboardMarkup(support_btn))

def remove_payment_button(context: CallbackContext):
    job = context.job
    try:
        context.bot.edit_message_reply_markup(chat_id=job.context["chat_id"], message_id=job.context["message_id"], reply_markup=None)
    except Exception as e:
        logging.error(f"خطا در حذف دکمه پرداخت: {e}")

def handle_contact(update: Update, context: CallbackContext):
    contact = update.message.contact
    user_id = contact.user_id
    phone = contact.phone_number

    users_col.update_one(
        {"user_id": user_id},
        {"$set": {"phone": phone, "joined": False, "expire_at": None}},
        upsert=True
    )

    # دکمه پرداخت
    btn = [[InlineKeyboardButton("پرداخت و دریافت لینک عضویت", url=ZARINPAL_LINK)]]
    msg = update.message.reply_text("✅ شماره ثبت شد. حالا پرداخت کن تا لینک عضویت برات فعال بشه:", reply_markup=InlineKeyboardMarkup(btn))

    context.job_queue.run_once(remove_payment_button, 600, context={"chat_id": msg.chat_id, "message_id": msg.message_id})

    # دکمه پشتیبانی
    show_support_button(update)

def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "support":
        query.answer()
        context.user_data["awaiting_ticket"] = True
        context.bot.send_message(chat_id=user_id, text="✏️ لطفاً پیام خود را برای پشتیبانی ارسال کن.")

def handle_text(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if context.user_data.get("awaiting_ticket"):
        msg = update.message.text
        timestamp = datetime.now(pytz.timezone("Asia/Tehran")).strftime("%Y-%m-%d %H:%M")
        user = users_col.find_one({"user_id": user_id})
        ticket = {
            "from": user_id,
            "text": msg,
            "time": timestamp
        }
        tickets_col.insert_one(ticket)

        phone = user.get("phone", "نامشخص")
        full_name = update.message.from_user.full_name

        admin_msg = (
            f"📨 تیکت جدید\n"
            f"👤 نام: {full_name}\n"
            f"📞 شماره: {phone}\n"
            f"🆔 آیدی: {user_id}\n\n"
            f"📩 پیام:\n{msg}"
        )
        context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
        update.message.reply_text("✅ پیام شما برای پشتیبانی ارسال شد.")
        context.user_data["awaiting_ticket"] = False
    else:
        update.message.reply_text("برای شروع، دستور /start رو ارسال کن.")

# ---------------- اجرای ربات ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 ربات VIP اجرا شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
