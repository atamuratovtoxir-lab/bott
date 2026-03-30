import logging
import requests
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
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

# 📦 DATABASE (userlarni saqlash)
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    city TEXT
)
""")
conn.commit()


# 🌤 Ob-havo API
def get_weather(city):
    url = f"https://api.open-meteo.com/v1/forecast?latitude=41&longitude=69&hourly=temperature_2m,precipitation_probability"
    data = requests.get(url).json()

    temps = data["hourly"]["temperature_2m"][:24]

    return temps


# 📊 GRAFIK CHIZISH
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
    user = update.message.from_user
    user_id = user.id

    keyboard = [["Toshkent", "Samarqand"], ["Buxoro", "Andijon"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"Salom {user.first_name} 👋\n"
        "Men ob-havoni yuboraman.\n\n"
        "Viloyatingizni tanlang 👇",
        reply_markup=markup,
    )


# 📍 Viloyat tanlash
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    user_id = update.message.from_user.id

    # 💾 user saqlash
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, city) VALUES (?, ?)",
        (user_id, city),
    )
    conn.commit()

    temps = get_weather(city)

    # 📊 grafik yaratish
    file_path = create_graph(temps, user_id)

    # matn
    text = f"📍 {city}\n📊 24 soatlik harorat tayyor!"

    await update.message.reply_photo(photo=open(file_path, "rb"), caption=text)


# 📦 USERLARNI O‘QISH
def get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return cursor.fetchall()


# ⏰ umumiy xabar
async def send_daily(context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()

    for (user_id,) in users:
        await context.bot.send_message(
            chat_id=user_id,
            text="🌅 Bugungi ob-havo yangilandi!",
        )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))

    job = app.job_queue

    # ⏰ har kuni
    job.run_daily(send_daily, time=datetime.strptime("08:00", "%H:%M").time())

    print("Bot ishga tushdi 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()