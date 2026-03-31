import logging
import requests
import sqlite3

import pytz
from datetime import datetime

from flask import Flask
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 🔐 TOKEN
TOKEN = "8750583800:AAGWDecP47uPEfcYIrZamE45aHpJsxF2RUA"

UZBEK_TZ = pytz.timezone("Asia/Tashkent")

logging.basicConfig(level=logging.INFO)

# 🌍 VILOYATLAR
REGIONS = {
    "Toshkent viloyati": ["Toshkent", "Chirchiq", "Angren", "Bekobod"],
    "Samarqand viloyati": ["Samarqand", "Urgut", "Kattaqo‘rg‘on"],
    "Buxoro viloyati": ["Buxoro", "Kogon", "G‘ijduvon"],
    "Andijon viloyati": ["Andijon", "Asaka", "Shahrixon"],
    "Farg‘ona viloyati": ["Farg‘ona", "Qo‘qon", "Marg‘ilon"],
    "Namangan viloyati": ["Namangan", "Chortoq", "Pop"],
    "Xorazm viloyati": ["Urganch", "Xiva", "Hazorasp"],
    "Qashqadaryo viloyati": ["Qarshi", "Shahrisabz", "Koson"],
    "Surxondaryo viloyati": ["Termiz", "Denov", "Sherobod"],
    "Jizzax viloyati": ["Jizzax", "Zomin", "G‘allaorol"],
    "Sirdaryo viloyati": ["Guliston", "Shirin", "Boyovut"],
    "Navoiy viloyati": ["Navoiy", "Zarafshon", "Uchquduq"],
}

# 🗂 DB
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    city TEXT
)
""")
conn.commit()

# 🌤 OB-HAVO
def get_weather(city):
    url = "https://api.open-meteo.com/v1/forecast"

    coords = {
        "Toshkent": (41.2995, 69.2401),
        "Samarqand": (39.6547, 66.9750),
        "Buxoro": (39.7747, 64.4286),
        "Andijon": (40.7821, 72.3442),
        "Farg‘ona": (40.3842, 71.7843),
        "Namangan": (41.0011, 71.6726),
        "Urganch": (41.5500, 60.6333),
        "Qarshi": (38.8600, 65.7900),
        "Termiz": (37.9400, 67.5700),
        "Jizzax": (40.1158, 67.8422),
        "Guliston": (40.5000, 68.6667),
        "Navoiy": (40.1000, 65.3700),
    }

    lat, lon = coords.get(city, (None, None))

    if not lat:
        return None

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation_probability",
        "timezone": "auto",
    }

    try:
        data = requests.get(url, params=params, timeout=10).json()
        return data["hourly"]
    except:
        return None

# 👤 USER SAQLASH
def save_user(user_id, city):
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, city) VALUES (?, ?)",
        (user_id, city),
    )
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id, city FROM users")
    return cursor.fetchall()

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [[r] for r in REGIONS.keys()]

    await update.message.reply_text(
        f"👋 Salom {user.first_name}!\n\n"
        "🤖 Bot imkoniyatlari:\n"
        "• Har kuni 08:00 ob-havo\n"
        "• Har 3 soatda yomg‘ir alert\n\n"
        "📍 Viloyatni tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )

# 🔥 TEXT HANDLER
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text in REGIONS:
        cities = REGIONS[text]
        keyboard = [[c] for c in cities]

        await update.message.reply_text(
            f"🏙 {text} → shaharni tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        )
        return

    save_user(user_id, text)
    await update.message.reply_text(f"✅ Tanlandi: {text}")

# 🌅 DAILY
async def daily_send(app):
    for user_id, city in get_users():
        data = get_weather(city)
        if not data:
            continue

        temps = data["temperature_2m"][:24]

        msg = f"🌅 {city} bugungi ob-havo:\n\n"
        for i, t in enumerate(temps):
            msg += f"{i}:00 → {t}°C\n"

        try:
            await app.bot.send_message(chat_id=user_id, text=msg)
        except:
            pass

# 🌧 ALERT
async def alert_send(app):
    for user_id, city in get_users():
        data = get_weather(city)
        if not data:
            continue

        rain = data["precipitation_probability"]

        for i, r in enumerate(rain):
            if r >= 70:
                try:
                    await app.bot.send_message(
                        chat_id=user_id,
                        text=f"⚠️ {city} da {i}:00 da yomg‘ir ehtimoli {r}%",
                        disable_notification=True,
                    )
                except:
                    pass

# 🤖 BOT
def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    scheduler = AsyncIOScheduler(timezone=UZBEK_TZ)
    scheduler.add_job(lambda: app.create_task(daily_send(app)), "cron", hour=8)
    scheduler.add_job(lambda: app.create_task(alert_send(app)), "interval", hours=3)
    scheduler.start()

    print("🚀 Bot ishlayapti")
    app.run_polling()

# 🌐 WEB
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot ishlayapti 🚀"

# ▶️ MAIN
if __name__ == "__main__":
    import threading

    threading.Thread(target=run_bot).start()
    web.run(host="0.0.0.0", port=10000)
