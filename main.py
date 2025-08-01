from telegram import *
from telegram.ext import *
import logging
from pymongo import MongoClient
import datetime

# توکن ربات
TOKEN = "توکن خودت اینجا بذار"

# اتصال به MongoDB Atlas
MONGO_URI = "mongodb+srv://vipadmin:milad137555@cluster0.g6mqucj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["vip_bot"]
users_collection = db["users"]

# تنظیمات لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# شناسه عددی کانال VIP
VIP_CHANNEL_ID = -1002891641618

# فقط آیدی عددی ادمین اصلی
ADMIN_ID = 123456789  # آیدی عددی خودت رو جایگزین کن

# شروع ربات
def start(update, context):
    keyboard = [[KeyboardButton("ارسال شماره من ☎️", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text("سلام 👋 برای ادامه، لطفاً شماره موبایل خود را ارسال کنید:", reply_markup=reply_markup)

# ذخیره اطلاعات کاربر در دیتابیس
def save_user(user_id, phone_number, full_name):
    existing_user = users_collection.find_one({"user_id": user_id})
    if not existing_user:
        users_collection.insert_one({
            "user_id": user_id,
            "phone": phone_number,
            "full_name": full_name,
            "join_date": datetime.datetime.utcnow(),
            "is_active": True
        })
    else:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"phone": phone_number, "full_name": full_name, "is_active": True}}
        )

# دریافت شماره موبایل
def contact_handler(update, context):
    contact = update.message.contact
    user_id = contact.user_id
    phone_number = contact.phone_number
    full_name = update.message.from_user.full_name
    save_user(user_id, phone_number, full_name)

    keyboard = [[InlineKeyboardButton("💬 تیکت به پشتیبانی", callback_data="support_ticket")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("✅ شماره شما ثبت شد. برای خرید اشتراک، لطفاً هزینه را پرداخت کنید:\n\n[لینک پرداخت](https://zarinp.al/yourlink)", parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

# دکمه پشتیبانی
def button_handler(update, context):
    query = update.callback_query
    query.answer()
    if query.data == "support_ticket":
        context.user_data['awaiting_support'] = True
        query.message.reply_text("پیام خود را برای پشتیبانی ارسال کنید:")
        
# دریافت پیام تیکت
def message_handler(update, context):
    if context.user_data.get('awaiting_support'):
        user_id = update.message.from_user.id
        full_name = update.message.from_user.full_name
        phone = users_collection.find_one({"user_id": user_id}) or {}
        msg = f"📩 تیکت جدید\n\n👤 نام: {full_name}\n📞 شماره: {phone.get('phone', 'نامشخص')}\n🆔 آیدی: {user_id}\n\n📨 پیام:\n{update.message.text}"
        context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        update.message.reply_text("✅ پیام شما ارسال شد. منتظر پاسخ باشید.")
        context.user_data['awaiting_support'] = False
    else:
        update.message.reply_text("برای شروع، دستور /start را ارسال کنید.")

# راه‌اندازی ربات
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.contact, contact_handler))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
