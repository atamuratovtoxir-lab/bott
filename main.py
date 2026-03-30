import logging
import requests
import sqlite3
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from datetime import time

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 🔐 OLD TOKEN (o‘zingnikini qo‘y)
TOKEN = "8750583800:AAGWDecP47uPEfcYIrZamE45aHpJsxF2RUA"

logging.basicConfig(level=logging.INFO)

# 📦 DATABASE
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
    params = {
        "latitude": 41,
        "longitude": 69,
        "hourly": "temperature_2m",
    }

    data = requests.get(url, params=params).json()

    return data["hourly"]["temperature_2m"][:24]


# 📊 GRAFIK
def create_graph(temps, user_id):
    hours = list(range(24))

    plt.figure()
    plt.plot(hours, temps)
    plt.title("24 soatlik harorat")
    plt.xlabel("Soat")
    plt.ylabel("°C")

    file_name = f"graph_{user_id}.png"
    plt.savefig(file_name)
    plt.close()

    return file_name


# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Toshkent", "Samarqand"],
        ["Buxoro", "Andijon"],
    ]

    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Salom 👋\nViloyatingizni tanlang:",
        reply_markup=markup,
    )


# 📍 CITY
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    user_id = update.message.from_user.id

    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, city) VALUES (?, ?)",
        (user_id, city),
    )
    conn.commit()

    temps = get_weather(city)
    file_path = create_graph(temps, user_id)

    with open(file_path, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=f"📍 {city}\n📊 24 soatlik harorat",
        )


# 📦 USERS
def get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return cursor.fetchall()


# ⏰ DAILY
async def send_daily(context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()

    for (user_id,) in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🌅 Bugungi ob-havo yangilandi!",
            )
        except Exception as e:
            logging.error(e)


# ▶️ MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))

    # ⏰ 08:00
    app.job_queue.run_daily(send_daily, time=time(8, 0))

    print("Bot ishladi 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()
