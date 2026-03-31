import logging
import sqlite3
import requests
import matplotlib.pyplot as plt
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8750583800:AAGWDecP47uPEfcYIrZamE45aHpJsxF2RUA"

logging.basicConfig(level=logging.INFO)

# 📦 DB
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    city TEXT
)
""")
conn.commit()

# 📍 DATA
REGIONS = {
    "Toshkent": ["Toshkent", "Chirchiq", "Angren"],
    "Samarqand": ["Samarqand", "Urgut"],
    "Farg'ona": ["Farg'ona", "Qo'qon", "Marg'ilon"],
}

# 📍 USER STATE (LEVEL)
user_state = {}

# ------------------
# DB FUNCTIONS
# ------------------
def save_city(user_id, city):
    cursor.execute(
        "INSERT OR REPLACE INTO users VALUES (?, ?)",
        (user_id, city),
    )
    conn.commit()

def get_city(user_id):
    cursor.execute("SELECT city FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else None

# ------------------
# WEATHER API
# ------------------
def get_weather(city):
    geo = requests.get(
        f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    ).json()

    if "results" not in geo:
        return None

    lat = geo["results"][0]["latitude"]
    lon = geo["results"][0]["longitude"]

    return requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    ).json()

# ------------------
# GRAPH
# ------------------
def create_graph(data):
    days = data["time"]
    temps = data["temperature_2m_max"]

    plt.figure()
    plt.plot(days, temps)
    plt.xticks(rotation=45)

    file = "graph.png"
    plt.savefig(file)
    plt.close()

    return file

# ------------------
# MENUS
# ------------------
def main_menu():
    return ReplyKeyboardMarkup(
        [["📍 Viloyat tanlash"]],
        resize_keyboard=True
    )

def region_menu():
    return ReplyKeyboardMarkup(
        [[r] for r in REGIONS.keys()] + [["⬅️ Orqaga"]],
        resize_keyboard=True
    )

def city_menu(region):
    return ReplyKeyboardMarkup(
        [[c] for c in REGIONS[region]] + [["⬅️ Orqaga"]],
        resize_keyboard=True
    )

def weather_menu():
    return ReplyKeyboardMarkup(
        [
            ["🌤 Hozirgi ob-havo"],
            ["📊 24 soatlik"],
            ["📅 5 kunlik grafik"],
            ["⬅️ Orqaga"],
        ],
        resize_keyboard=True
    )

# ------------------
# START
# ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = "MAIN"

    await update.message.reply_text(
        "👋 Salom!\n\nMen ob-havo botiman.\n\n📍 Viloyat tanlash uchun bosing:",
        reply_markup=main_menu(),
    )

# ------------------
# HANDLE TEXT
# ------------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    state = user_state.get(user_id, "MAIN")

    # 🔙 ORQAGA (GLOBAL)
    if text == "⬅️ Orqaga":
        if state == "CITY":
            user_state[user_id] = "REGION"
            await update.message.reply_text(
                "⬅️ Viloyat tanlash",
                reply_markup=region_menu(),
            )
            return

        if state == "WEATHER":
            user_state[user_id] = "CITY"
            region = find_region(get_city(user_id))
            await update.message.reply_text(
                "⬅️ Shahar tanlash",
                reply_markup=city_menu(region),
            )
            return

        await start(update, context)
        return

    # 📍 VILOYAT TANLASH
    if text == "📍 Viloyat tanlash":
        user_state[user_id] = "REGION"
        await update.message.reply_text(
            "📍 Viloyatni tanlang:",
            reply_markup=region_menu(),
        )
        return

    # 🌍 REGION TANLANDI
    if text in REGIONS:
        user_state[user_id] = "CITY"

        await update.message.reply_text(
            f"{text} → shahar tanlang:",
            reply_markup=city_menu(text),
        )
        return

    # 🏙 CITY TANLANDI
    for region, cities in REGIONS.items():
        if text in cities:
            save_city(user_id, text)
            user_state[user_id] = "WEATHER"

            await update.message.reply_text(
                f"✅ Tanlandi: {text}",
                reply_markup=weather_menu(),
            )
            return

    # 🌤 HOZIRGI OB-HAVO
    if text == "🌤 Hozirgi ob-havo":
        city = get_city(user_id)
        data = get_weather(city)

        msg = f"🌤 {city}\n"
        msg += f"🌡 {data['current_weather']['temperature']}°C\n"
        msg += f"💨 Shamol: {data['current_weather']['windspeed']} km/h"

        await update.message.reply_text(msg)
        return

    # 📊 24 SOAT
    if text == "📊 24 soatlik":
        city = get_city(user_id)
        data = get_weather(city)

        temps = data["hourly"]["temperature_2m"][:24]

        msg = "📊 24 soat:\n"
        for i, t in enumerate(temps):
            msg += f"{i}:00 → {t}°C\n"

        await update.message.reply_text(msg)
        return

    # 📅 5 KUNLIK
    if text == "📅 5 kunlik grafik":
        city = get_city(user_id)
        data = get_weather(city)

        file = create_graph(data["daily"])

        await update.message.reply_photo(photo=open(file, "rb"))
        os.remove(file)
        return

# ------------------
# FIND REGION
# ------------------
def find_region(city):
    for region, cities in REGIONS.items():
        if city in cities:
            return region
    return None

# ------------------
# RUN
# ------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("Bot ishlayapti...")
    app.run_polling()

if __name__ == "__main__":
    main()
