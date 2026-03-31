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
user_state = {}
scheduler = AsyncIOScheduler()

# 📍 REGIONLAR
regions = {
    "Toshkent viloyati": ["Toshkent", "Chirchiq", "Angren", "Olmaliq", "Bekobod"],
    "Samarqand viloyati": ["Samarqand", "Urgut", "Ishtixon", "Kattaqo‘rg‘on"],
    "Farg‘ona viloyati": ["Farg‘ona", "Qo‘qon", "Marg‘ilon", "Rishton"],
    "Andijon viloyati": ["Andijon", "Asaka", "Shahrixon", "Xonobod"],
    "Namangan viloyati": ["Namangan", "Chortoq", "Kosonsoy", "Pop"],
    "Buxoro viloyati": ["Buxoro", "Kogon", "G‘ijduvon"],
    "Navoiy viloyati": ["Navoiy", "Zarafshon", "Karmana"],
    "Qashqadaryo viloyati": ["Qarshi", "Shahrisabz", "Kitob"],
    "Surxondaryo viloyati": ["Termiz", "Denov", "Boysun"],
    "Xorazm viloyati": ["Urganch", "Xiva", "Xonqa"],
    "Jizzax viloyati": ["Jizzax", "Zomin", "G‘allaorol"],
    "Qoraqalpog‘iston": ["Nukus", "Taxiatosh", "Chimboy"]
}

# 🌍 GEO API
async def get_coords(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    if "results" in data and data["results"]:
        return data["results"][0]["latitude"], data["results"][0]["longitude"]

    return None, None

# 🌦 WEATHER
async def get_weather(city):
    lat, lon = await get_coords(city)

    if not lat:
        return None

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,precipitation_probability&daily=temperature_2m_max,temperature_2m_min&timezone=Asia/Tashkent"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

# 📊 GRAPH
async def send_graph(update: Update, context):
    user_id = update.effective_user.id
    city = user_city.get(user_id)

    if not city:
        return await update.message.reply_text("❗ Avval joy tanlang")

    data = await get_weather(city)

    if not data:
        return await update.message.reply_text("❌ Shahar topilmadi")

    dates = data["daily"]["time"]
    max_t = data["daily"]["temperature_2m_max"]
    min_t = data["daily"]["temperature_2m_min"]

    plt.figure(figsize=(8,5))
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

# 🌧 ALERT
async def rain_alert(app):
    for user_id, city in user_city.items():
        data = await get_weather(city)

        if not data:
            continue

        rain = data["hourly"]["precipitation_probability"][:24]
        times = data["hourly"]["time"][:24]

        for i in range(24):
            if rain[i] >= 60:
                await app.bot.send_message(
                    user_id,
                    f"🌧 Yomg‘ir!\n{city} {times[i][11:16]} - {rain[i]}%"
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
        "👋 Salom!\nIstalgan shahar yozing 🌍\nMasalan: Toshkent",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ⚙️ SETTINGS
async def settings(update: Update, context):
    keyboard = [
        ["📍 Joy tanlash"],
        ["🔙 Orqaga"]
    ]

    await update.message.reply_text(
        "⚙️ Sozlamalar",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# 📍 REGION
async def choose_region(update):
    keyboard = [[r] for r in regions]
    keyboard.append(["🔙 Orqaga"])

    await update.message.reply_text(
        "📍 Viloyat tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# 📌 HANDLE
async def handle(update: Update, context):
    text = update.message.text
    user_id = update.effective_user.id

    state = user_state.get(user_id, "main")

    # 🔙 ORQAGA
    if text == "🔙 Orqaga":
        user_state[user_id] = "main"

        keyboard = [
            ["🌤 Hozirgi ob-havo"],
            ["📊 24 soat"],
            ["📅 5 kunlik"],
            ["⚙️ Sozlamalar"]
        ]

        return await update.message.reply_text(
            "🏠 Bosh menyu",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    if text == "⚙️ Sozlamalar":
        return await settings(update, context)

    if text == "📍 Joy tanlash":
        user_state[user_id] = "region"
        return await choose_region(update)

    if text in regions:
        user_state[user_id] = "city"

        keyboard = [[c] for c in regions[text]]
        keyboard.append(["🔙 Orqaga"])

        return await update.message.reply_text(
            "🏙 Shahar tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    # 🌍 SHAHAR SAQLASH
    user_city[user_id] = text
    user_state[user_id] = "main"

    keyboard = [
        ["🌤 Hozirgi ob-havo"],
        ["📊 24 soat"],
        ["📅 5 kunlik"],
        ["⚙️ Sozlamalar"]
    ]

    return await update.message.reply_text(
        f"✅ {text} saqlandi",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# 🚀 MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    scheduler.add_job(lambda: app.create_task(rain_alert(app)), "interval", hours=3)
    scheduler.start()

    print("Bot ishladi...")
    app.run_polling()

if __name__ == "__main__":
    main()
