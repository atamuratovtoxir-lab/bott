import aiohttp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "8750583800:AAESA_ESsTR3iX3yJIgt_AzeRASSe1L441Q"

user_city = {}
target_user_id = None

# 📍 O‘ZBEKISTON SHAHARLARI
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
    "Jizzax": ["Jizzax", "Zomin", "G‘allaorol"],
    "Qoraqalpog‘iston": ["Nukus", "Taxiatosh", "Chimboy"]
}

UZBEK_CITIES = []
for v in regions.values():
    UZBEK_CITIES.extend(v)

BUTTONS = {
    "🌤 Hozirgi ob-havo",
    "📊 24 soat",
    "📅 5 kunlik",
    "⚙️ Sozlamalar",
    "📍 Joy tanlash",
    "🔙 Orqaga"
}

# 🌍 GEO
async def get_coords(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=uz&format=json"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    if data.get("results"):
        return data["results"][0]["latitude"], data["results"][0]["longitude"]

    return None, None

# 🌦 WEATHER
async def get_weather(city):
    lat, lon = await get_coords(city)

    if not lat:
        return None

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,weathercode&daily=temperature_2m_max,temperature_2m_min&timezone=Asia/Tashkent"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

# 🌧 YOMG‘IR TEKSHIRISH
def check_rain(data):
    codes = data["hourly"]["weathercode"]

    for code in codes[:24]:
        if 51 <= code <= 99:
            return True

    return False

# 📊 GRAPH
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
    plt.plot(dates, max_t)
    plt.plot(dates, min_t)

    plt.title(city)
    plt.xticks(rotation=45)
    plt.tight_layout()

    file = "graph.png"
    plt.savefig(file)
    plt.close()

    with open(file, "rb") as f:
        await update.message.reply_photo(f)

    os.remove(file)

# 📌 START
async def start(update: Update, context):
    global target_user_id
    target_user_id = update.effective_user.id

    keyboard = [
        ["🌤 Hozirgi ob-havo"],
        ["📊 24 soat"],
        ["📅 5 kunlik"],
        ["⚙️ Sozlamalar"]
    ]

    await update.message.reply_text(
        "👋 Salom!\nO‘zbekiston shahrini yozing 🌍",
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

    if text == "🔙 Orqaga":
        return await start(update, context)

    if text == "⚙️ Sozlamalar":
        return await settings(update, context)

    if text == "📍 Joy tanlash":
        return await choose_region(update)

    if text in regions:
        keyboard = [[c] for c in regions[text]]
        keyboard.append(["🔙 Orqaga"])

        return await update.message.reply_text(
            "🏙 Shahar tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    if text == "🌤 Hozirgi ob-havo":
        city = user_city.get(user_id)

        if not city:
            return await update.message.reply_text("❗ Avval shahar tanlang")

        data = await get_weather(city)
        cw = data["current_weather"]

        return await update.message.reply_text(
            f"{city}\n🌡 {cw['temperature']}°C\n🌬 {cw['windspeed']}"
        )

    if text == "📊 24 soat":
        city = user_city.get(user_id)

        if not city:
            return await update.message.reply_text("❗ Avval shahar tanlang")

        data = await get_weather(city)

        msg = f"📊 {city}:\n\n"

        for i in range(24):
            msg += f"{data['hourly']['time'][i][11:16]} - {data['hourly']['temperature_2m'][i]}°C\n"

        return await update.message.reply_text(msg)

    if text == "📅 5 kunlik":
        return await send_graph(update, context)

    # 🌍 SHAHAR SAQLASH
    if text in UZBEK_CITIES:
        user_city[user_id] = text

        return await update.message.reply_text(f"✅ {text} saqlandi")

    if text not in BUTTONS:
        return await update.message.reply_text("❌ Faqat O‘zbekiston shaharlari!")

# 🌅 08:00 + 🌧 CHECK
async def morning_job(context):
    for user_id, city in user_city.items():
        try:
            data = await get_weather(city)
            cw = data["current_weather"]

            await context.bot.send_message(
                chat_id=user_id,
                text=f"🌅 Ertalab\n\n{city}\n🌡 {cw['temperature']}°C"
            )

            if check_rain(data):
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🌧 DIQQAT!\n{city} da yomg‘ir kutilmoqda!"
                )

        except:
            pass

# 🚀 MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(morning_job, "cron", hour=8, minute=0, args=[app])
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("Bot ishladi...")
    app.run_polling()

if __name__ == "__main__":
    main()
