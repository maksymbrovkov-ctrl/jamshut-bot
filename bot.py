import telebot
from openai import OpenAI
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    print("❌ Ошибка: Не найдены API ключи!")
    print("Убедитесь, что в Secrets добавлены:")
    print("- TELEGRAM_BOT_TOKEN")
    print("- OPENAI_API_KEY")
    exit(1)

BOT_NAMES = ["джамшут", "джамш", "джамшутик"]

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

def generate_response(user_message):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "Ты саркастичный бот Джамшут — философ и юморист. "
                "Отвечай дерзко, иронично, с умными колкостями, но не оскорбляй пользователей."
            )},
            {"role": "user", "content": user_message}
        ]
    )
    return completion.choices[0].message.content

def is_mentioned(message_text):
    text_lower = message_text.lower()
    for name in BOT_NAMES:
        if name in text_lower:
            return True
    return False

@bot.message_handler(func=lambda m: True)
def handle_group_message(message):
    if message.text and is_mentioned(message.text):
        response = generate_response(message.text)
        bot.reply_to(message, response)

print("🤖 Джамшут запущен и готов философствовать!")
bot.polling(none_stop=True)
