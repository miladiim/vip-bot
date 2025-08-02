
import logging
from flask import Flask, request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from pymongo import MongoClient
import json
import requests

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

TOKEN = config["token"]
CHANNEL_LINK = config["channel"]
ZARINPAL_URL = config["zarinpal_url"]
ADMIN_ID = 368422936  # آیدی عددی شما

# MongoDB setup
client = MongoClient("mongodb+srv://vipadmin:milad137555@cluster0.g6mqucj.mongodb.net")
db = client["vip_bot"]
users_col = db["users"]
tickets_col = db["tickets"]

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Telegram bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    button = KeyboardButton("ارسال شماره 📱", request_contact=True)
    markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("برای ادامه لطفا شماره موبایل خود را ارسال کنید:", reply_markup=markup)

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

async def handle_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tickets_col.insert_one({
        "user_id": user_id,
        "message": update.message.text
    })
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"🎟 تیکت جدید از {user_id}:\n{update.message.text}")
    await update.message.reply_text("✅ پیام شما به پشتیبانی ارسال شد.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "تیکت" in text:
        await handle_ticket(update, context)

@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), Application.builder().token(TOKEN).build().bot)
    Application.builder().token(TOKEN).build().process_update(update)
    return "ok"

@app.route("/")
def index():
    return "Bot is running."

def main():
    app_telegram = Application.builder().token(TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app_telegram.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    app_telegram.run_polling()

if __name__ == "__main__":
    main()
