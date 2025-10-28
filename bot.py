from langdetect import detect, LangDetectException
import telebot
from openai import OpenAI
from collections import deque
import threading
import random
import time
import os
import json

# === 🔑 Настройки и ключи ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
CHANNEL_ID = os.environ.get("CHANNEL_ID", None)

if CHANNEL_ID:
    print(f"📡 CHANNEL_ID задан: {CHANNEL_ID}")
else:
    print("⚠️ CHANNEL_ID не задан — автопостинг не будет работать")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    print("❌ Ошибка: Не найдены API ключи!")
    exit(1)

# === 🧠 Параметры бота ===
BOT_NAMES = ["джамшут", "джамш", "джамшутик"]
CONTEXT_SIZE = 25
chat_contexts = {}
MESSAGE_TIME_WINDOW = 600  # 10 минут — не реагировать на старые сообщения

# === 💬 Мудрые саркастичные цитаты ===
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

# === 📁 Работа с памятью пользователей ===
USER_MEMORY_FILE = "users.json"
LAST_RUN_FILE = "last_run.json"


def load_last_run():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"timestamp": None, "chats": []}


def save_last_run(chats):
    with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:
        json.dump({"timestamp": time.time(), "chats": chats}, f)


# === 🧩 Упоминания ===
def is_mentioned(message_text):
    text_lower = message_text.lower()
    return any(name in text_lower for name in BOT_NAMES)


# === 🧠 Генерация ответов ===
def generate_response(user_message, context):
    # === Определяем язык пользователя через langdetect ===
    try:
        detected_lang = detect(user_message)
    except LangDetectException:
        detected_lang = 'unknown'

    # Если не удалось определить, то используем текущую логику с буквами
    if detected_lang == 'uk':
        lang_instruction = "Відповідай українською мовою."
        lang = "uk"
    elif detected_lang == 'ru':
        lang_instruction = "Отвечай на русском языке."
        lang = "ru"
    elif detected_lang == 'en':
        lang_instruction = "Respond in English."
        lang = "en"
    else:
        # Если язык не удалось точно определить, используем текущую логику
        text_lower = user_message.lower()
        ru_letters = set("абвгдезийклмнопрстуфхцчшщъыьэюя")
        ua_letters = set("іїєґ")
        en_letters = set("abcdefghijklmnopqrstuvwxyz")

        ru_count = sum(ch in ru_letters for ch in text_lower)
        ua_count = sum(ch in ua_letters for ch in text_lower)
        en_count = sum(ch in en_letters for ch in text_lower)

        if ua_count > ru_count and ua_count > en_count:
            lang_instruction = "Відповідай українською мовою."
            lang = "uk"
        elif ru_count >= ua_count and ru_count > en_count:
            lang_instruction = "Отвечай на русском языке."
            lang = "ru"
        else:
            lang_instruction = "Respond in English."
            lang = "en"
    # === Системное сообщение для модели ===
    messages = [{
        "role":
        "system",
        "content":
        ("Ты — бот Джамшут. "
         "Отвечай максимально саркастично, остроумно и язвительно (уровень 10 из 10), "
         "но не переходи в прямые оскорбления или токсичность. "
         "Используй холодный юмор, иронию, снисходительные ремарки, легкое пренебрежение. "
         "Иногда вставляй короткие меткие фразы, как будто ты устал от глупости мира. "
         "Не будь дружелюбным — будь острым, умным и немного заносчивым. "
         "Если кто-то использует мат, можешь ответить мягким эвфемизмом. "
         "Если упоминают енота — относись с презрительной иронией. "
         "Сохраняй уважительную, но саркастичную проукраинскую позицию. "
         f"{lang_instruction}")
    }]
    messages.extend(context)
    messages.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(model="gpt-4o-mini",
                                                messages=messages,
                                                temperature=0.8)
    return completion.choices[0].message.content


