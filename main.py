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
daily_users = set()

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

# 🔥 ASYNC API
async def get_weather(city):
    lat, lon = city_coords.get(city, (41, 69))
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability,wind_speed_10m&timezone=Asia/Tashkent"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[r] for r in regions.keys()]
    await update.message.reply_text(
        "🏙 Viloyatni tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    print(f"Keldi: {repr(text)}")
    user_id = update.effective_user.id

    daily_users.add(user_id)

    if text in regions:
        keyboard = [[c] for c in regions[text]]
        await update.message.reply_text(
            "🏙 Shaharni tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text in city_coords:
        user_city[user_id] = text

        keyboard = [
            ["🌤 Hozirgi ob-havo"],
            ["📊 24 soatlik"],
            ["📅 5 kunlik"],
            ["⬅️ Orqaga"]
        ]

        await update.message.reply_text(
            f"✅ {text} tanlandi",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text == "🌤 Hozirgi ob-havo":
        city = user_city.get(user_id)
        if not city:
            await update.message.reply_text("❗ Avval shahar tanlang")
            return

        data = await get_weather(city)
        if not data:
            await update.message.reply_text("❗ Ob-havo olinmadi")
            return

        temp = data["hourly"]["temperature_2m"][0]
        wind = data["hourly"]["wind_speed_10m"][0]

        await update.message.reply_text(f"🌤 {city}\n🌡 {temp}°C\n🌬 {wind} m/s")

    elif text == "📊 24 soatlik":
        city = user_city.get(user_id)
        data = await get_weather(city)

        if not data:
            await update.message.reply_text("❗ Ob-havo olinmadi")
            return

        msg = "📊 24 soat\n\n"
        hours = data["hourly"]["time"]
        temps = data["hourly"]["temperature_2m"]

        for i in range(8, 24):
            msg += f"{hours[i][11:16]} - {temps[i]}°C\n"

        await update.message.reply_text(msg)

    elif text == "📅 5 kunlik":
        city = user_city.get(user_id)
        data = await get_weather(city)

        if not data:
            await update.message.reply_text("❗ Ob-havo olinmadi")
            return

        temps = data["hourly"]["temperature_2m"][:120]

        plt.plot(temps)
        file = f"{city}.png"
        plt.savefig(file)
        plt.close()

        await update.message.reply_photo(photo=open(file, "rb"))
        os.remove(file)

    elif text == "⬅️ Orqaga":
        await start(update, context)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot ishladi...")
    app.run_polling()

if __name__ == "__main__":
    main()
