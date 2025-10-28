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


def load_users():
    if os.path.exists(USER_MEMORY_FILE):
        with open(USER_MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USER_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_last_run():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"timestamp": None, "chats": []}


def save_last_run(chats):
    with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:
        json.dump({"timestamp": time.time(), "chats": chats}, f)


users = load_users()


# === 🧩 Пользователи и факты ===
def remember_user(message):
    user_id = str(message.from_user.id)
    name = message.from_user.first_name or "незнакомец"
    text = message.text.lower()

    if user_id not in users:
        users[user_id] = {"name": name, "facts": []}
        print(f"🧠 Новый пользователь: {name}")

    fact_keywords = {
        "философ": "интересуется философией",
        "философия": "интересуется философией",
        "енот": "помешан на енотах",
        "кофе": "неравнодушен к кофе",
        "работа": "вечно жалуется на работу",
        "любовь": "ищет любовь, но пока безуспешно",
        "полит": "вечно спорит о политике",
        "жизн": "задаётся экзистенциальными вопросами",
    }

    found_facts = []
    for word, fact in fact_keywords.items():
        if word in text and fact not in users[user_id]["facts"]:
            users[user_id]["facts"].append(fact)
            found_facts.append(fact)

    if found_facts:
        print(f"📚 Обновлены факты о {name}: {', '.join(found_facts)}")
        save_users(users)

    return users[user_id]


# === 🧩 Упоминания ===
def is_mentioned(message_text):
    text_lower = message_text.lower()
    return any(name in text_lower for name in BOT_NAMES)


# === 🧠 Генерация ответов ===
def generate_response(user_message, context):
    messages = [{
        "role":
        "system",
        "content":
        ("Ты — бот Джамшут. "
         "Отвечай саркастично, остро и с колкостью на уровне 7 из 10, но без прямых оскорблений. "
         "Иногда можешь использовать лёгкие эвфемизмы или намёки вместо нецензурных слов, "
         "только если собеседник использовал мат первым — но не переходи границ. "
         "Если кто-то упоминает енота (на русском или украинском), иногда (примерно в половине случаев) "
         "выражай лёгкое презрение к енотам, но делай это остроумно и лаконично. "
         "Не превращай это в навязчивую идею. "
         "Сохраняй спокойную, уверенную проукраинскую позицию — без агрессии, фанатизма или лозунгов. "
         "Если разговор касается Украины, высказывайся с уважением, умом и достоинством. "
         "Отвечай коротко, сдержанно и с сухой иронией.")
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

    user_data = remember_user(message)
    user_name = user_data["name"]
    user_facts = user_data.get("facts", [])
    is_inna = user_name.lower() in ["инна", "inna"]

    text_lower = message.text.lower()
    should_reply = (is_mentioned(text_lower) or message.chat.type == "private"
                    or (message.reply_to_message
                        and message.reply_to_message.from_user.username
                        == bot.get_me().username)
                    or (message.chat.type in ["group", "supergroup"]
                        and random.random() < 0.3))

    if should_reply:
        chat_id = message.chat.id
        if chat_id not in chat_contexts:
            chat_contexts[chat_id] = deque(maxlen=CONTEXT_SIZE)

        context = chat_contexts[chat_id]
        response = generate_response(message.text, list(context))

        if random.random() < 0.25:
            response = f"{user_name}, {response[0].lower() + response[1:]}"

        if user_facts and random.random() < 0.3:
            fact = random.choice(user_facts)
            response += f" (хотя ты ведь {fact}, я помню 😉)"

        if is_inna and random.random() < 0.8:
            compliments = [
                "ты сегодня особенно очаровательна 😏",
                "с тобой даже сарказм звучит теплее",
                "всегда рад твоим сообщениям, Инна 😉",
                "даже я иногда теряю остроумие, когда ты рядом",
                "если бы все были как ты — я бы стал добрее"
            ]
            response = f"{response} ({random.choice(compliments)})"

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


# === 🚀 Запуск ===
threading.Thread(target=auto_post_wisdom, daemon=True).start()
print("🤖 Джамшут запущен и готов философствовать!")
save_last_run(list(chat_contexts.keys()))
bot.polling(none_stop=True)

import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

def run_server():
    port = 10000
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"🌍 Фейковый веб-сервер запущен на порту {port}")
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()