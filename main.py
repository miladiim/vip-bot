from flask import Flask, request
import telebot
import time

API_TOKEN = '494613530:AAHQFmKNzgoehLf9i35mIPn1Z8WhtkrBZa4'
ADMIN_ID = 368422936  # آیدی عددی خودت رو اینجا بذار

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

users = {}

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'

@app.route('/webhook', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return 'ok'

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn = telebot.types.KeyboardButton('📱 ارسال شماره موبایل', request_contact=True)
    markup.add(btn)
    bot.send_message(message.chat.id, "سلام 👋 لطفاً شماره موبایلت رو ارسال کن:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    users[user_id] = {'phone': phone, 'timestamp': int(time.time())}
    bot.send_message(ADMIN_ID, f"📥 کاربر جدید:\nآیدی: {user_id}\nشماره: {phone}")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🎫 تیکت به پشتیبانی')
    bot.send_message(message.chat.id, "✅ ثبت شد. اگر سوالی داری روی دکمه زیر بزن.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🎫 تیکت به پشتیبانی')
def ask_support(message):
    bot.send_message(message.chat.id, "📝 لطفاً پیام خود را بنویسید و ارسال کنید.")
    bot.register_next_step_handler(message, forward_to_admin)

def forward_to_admin(message):
    bot.send_message(ADMIN_ID, f"📩 پیام از {message.from_user.id}:\n{message.text}")
    bot.send_message(message.chat.id, "✅ پیام شما ارسال شد. منتظر پاسخ باشید.")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
