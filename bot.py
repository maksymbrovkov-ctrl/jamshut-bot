import telebot
from openai import OpenAI
from collections import deque
import threading
import random
import time
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CHANNEL_ID = os.environ.get("CHANNEL_ID", None)

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    print("❌ Ошибка: Не найдены API ключи!")
    print("Убедитесь, что в Secrets добавлены:")
    print("- TELEGRAM_BOT_TOKEN")
    print("- OPENAI_API_KEY")
    exit(1)

BOT_NAMES = ["джамшут", "джамш", "джамшутик"]
CONTEXT_SIZE = 10

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

chat_context = deque(maxlen=CONTEXT_SIZE)

def is_mentioned(message_text):
    text_lower = message_text.lower()
    for name in BOT_NAMES:
        if name in text_lower:
            return True
    return False

def generate_response(user_message, context):
    messages = [{"role": "system", "content": (
        "Ты саркастичный бот Джамшут — философ и юморист. "
        "Отвечай дерзко, иронично, с умными колкостями, но не оскорбляй пользователей."
    )}]
    messages.extend(context)
    messages.append({"role": "user", "content": user_message})
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    return completion.choices[0].message.content

def auto_post_wisdom():
    if not CHANNEL_ID:
        print("⚠️ CHANNEL_ID не задан - автопостинг отключен")
        return
    
    print(f"✅ Автопостинг мудростей запущен для канала: {CHANNEL_ID}")
    while True:
        sleep_time = random.randint(14400, 21600)
        time.sleep(sleep_time)
        
        try:
            message = generate_response("Напиши саркастичную философскую мудрость.", list(chat_context))
            bot.send_message(CHANNEL_ID, message)
            chat_context.append({"role": "assistant", "content": message})
            print(f"📤 Мудрость отправлена в канал")
        except Exception as e:
            print(f"❌ Ошибка автопостинга: {e}")

@bot.message_handler(func=lambda m: True)
def handle_group_message(message):
    if message.text and is_mentioned(message.text):
        response = generate_response(message.text, list(chat_context))
        bot.reply_to(message, response)
        chat_context.append({"role": "user", "content": message.text})
        chat_context.append({"role": "assistant", "content": response})

threading.Thread(target=auto_post_wisdom, daemon=True).start()

print("🤖 Джамшут запущен и готов философствовать!")
bot.polling(none_stop=True)