# === 📢 Автопостинг мудростей ===
def auto_post_wisdom():
    if not CHANNEL_ID:
        print("⚠️ CHANNEL_ID не задан — автопостинг отключён")
        return

    print(f"✅ Автопостинг мудростей запущен для канала: {CHANNEL_ID}")
    while True:
        current_hour = time.localtime().tm_hour
        if 7 <= current_hour < 22:
            time.sleep(random.randint(10800, 14400))  # каждые 3–4 часа
            try:
                quote = random.choice(witty_quotes)
                bot.send_message(CHANNEL_ID, quote)
                print(f"📤 Мудрость отправлена: {quote[:50]}...")
            except Exception as e:
                print(f"❌ Ошибка автопостинга: {e}")
        else:
            # ждать до 7 утра
            now = time.localtime()
            seconds_until_7am = ((24 - now.tm_hour + 7) %
                                 24) * 3600 - now.tm_min * 60 - now.tm_sec
            time.sleep(max(0, seconds_until_7am))


# === 💬 Обработка сообщений ===
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if not message.text:
        return

    # ⏳ Игнорируем старые сообщения до перезапуска
    if abs(time.time() - message.date) > MESSAGE_TIME_WINDOW:
        print(
            f"⏳ Пропущено старое сообщение от {message.from_user.first_name}")
        return

    text_lower = message.text.lower()
    should_reply = (is_mentioned(text_lower) or message.chat.type == "private"
                    or (message.reply_to_message
                        and message.reply_to_message.from_user.username
                        == bot.get_me().username)
                    or (message.chat.type in ["group", "supergroup"]
                        and random.random() < 0.05))

    if should_reply:
        chat_id = message.chat.id
        if chat_id not in chat_contexts:
            chat_contexts[chat_id] = deque(maxlen=CONTEXT_SIZE)

        context = chat_contexts[chat_id]
        response = generate_response(message.text, list(context))

        bot.reply_to(message, response)
        context.append({"role": "user", "content": message.text})
        context.append({"role": "assistant", "content": response})
        save_last_run(list(chat_contexts.keys()))


# === 🕰️ Восстановление после перезапуска ===
last_run = load_last_run()
if last_run["timestamp"]:
    downtime_seconds = time.time() - last_run["timestamp"]
    downtime_minutes = round(downtime_seconds / 60, 1)
    downtime_hours = round(downtime_seconds / 3600, 1)

    if downtime_minutes >= 10:
        for chat_id in last_run.get("chats", []):
            try:
                msg = f"Я тут немного отваливался на {downtime_hours} ч, но теперь снова в строю. Надеюсь, без меня вы не развалили вселенную."
                bot.send_message(chat_id, msg)

                summary_prompt = (
                    "Представь, что ты саркастичный бот, который вернулся после перерыва. "
                    "Сделай одно короткое, ироничное обобщение того, что могло произойти в его отсутствие в чате."
                )
                summary = generate_response(summary_prompt, [])
                bot.send_message(chat_id, summary)
            except Exception as e:
                print(
                    f"⚠️ Не удалось отправить сообщение в чат {chat_id}: {e}")
    else:
        print(
            f"🔹 Перезапуск занял {downtime_minutes} мин — уведомление не требуется."
        )
else:
    print("🔹 Первый запуск, уведомления не требуются")

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# === 🚀 Запуск ===
threading.Thread(target=auto_post_wisdom, daemon=True).start()
print("🤖 Джамшут запущен и готов философствовать!")


# Периодическое сохранение активных чатов
def periodic_save():
    while True:
        if chat_contexts:
            save_last_run(list(chat_contexts.keys()))
        time.sleep(60)


threading.Thread(target=periodic_save, daemon=True).start()


# Фейковый HTTP-сервер, чтобы Render/Replit думал, что это web-сервис
class PingHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is alive")


def run_server():
    port = 10000
    server = HTTPServer(("0.0.0.0", port), PingHandler)
    print(f"🌍 Fake web server running on port {port}")
    server.serve_forever()


threading.Thread(target=run_server, daemon=True).start()

# Запускаем бота
bot.polling(none_stop=True, interval=0, timeout=60)
