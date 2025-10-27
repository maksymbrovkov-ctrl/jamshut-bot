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

witty_quotes = [
    "Людям нравится спорить, но редко кто умеет быть правым — проверьте себя.",
    "Умные решения редко делают умные люди. Вы догадаетесь, почему.",
    "Если вы всё ещё сомневаетесь, значит, мозгов у вас явно меньше среднего.",
    "Попробуйте почитать инструкции, если это слишком сложно — вызовите кого-то умнее.",
    "Очевидные вещи лучше не спрашивать, иначе меня начинает коробить.",
    "Мудрость приходит с опытом. Опыт приходит с ошибками. Ну вы поняли.",
    "Иногда лучше промолчать и показаться дураком, чем открыть рот и развеять все сомнения.",
    "Жизнь — это не sprint, это marathon. Но большинство даже до старта не доползают.",
    "Философия — это когда непонятно, зато звучит умно. Как раз ваш случай.",
    "Если проблему можно решить деньгами, значит это не проблема, а прайс-лист."
]

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
        "Ты — колкий, язвительный бот Джамшут. "
        "Отвечай на сообщения с сарказмом, ехидством и лёгкой циничностью. "
        "Будь колким выше среднего уровня, но не переходи в грубость или оскорбления. "
        "Используй умный юмор, иронию и философские нотки."
    )}]
    messages.extend(context)
    messages.append({"role": "user", "content": user_message})
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.8
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
            quote = random.choice(witty_quotes)
            bot.send_message(CHANNEL_ID, quote)
            print(f"📤 Мудрость отправлена в канал: {quote[:50]}...")
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
