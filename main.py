import aiohttp
import asyncio
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import pytz

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8750583800:AAESA_ESsTR3iX3yJIgt_AzeRASSe1L441Q"
API_KEY = "0ebc0669786259cc3183b9f7d9d33ecd"

logging.basicConfig(level=logging.INFO)

user_city = {}

uzb_tz = pytz.timezone("Asia/Tashkent")

# 🌍 VILOYATLAR
regions = {
    "Toshkent": ["Toshkent", "Chirchiq", "Angren", "Olmaliq", "Bekobod", "Yangiyo‘l"],
    "Samarqand": ["Samarqand", "Urgut", "Kattaqo‘rg‘on", "Jomboy", "Pastdarg‘om"],
    "Buxoro": ["Buxoro", "G‘ijduvon", "Kogon", "Vobkent", "Olot"],
    "Andijon": ["Andijon", "Asaka", "Shahrixon", "Xonobod"],
    "Farg‘ona": ["Farg‘ona", "Qo‘qon", "Marg‘ilon", "Quva", "Rishton"],
    "Namangan": ["Namangan", "Chortoq", "Kosonsoy", "Pop"],
    "Xorazm": ["Urganch", "Xiva", "Xonqa", "Shovot", "Gurlan"],
    "Qashqadaryo": ["Qarshi", "Shahrisabz", "Kitob", "G‘uzor"],
    "Surxondaryo": ["Termiz", "Denov", "Boysun", "Sherobod"],
    "Jizzax": ["Jizzax", "Zomin", "G‘allaorol", "Forish"],
    "Navoiy": ["Navoiy", "Zarafshon", "Karmana", "Uchquduq"],
    "Qoraqalpog‘iston": ["Nukus", "Taxiatosh", "Chimboy", "Beruniy", "Mo‘ynoq"]
}

# 📍 KORDINATALAR (qisqartirmadim)
city_coords = {
    "Toshkent": (41.2995, 69.2401),
    "Chirchiq": (41.4689, 69.5822),
    "Angren": (41.0167, 70.1436),
    "Olmaliq": (40.8447, 69.5970),
    "Bekobod": (40.2208, 69.2697),
    "Yangiyo‘l": (41.1122, 69.0460),

    "Samarqand": (39.6547, 66.9750),
    "Urgut": (39.4022, 67.2433),
    "Kattaqo‘rg‘on": (39.9000, 66.2667),
    "Jomboy": (39.7000, 67.0900),
    "Pastdarg‘om": (39.6500, 66.8000),

    "Buxoro": (39.7747, 64.4286),
    "G‘ijduvon": (40.1000, 64.6833),
    "Kogon": (39.7228, 64.5519),
    "Vobkent": (40.0200, 64.5150),
    "Olot": (39.3800, 63.9200),

    "Andijon": (40.7821, 72.3442),
    "Asaka": (40.6500, 72.2333),
    "Shahrixon": (40.7167, 72.0500),
    "Xonobod": (40.9000, 72.1000),

    "Farg‘ona": (40.3842, 71.7843),
    "Qo‘qon": (40.5286, 70.9425),
    "Marg‘ilon": (40.4722, 71.7247),
    "Quva": (40.5200, 72.0700),
    "Rishton": (40.3600, 71.2100),

    "Namangan": (41.0058, 71.6436),
    "Chortoq": (41.0333, 71.8333),
    "Kosonsoy": (41.2500, 71.5500),
    "Pop": (41.0900, 71.1050),

    "Urganch": (41.5500, 60.6333),
    "Xiva": (41.3783, 60.3633),
    "Xonqa": (41.4500, 60.7833),
    "Shovot": (41.6500, 60.3000),
    "Gurlan": (41.8400, 60.3900),

    "Qarshi": (38.8606, 65.7891),
    "Shahrisabz": (39.0572, 66.8342),
    "Kitob": (39.0842, 66.8333),
    "G‘uzor": (38.6200, 65.8200),

    "Termiz": (37.2242, 67.2783),
    "Denov": (38.2667, 67.9000),
    "Boysun": (38.2000, 67.2000),
    "Sherobod": (37.6600, 67.0000),

    "Jizzax": (40.1158, 67.8422),
    "Zomin": (39.9417, 68.3958),
    "G‘allaorol": (40.0667, 67.5833),
    "Forish": (40.3833, 67.2833),

    "Navoiy": (40.0844, 65.3792),
    "Zarafshon": (41.5675, 64.2083),
    "Karmana": (40.0833, 65.3667),
    "Uchquduq": (42.1500, 63.5500),

    "Nukus": (42.4531, 59.6103),
    "Taxiatosh": (42.0833, 59.2000),
    "Chimboy": (42.9500, 59.0667),
    "Beruniy": (41.6900, 60.7500),
    "Mo‘ynoq": (43.8000, 59.0200)
}

# 🌐 API
async def get_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

# ⏰ AUTO
async def auto_task(app):
    while True:
        now = datetime.now(uzb_tz)

        if now.hour == 8 and now.minute == 0:
            for user_id, city in user_city.items():
                try:
                    lat, lon = city_coords[city]
                    data = await get_weather(lat, lon)

                    temp = data["list"][0]["main"]["temp"]
                    wind = data["list"][0]["wind"]["speed"]
                    desc = data["list"][0]["weather"][0]["description"]

                    text = f"🌤 {city}\n🌡 {temp}°C\n🌬 {wind} m/s\n☁️ {desc}"

                    await app.bot.send_message(user_id, text)
                except:
                    pass

        await asyncio.sleep(60)

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[r] for r in regions.keys()]
    await update.message.reply_text("🏙 Viloyat tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

# HANDLER
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text in regions:
        keyboard = [[c] for c in regions[text]]
        await update.message.reply_text("🏙 Shahar:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif text in city_coords:
        user_city[user_id] = text
        keyboard = [["🌤 Hozir"], ["📊 24 soat"], ["📅 5 kun"], ["⬅️ Orqaga"]]
        await update.message.reply_text(f"✅ {text}", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif text == "🌤 Hozir":
        city = user_city[user_id]
        lat, lon = city_coords[city]
        data = await get_weather(lat, lon)

        d = data["list"][0]
        temp = d["main"]["temp"]
        wind = d["wind"]["speed"]
        desc = d["weather"][0]["description"]

        await update.message.reply_text(f"🌡 {temp}°C\n🌬 {wind} m/s\n☁️ {desc}")

    elif text == "📊 24 soat":
        city = user_city[user_id]
        lat, lon = city_coords[city]
        data = await get_weather(lat, lon)

        msg = ""
        for i in range(8):
            d = data["list"][i]

            time = d["dt_txt"][11:16]
            temp = d["main"]["temp"]
            wind = d["wind"]["speed"]
            desc = d["weather"][0]["description"]

            msg += f"{time} 🌡{temp}°C 🌬{wind}m/s ☁️{desc}\n"

        await update.message.reply_text(msg)

    elif text == "📅 5 kun":
        city = user_city[user_id]
        lat, lon = city_coords[city]
        data = await get_weather(lat, lon)

        temps = [x["main"]["temp"] for x in data["list"][:10]]

        plt.plot(temps)
        file = f"{city}.png"
        plt.savefig(file)
        plt.close()

        await update.message.reply_photo(photo=open(file, "rb"))
        os.remove(file)

    elif text == "⬅️ Orqaga":
        await start(update, context)

# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    loop = asyncio.get_event_loop()
    loop.create_task(auto_task(app))

    print("🔥 BOT READY")
    app.run_polling()

if __name__ == "__main__":
    main()
