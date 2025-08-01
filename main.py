from telegram import *
from telegram.ext import *
import logging
from pymongo import MongoClient
import datetime

# توکن ربات
TOKEN = "494613530:AAHQFmKNzgoehLf9i35mIPn1Z8WhtkrBZa4"

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
ADMIN_ID = 368422936

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

def start(update, context):
    keyboard = [[KeyboardButton("ارسال شماره من ☎️", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text("سلام 👋 برای ادامه، لطفاً شماره موبایل خود را ارسال کنید:", reply_markup=reply_markup)

def contact_handler(update, context):
    contact = update.message.contact
    user_id = contact.user_id
    phone_number = contact.phone_number
    full_name = update.message.from_user.full_name
    save_user(user_id, phone_number, full_name)

    keyboard = [
        [InlineKeyboardButton("🌟 ورود به کانال VIP", url="https://t.me/+Bnko8vYkvcRkYjdk")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    sent_msg = update.message.reply_text(
        "✅ شماره شما ثبت شد. برای خرید اشتراک، لطفاً هزینه را پرداخت کنید:\n\n[لینک پرداخت](https://zarinp.al/634382)",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

    ticket_keyboard = [[InlineKeyboardButton("💬 تیکت به پشتیبانی", callback_data="support_ticket")]]
    ticket_markup = InlineKeyboardMarkup(ticket_keyboard)
    update.message.reply_text("در صورت نیاز به پشتیبانی، از این دکمه استفاده کنید:", reply_markup=ticket_markup)

    context.job_queue.run_once(
        remove_channel_button, 600,
        context={'chat_id': sent_msg.chat_id, 'message_id': sent_msg.message_id, 'user_id': user_id}
    )

def remove_channel_button(context: CallbackContext):
    job = context.job
    chat_id = job.context['chat_id']
    message_id = job.context['message_id']
    user_id = job.context['user_id']

    try:
        context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
        context.bot.send_message(chat_id=user_id, text="⏰ دکمه ورود به کانال VIP پس از ۱۰ دقیقه حذف شد. لطفاً اشتراک خود را تمدید کنید.")
    except Exception as e:
        logger.error(f"خطا در حذف دکمه لینک کانال: {e}")

def button_handler(update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    if data == "support_ticket":
        context.user_data['awaiting_support'] = True
        query.message.reply_text("پیام خود را برای پشتیبانی ارسال کنید:")

    elif data.startswith("quick_reply:"):
        target_user_id = int(data.split(":")[1])
        context.user_data['reply_to_user'] = target_user_id
        query.message.reply_text(f"لطفاً پیام پاسخ به کاربر با آیدی {target_user_id} را ارسال کنید:")

def message_handler(update, context):
    user_id = update.message.from_user.id

    if user_id == ADMIN_ID and context.user_data.get('reply_to_user'):
        reply_user_id = context.user_data['reply_to_user']
        reply_text = update.message.text

        try:
            context.bot.send_message(chat_id=reply_user_id, text=f"💬 پاسخ پشتیبانی:\n\n{reply_text}")
            update.message.reply_text("✅ پاسخ شما به کاربر ارسال شد.")
        except Exception as e:
            update.message.reply_text(f"❌ خطا در ارسال پیام به کاربر: {e}")

        context.user_data['reply_to_user'] = None
        return

    if context.user_data.get('awaiting_support'):
        full_name = update.message.from_user.full_name
        phone_doc = users_collection.find_one({"user_id": user_id}) or {}
        phone = phone_doc.get('phone', 'نامشخص')
        user_message = update.message.text

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 پاسخ سریع", callback_data=f"quick_reply:{user_id}")]
        ])

        msg = f"📩 تیکت جدید\n\n👤 نام: {full_name}\n📞 شماره: {phone}\n🆔 آیدی: {user_id}\n\n📨 پیام:\n{user_message}"

        context.bot.send_message(chat_id=ADMIN_ID, text=msg, reply_markup=keyboard)
        update.message.reply_text("✅ پیام شما ارسال شد. منتظر پاسخ باشید.")
        context.user_data['awaiting_support'] = False
        return

    update.message.reply_text("برای شروع، دستور /start را ارسال کنید.")

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
