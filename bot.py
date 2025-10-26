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

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "Привет! Я енот-ИИ, вершина эволюции 🦝💡")

@bot.message_handler(func=lambda msg: True)
def chat_with_ai(message):
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": message.text}]
        )
        answer = completion.choices[0].message.content
        bot.reply_to(message, answer)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

print("🦝 Бот запущен и готов к работе!")
bot.polling()
