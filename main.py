import os
import logging
import requests
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from flask import Flask
from threading import Thread

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 🔐 TOKEN
TOKEN = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)

# 🌐 FLASK (Render uchun kerak)
app_web = Flask("")


@app_web.route("/")
def home():
    return "Bot ishlayapti 🚀"


def run_web():
    app_web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


# 🌍 SHAHARLAR
CITIES = {
    "Toshkent": (41.2995, 69.2401),
    "Samarqand": (39.6547, 66.9750),
    "Buxoro": (39.7747, 64.4286),
    "Andijon": (40.7821, 72.3442),
}


def get_weather(city):
    if city not in CITIES:
        return None

    lat, lon = CITIES[city]

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m",
        "timezone": "auto",
    }

    try:
        data = requests.get(url, timeout=10).json()
        return data["hourly"]["temperature_2m"][:24]
    except Exception as e:
        logging.error(e)
        return None


def create_graph(temps, user_id):
    hours = list(range(24))

    plt.figure()
    plt.plot(hours, temps)
    plt.title("24 soatlik harorat")
    plt.xlabel("Soat")
    plt.ylabel("°C")

    path = f"/tmp/weather_{user_id}.png"
    plt.savefig(path)
    plt.close()

    return path


# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Toshkent", "Samarqand"],
        ["Buxoro", "Andijon"],
    ]

    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 Salom!\nViloyatni tanlang:",
        reply_markup=markup,
    )


# 📍 CITY
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    user_id = update.message.from_user.id

    temps = get_weather(city)

    if not temps:
        await update.message.reply_text("❌ Ob-havo topilmadi")
        return

    file_path = create_graph(temps, user_id)

    with open(file_path, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=f"📍 {city} ob-havo",
        )


# ▶️ MAIN
def main():
    # Telegram bot
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))

    # Web server (Render uchun)
    Thread(target=run_web).start()

    print("Bot ishga tushdi 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()
