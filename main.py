import aiohttp
import asyncio

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = "8750583800:AAESA_ESsTR3iX3yJIgt_AzeRASSe1L441Q"

user_city = {}

# 🌍 12 VILOYAT + HAR BIRIDA 3+ SHAHAR + KOORDINATALAR
regions = {
    "Toshkent viloyati": {
        "Toshkent": (41.31, 69.24),
        "Chirchiq": (41.47, 69.58),
        "Angren": (41.02, 70.14)
    },
    "Samarqand viloyati": {
        "Samarqand": (39.65, 66.97),
        "Urgut": (39.40, 67.25),
        "Kattaqo‘rg‘on": (39.90, 66.26)
    },
    "Farg‘ona viloyati": {
        "Farg‘ona": (40.39, 71.78),
        "Qo‘qon": (40.52, 70.94),
        "Marg‘ilon": (40.47, 71.72)
    },
    "Andijon viloyati": {
        "Andijon": (40.78, 72.34),
        "Asaka": (40.64, 72.24),
        "Shahrixon": (40.71, 72.06)
    },
    "Namangan viloyati": {
        "Namangan": (41.00, 71.67),
        "Chortoq": (41.07, 71.82),
        "Pop": (40.87, 71.11)
    },
    "Buxoro viloyati": {
        "Buxoro": (39.77, 64.42),
        "Kogon": (39.72, 64.55),
        "G‘ijduvon": (40.10, 64.68)
    },
    "Navoiy viloyati": {
        "Navoiy": (40.10, 65.37),
        "Zarafshon": (41.57, 64.23),
        "Karmana": (40.09, 65.38)
    },
    "Qashqadaryo viloyati": {
        "Qarshi": (38.86, 65.79),
        "Shahrisabz": (39.05, 66.83),
        "Kitob": (39.12, 66.88)
    },
    "Surxondaryo viloyati": {
        "Termiz": (37.22, 67.28),
        "Denov": (38.27, 67.90),
        "Boysun": (38.20, 67.20)
    },
    "Xorazm viloyati": {
        "Urganch": (41.55, 60.63),
        "Xiva": (41.38, 60.36),
        "Xonqa": (41.47, 60.78)
    },
    "Jizzax": {
        "Jizzax": (40.12, 67.84),
        "Zomin": (39.96, 68.40),
        "G‘allaorol": (40.02, 67.60)
    },
    "Qoraqalpog‘iston": {
        "Nukus": (42.46, 59.61),
        "Taxiatosh": (42.32, 59.60),
        "Chimboy": (42.93, 59.77)
    }
}

# 🌦 OB-HAVO API
async def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m&daily=temperature_2m_max,temperature_2m_min&timezone=Asia/Tashkent"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            return await r.json()

# 📌 MENYU
def main_menu():
    return ReplyKeyboardMarkup([
        ["🌤 Hozirgi ob-havo", "📊 24 soat"],
        ["📅 5 kunlik", "🏠 Orqaga"]
    ], resize_keyboard=True)

# 🚀 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[r] for r in regions.keys()]
    await update.message.reply_text(
        "👋 Viloyatni tanlang:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

# 🎯 HANDLER
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id

    # VILOYAT TANLASH
    if text in regions:
        kb = [[c] for c in regions[text]]
        await update.message.reply_text(
            "🏙 Shaharni tanlang:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    # SHAHAR SAQLASH
    for region in regions.values():
        if text in region:
            user_city[uid] = (text, region[text])
            await update.message.reply_text(
                f"✅ {text} saqlandi",
                reply_markup=main_menu()
            )
            return

    # SHAHAR TANLANMAGAN
    if uid not in user_city:
        await update.message.reply_text("❗ Avval shahar tanlang")
        return

    city, (lat, lon) = user_city[uid]

    data = await get_weather(lat, lon)

    if not data:
        await update.message.reply_text("❗ API ishlamayapti")
        return

    # 🌤 HOZIRGI
    if text == "🌤 Hozirgi ob-havo":
        cw = data["current_weather"]
        await update.message.reply_text(
            f"{city}\n🌡 {cw['temperature']}°C\n💨 {cw['windspeed']}"
        )

    # 📊 24 SOAT
    elif text == "📊 24 soat":
        msg = ""
        for i in range(24):
            t = data["hourly"]["time"][i][11:16]
            temp = data["hourly"]["temperature_2m"][i]
            msg += f"{t} → {temp}°C\n"

        await update.message.reply_text(msg)

    # 📅 5 KUN
    elif text == "📅 5 kunlik":
        msg = ""
        for i in range(5):
            day = data["daily"]["time"][i]
            max_t = data["daily"]["temperature_2m_max"][i]
            min_t = data["daily"]["temperature_2m_min"][i]
            msg += f"{day}\n🌡 {min_t}/{max_t}°C\n\n"

        await update.message.reply_text(msg)

    # 🏠 ORQAGA
    elif text == "🏠 Orqaga":
        kb = [[r] for r in regions.keys()]
        await update.message.reply_text(
            "Viloyatni tanlang:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )

# 🚀 MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🤖 BOT ISHLADI")
    app.run_polling()

if __name__ == "__main__":
    main()
