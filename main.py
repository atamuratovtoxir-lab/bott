import aiohttp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "8750583800:AAGWDecP47uPEfcYIrZamE45aHpJsxF2RUA"

user_city = {}
user_region = {}
scheduler = AsyncIOScheduler()

# 📍 REGIONLAR
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

# 📍 KOORDINATALAR
city_coords = {
    "Toshkent": (41.2995, 69.2401),
    "Chirchiq": (41.4689, 69.5822),
    "Angren": (41.0167, 70.1436),
    "Samarqand": (39.6547, 66.9750),
    "Urgut": (39.4022, 67.2433),
    "Kattaqo‘rg‘on": (39.9000, 66.2667),
    "Buxoro": (39.7747, 64.4286),
    "G‘ijduvon": (40.1000, 64.6833),
    "Kogon": (39.7228, 64.5519),
    "Andijon": (40.7821, 72.3442),
    "Asaka": (40.6500, 72.2333),
    "Shahrixon": (40.7167, 72.0500),
    "Farg‘ona": (40.3842, 71.7843),
    "Qo‘qon": (40.5286, 70.9425),
    "Marg‘ilon": (40.4722, 71.7247),
    "Namangan": (41.0058, 71.6436),
    "Chortoq": (41.0333, 71.8333),
    "Kosonsoy": (41.2500, 71.5500),
    "Urganch": (41.5500, 60.6333),
    "Xiva": (41.3783, 60.3633),
    "Xonqa": (41.4500, 60.7833),
    "Qarshi": (38.8606, 65.7891),
    "Shahrisabz": (39.0572, 66.8342),
    "Kitob": (39.0842, 66.8333),
    "Termiz": (37.2242, 67.2783),
    "Denov": (38.2667, 67.9000),
    "Boysun": (38.2000, 67.2000),
    "Jizzax": (40.1158, 67.8422),
    "Zomin": (39.9417, 68.3958),
    "G‘allaorol": (40.0667, 67.5833),
    "Navoiy": (40.0844, 65.3792),
    "Zarafshon": (41.5675, 64.2083),
    "Karmana": (40.0833, 65.3667),
    "Nukus": (42.4531, 59.6103),
    "Taxiatosh": (42.0833, 59.2000),
    "Chimboy": (42.9500, 59.0667)
}

# 🌦 API
async def get_weather(city):
    lat, lon = city_coords.get(city, (41, 69))

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,precipitation_probability&daily=temperature_2m_max,temperature_2m_min&timezone=Asia/Tashkent"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

# 📊 5 KUNLIK GRAFIK
async def send_graph(update: Update, context):
    user_id = update.effective_user.id
    city = user_city.get(user_id)

    if not city:
        return await update.message.reply_text("❗ Avval shahar tanlang")

    data = await get_weather(city)

    dates = data["daily"]["time"]
    max_t = data["daily"]["temperature_2m_max"]
    min_t = data["daily"]["temperature_2m_min"]

    plt.figure()
    plt.plot(dates, max_t, label="Max")
    plt.plot(dates, min_t, label="Min")

    plt.title(city)
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    file = "graph.png"
    plt.savefig(file)
    plt.close()

    with open(file, "rb") as f:
        await update.message.reply_photo(f)

    os.remove(file)

# 🌅 DAILY
async def daily_weather(app):
    for user_id, city in user_city.items():
        data = await get_weather(city)
        temps = data["hourly"]["temperature_2m"][:24]
        hours = data["hourly"]["time"][:24]

        msg = f"🌅 {city}\n\n"
        for i in range(24):
            msg += f"{hours[i][11:16]} - {temps[i]}°C\n"

        await app.bot.send_message(user_id, msg)

# 🌧 ALERT
async def rain_alert(app):
    for user_id, city in user_city.items():
        data = await get_weather(city)

        rain = data["hourly"]["precipitation_probability"][:24]
        hours = data["hourly"]["time"][:24]

        for i in range(24):
            if rain[i] >= 60:
                await app.bot.send_message(
                    user_id,
                    f"🌧 Yomg‘ir!\n{city} {hours[i][11:16]} - {rain[i]}%"
                )
                break

# 📌 START
async def start(update: Update, context):
    keyboard = [
        ["🌤 Hozirgi ob-havo"],
        ["📊 24 soat"],
        ["📅 5 kunlik"],
        ["⚙️ Sozlamalar"]
    ]

    await update.message.reply_text(
        "👋 Botga xush kelibsiz!",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ⚙️ SETTINGS
async def settings(update: Update, context):
    keyboard = [
        ["📍 Joy tanlash"],
        ["🔄 Shahar o'zgartirish"]
    ]
    await update.message.reply_text(
        "⚙️ Sozlamalar",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# 📍 REGION
async def choose_region(update):
    keyboard = [[r] for r in regions]
    await update.message.reply_text(
        "📍 Viloyat tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# 📌 MESSAGE
async def handle(update: Update, context):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "⚙️ Sozlamalar":
        return await settings(update, context)

    elif text == "📍 Joy tanlash" or text == "🔄 Shahar o'zgartirish":
        return await choose_region(update)

    elif text in regions:
        keyboard = [[c] for c in regions[text]]
        await update.message.reply_text(
            "🏙 Shahar tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text in city_coords:
        user_city[user_id] = text
        await update.message.reply_text(f"✅ {text} tanlandi")

    elif text == "🌤 Hozirgi ob-havo":
        city = user_city.get(user_id)
        data = await get_weather(city)
        cw = data["current_weather"]

        await update.message.reply_text(
            f"{city}\n🌡 {cw['temperature']}°C\n🌬 {cw['windspeed']}"
        )

    elif text == "📅 5 kunlik":
        await send_graph(update, context)

# 🚀 MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    scheduler.add_job(lambda: app.create_task(daily_weather(app)), "cron", hour=8)
    scheduler.add_job(lambda: app.create_task(rain_alert(app)), "interval", hours=3)

    scheduler.start()

    print("Bot ishladi...")
    app.run_polling()

if __name__ == "__main__":
    main()
