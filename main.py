import requests
import matplotlib.pyplot as plt
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "8750583800:AAGWDecP47uPEfcYIrZamE45aHpJsxF2RUA"  # <-- shu yerga token qo‘y

# USER STATE
user_city = {}
user_state = {}

# Viloyatlar va shaharlar
regions = {
    "Toshkent": ["Toshkent", "Chirchiq", "Angren"],
    "Samarqand": ["Samarqand", "Urgut", "Kattaqo‘rg‘on"],
    "Buxoro": ["Buxoro", "G‘ijduvon", "Kogon"],
    "Andijon": ["Andijon", "Asaka", "Shahrixon"],
    "Farg‘ona": ["Farg‘ona", "Qo‘qon", "Marg‘ilon"],
    "Namangan": ["Namangan", "Chortoq", "Kosonsoy"],
    "Xorazm": ["Urganch", "Xiva", "Xonqa"],
    "Qashqadaryo": ["Qarshi", "Shahrisabz", "Kitob"],
    "Surxondaryo": ["Termiz", "Denov", "Boysun"],
    "Jizzax": ["Jizzax", "Zomin", "G‘allaorol"],
    "Navoiy": ["Navoiy", "Zarafshon", "Karmana"],
    "Qoraqalpog‘iston": ["Nukus", "Taxiatosh", "Chimboy"]
}

# API (Open-Meteo)
def get_weather(city):
    url = f"https://api.open-meteo.com/v1/forecast?latitude=41&longitude=69&hourly=temperature_2m,precipitation_probability,wind_speed_10m&timezone=Asia/Tashkent"
    try:
        r = requests.get(url)
        return r.json()
    except:
        return None


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[r] for r in regions.keys()]
    await update.message.reply_text(
        "🏙 Viloyatni tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    user_state[update.effective_user.id] = "region"


# MESSAGE HANDLER
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # REGION
    if text in regions:
        user_state[user_id] = "city_select"
        keyboard = [[c] for c in regions[text]]
        keyboard.append(["⬅️ Orqaga"])
        await update.message.reply_text(
            "🏙 Shaharni tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    # CITY
    elif text in sum(regions.values(), []):
        user_city[user_id] = text
        user_state[user_id] = "menu"

        keyboard = [
            ["🌤 Hozirgi ob-havo"],
            ["📊 24 soatlik"],
            ["📅 5 kunlik"],
            ["⬅️ Orqaga"]
        ]

        await update.message.reply_text(
            f"✅ {text} tanlandi\n\nEndi bo‘limni tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    # BACK
    elif text == "⬅️ Orqaga":
        await start(update, context)

    # HOZIRGI OB HAVO
    elif text == "🌤 Hozirgi ob-havo":
        city = user_city.get(user_id)
        data = get_weather(city)

        temp = data["hourly"]["temperature_2m"][0]
        wind = data["hourly"]["wind_speed_10m"][0]

        await update.message.reply_text(
            f"🌤 {city}\n\n🌡 Harorat: {temp}°C\n🌬 Shamol: {wind} m/s"
        )

    # 24 SOATLIK
    elif text == "📊 24 soatlik":
        city = user_city.get(user_id)
        data = get_weather(city)

        msg = "📊 24 soatlik:\n\n"

        for i in range(24):
            time = data["hourly"]["time"][i][11:16]
            temp = data["hourly"]["temperature_2m"][i]
            msg += f"{time} | {temp}°C\n"

        await update.message.reply_text(msg)

    # 5 KUNLIK GRAFIK
    elif text == "📅 5 kunlik":
        city = user_city.get(user_id)
        data = get_weather(city)

        temps = data["hourly"]["temperature_2m"][:120]

        plt.figure()
        plt.plot(temps)
        plt.title(f"{city} 5 kunlik")
        plt.xlabel("Soat")
        plt.ylabel("Temp")

        file = f"{city}.png"
        plt.savefig(file)
        plt.close()

        await update.message.reply_photo(photo=open(file, "rb"))
        os.remove(file)


# ALERT
async def weather_alerts(app):
    for user_id, city in user_city.items():

        data = get_weather(city)
        if not data:
            continue

        temp = data["hourly"]["temperature_2m"]
        rain = data["hourly"]["precipitation_probability"]
        wind = data["hourly"]["wind_speed_10m"]

        alerts = []

        if any(r > 60 for r in rain[24:48]):
            alerts.append("🌧 Yomg‘ir ehtimoli bor")

        if any(w > 25 for w in wind[24:48]):
            alerts.append("🌬 Kuchli shamol")

        if any(t < 0 for t in temp[24:48]):
            alerts.append("❄ Sovuq")

        if alerts:
            msg = "🚨 ALERT\n\n" + "\n".join(alerts)
            await app.bot.send_message(user_id, msg)


# DAILY WEATHER
async def daily_weather(app):
    for user_id, city in user_city.items():

        data = get_weather(city)
        hourly = data["hourly"]

        msg = f"🌤 BUGUN ({city})\n\n"

        for i in range(8, 24):
            time = hourly["time"][i][11:16]
            temp = hourly["temperature_2m"][i]
            wind = hourly["wind_speed_10m"][i]
            rain = hourly["precipitation_probability"][i]

            msg += f"{time} | 🌡 {temp}°C | 🌬 {wind} m/s | ☔ {rain}%\n"

        await app.bot.send_message(user_id, msg)


# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: app.create_task(daily_weather(app)), "cron", hour=8, minute=0)
    scheduler.add_job(lambda: app.create_task(weather_alerts(app)), "cron", hour=20, minute=0)
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
