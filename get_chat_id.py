import telebot
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_TOKEN:
    print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден!")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

print("🔍 Бот запущен для получения Chat ID")
print("📝 Напишите боту или добавьте его в группу/канал и отправьте сообщение")
print("-" * 60)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    print(f"✅ Chat ID: {message.chat.id}")
    print(f"   Тип: {message.chat.type}")
    if message.chat.title:
        print(f"   Название: {message.chat.title}")
    print("-" * 60)

bot.polling(none_stop=True)
