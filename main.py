import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz

# آدرس MongoDB Atlas
mongo_uri = "mongodb+srv://vipadmin:milad137555@cluster0.g6mqucj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_uri)
db = client["vip_bot"]
users_collection = db["users"]

# تنظیمات
TOKEN = "توکن رباتت اینجا"
CHANNEL_ID = -1002891641618
ADMIN_ID = 5193853523
ZARINPAL_LINK = "https://zarinp.al/miladvip"

# تنظیم منطقه زمانی ایران
tehran = pytz.timezone("Asia/Tehran")

# راه‌اندازی لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# شروع ربات
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = users_collection.find_one({"_id": user_id})

    if not user:
        # ساخت دکمه اشتراک شماره
        button = KeyboardButton("📱 ارسال شماره", request_contact=True)
        keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True)
        await update.message.reply_text("برای ادامه، لطفاً شماره موبایل خود را ارسال کنید:", reply_markup=keyboard)
    else:
        await update.message.reply_text("شما قبلاً ثبت‌نام کرده‌اید.")

# دریافت شماره
async def contact_handler(update: Update, context: CallbackContext):
    user = update.effective_user
    phone = update.message.contact.phone_number
    now = datetime.now(tehran)

    # ذخیره در MongoDB
    users_collection.update_one(
        {"_id": user.id},
        {"$set": {
            "username": user.username,
            "first_name": user.first_name,
            "phone": phone,
            "registered_at": now,
            "is_paid": False,
            "expires_at": None
        }},
        upsert=True
    )

    keyboard = [[
        KeyboardButton("💳 پرداخت VIP"),
    ]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("✅ شماره شما ثبت شد. حالا برای فعال‌سازی عضویت VIP، روی دکمه زیر بزنید:", reply_markup=reply_markup)

# دکمه پرداخت
async def handle_text(update: Update, context: CallbackContext):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "💳 پرداخت VIP":
        await update.message.reply_text(f"برای پرداخت روی لینک زیر بزنید:\n\n{ZARINPAL_LINK}")

    elif text == "📨 تیکت به پشتیبانی":
        await update.message.reply_text("پیام خود را ارسال کنید. ادمین پاسخ خواهد داد.")
        context.user_data["awaiting_ticket"] = True

    else:
        if context.user_data.get("awaiting_ticket"):
            context.user_data["awaiting_ticket"] = False
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"📩 پیام جدید از کاربر:\n\nID: {user_id}\n@{update.effective_user.username}\n\n{text}")
            await update.message.reply_text("پیام شما به پشتیبانی ارسال شد.")
        else:
            await update.message.reply_text("دستور نامعتبر است.")

# ادمین عضویت رو دستی فعال کنه
async def activate(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text("فرمت درست:\n/activate user_id")
        return

    try:
        user_id = int(context.args[0])
        expire_date = datetime.now(tehran) + timedelta(days=30)
        users_collection.update_one(
            {"_id": user_id},
            {"$set": {"is_paid": True, "expires_at": expire_date}}
        )

        await context.bot.send_message(chat_id=user_id, text="🎉 عضویت VIP شما فعال شد!\n\nعضویت تا ۳۰ روز آینده معتبر است.")
        await update.message.reply_text("✅ کاربر با موفقیت فعال شد.")
    except:
        await update.message.reply_text("خطا در فعال‌سازی.")

# بررسی انقضا و حذف از کانال
async def check_expirations(context: CallbackContext):
    now = datetime.now(tehran)
    expired_users = users_collection.find({
        "is_paid": True,
        "expires_at": {"$lte": now}
    })

    for user in expired_users:
        try:
            await context.bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=user["_id"])
            await context.bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=user["_id"])
            await context.bot.send_message(chat_id=user["_id"], text="⛔️ اشتراک VIP شما به پایان رسید و از کانال حذف شدید.")
            users_collection.update_one({"_id": user["_id"]}, {"$set": {"is_paid": False, "expires_at": None}})
        except:
            pass

# اجرای ربات
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("activate", activate))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.job_queue.run_repeating(check_expirations, interval=3600, first=10)

    print("ربات اجرا شد.")
    app.run_polling()
