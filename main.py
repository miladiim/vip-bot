import logging
from flask import Flask, request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from pymongo import MongoClient
import json

# اطلاعات ثابت
TOKEN = "494613530:AAHQFmKNzgoehLf9i35mIPn1Z8WhtkrBZa4"
ZARINPAL_URL = "https://zarinp.al/634382"
CHANNEL_LINK = "https://t.me/+Bnko8vYkvcRkYjdk"
ADMIN_ID = 368422936
MONGO_URI = "mongodb+srv://vipadmin:milad137555@cluster0.g6mqucj.mongodb.net"
DB_NAME = "vip_bot"

# اتصال به MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_col = db["users"]
tickets_col = db["tickets"]

# اپلیکیشن Flask برای وب‌هوک
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ساخت اپلیکیشن تلگرام
bot_app = ApplicationBuilder().token(TOKEN).build()

# هندلر شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = KeyboardButton("ارسال شماره 📱", request_contact=True)
    markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("برای ادامه لطفا شماره موبایل خود را ارسال کنید:", reply_markup=markup)

# هندلر دریافت شماره
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_id = update.effective_user.id

    users_col.update_one({"user_id": user_id}, {"$set": {
        "user_id": user_id,
        "phone_number": contact.phone_number,
        "step": "waiting_payment"
    }}, upsert=True)

    await update.message.reply_text(
        f"✅ شماره شما ثبت شد.\nاکنون برای فعال‌سازی عضویت VIP روی لینک زیر پرداخت را انجام دهید:\n\n{ZARINPAL_URL}",
        reply_markup=ReplyKeyboardRemove()
    )

    keyboard = [[KeyboardButton("📩 تیکت به پشتیبانی")]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("در صورت نیاز به پشتیبانی از این گزینه استفاده کنید:", reply_markup=markup)

# هندلر ارسال تیکت
async def handle_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text

    tickets_col.insert_one({
        "user_id": user_id,
        "message": message
    })

    await context.bot.send_message(chat_id=ADMIN_ID, text=f"🎟 تیکت جدید از {user_id}:\n{message}")
    await update.message.reply_text("✅ پیام شما به پشتیبانی ارسال شد.")

# هندلر عمومی
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "تیکت" in update.message.text:
        await handle_ticket(update, context)

# وب‌هوک
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.update_queue.put_nowait(update)
    return "ok"

# صفحه تست
@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است."

# تعریف هندلرها
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
bot_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

# اجرای فلask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
