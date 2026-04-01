import asyncio
import aiohttp
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8750583800:AAESA_ESsTR3iX3yJIgt_AzeRASSe1L441Q"

# =========================
# VILOYATLAR + SHAHARLAR
# =========================

CITIES = {
    "Toshkent": {
        "Toshkent": (41.2995, 69.2401),
        "Chirchiq": (41.4700, 69.5820),
        "Angren": (41.0167, 70.1436),
    },
    "Samarqand": {
        "Samarqand": (39.6547, 66.9597),
        "Urgut": (39.4020, 67.2450),
        "Kattaqo‘rg‘on": (39.9000, 66.2600),
    },
    "Buxoro": {
        "Buxoro": (39.7747, 64.4286),
        "Kogon": (39.7210, 64.5460),
        "G‘ijduvon": (40.1000, 64.6800),
    },
    "Andijon": {
        "Andijon": (40.7821, 72.3442),
        "Asaka": (40.6370, 72.2380),
        "Shahrixon": (40.7100, 72.0600),
    },
    "Farg‘ona": {
        "Farg‘ona": (40.3842, 71.7843),
        "Qo‘qon": (40.5286, 70.9425),
        "Marg‘ilon": (40.4720, 71.7246),
    },
    "Namangan": {
        "Namangan": (40.9983, 71.6726),
        "Chortoq": (41.0300, 71.8200),
        "Pop": (40.8730, 71.1080),
    },
    "Qashqadaryo": {
        "Qarshi": (38.8600, 65.7890),
        "Shahrisabz": (39.0520, 66.8340),
        "Kitob": (39.1190, 66.8850),
    },
    "Surxondaryo": {
        "Termiz": (37.2242, 67.2783),
        "Denov": (38.2160, 67.8780),
        "Boysun": (38.2080, 67.2060),
    },
    "Jizzax": {
        "Jizzax": (40.1158, 67.8422),
        "G‘allaorol": (40.0200, 67.4500),
        "Zomin": (39.9600, 68.3950),
    },
    "Sirdaryo": {
        "Guliston": (40.4897, 68.7842),
        "Shirin": (40.2890, 69.1550),
        "Boyovut": (40.1350, 68.7500),
    },
    "Xorazm": {
        "Urganch": (41.5500, 60.6333),
        "Xiva": (41.3783, 60.3639),
        "Hazorasp": (41.3200, 61.0400),
    },
    "Navoiy": {
        "Navoiy": (40.1033, 65.3714),
        "Zarafshon": (41.5530, 64.2060),
        "Karmana": (40.0510, 65.3770),
    },
}

user_data = {}

# =========================
# API
# =========================

async def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m&daily=temperature_2m_max,temperature_2m_min&timezone=Asia/Tashkent"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                print("API STATUS:", r.status)

                if r.status != 200:
                    return None

                data = await r.json()
                print("API OK")
                return data

    except Exception as e:
        print("API ERROR:", e)
        return None

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[city] for city in CITIES.keys()]

    await update.message.reply_text(
        "Shahar tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =========================
# HANDLER
# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    print("USER TEXT:", repr(text))

    # Shahar tanlash
    if text in CITIES:
        user_data[user_id] = {"region": text}

        keyboard = [
            ["🌤 Hozirgi ob-havo"],
            ["📊 24 soat"],
            ["📅 5 kunlik"]
        ]

        await update.message.reply_text(
            f"{text} tanlandi",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    # Agar shahar tanlanmagan bo‘lsa
    if user_id not in user_data:
        await update.message.reply_text("Avval shahar tanlang!")
        return

    region = user_data[user_id]["region"]

    # Default birinchi shahar
    city = list(CITIES[region].keys())[0]
    lat, lon = CITIES[region][city]

    data = await get_weather(lat, lon)

    if not data:
        await update.message.reply_text("❗ Ob-havo olinmadi (API xato)")
        return

    # =========================
    # HOZIRGI OB-HAVO
    # =========================

    if text == "🌤 Hozirgi ob-havo":
        try:
            cw = data.get("current_weather")

            if not cw:
                await update.message.reply_text("❗ Hozirgi ob-havo yo‘q")
                return

            await update.message.reply_text(
                f"{city}\n🌡 {cw['temperature']}°C\n💨 {cw['windspeed']}"
            )

        except Exception as e:
            print("CURRENT ERROR:", e)
            await update.message.reply_text("❗ Xatolik (current weather)")

    # =========================
    # 24 SOAT
    # =========================

    elif text == "📊 24 soat":
        try:
            msg = ""

            for i in range(24):
                time = data["hourly"]["time"][i][11:16]
                temp = data["hourly"]["temperature_2m"][i]
                msg += f"{time} → {temp}°C\n"

            await update.message.reply_text(msg)

        except Exception as e:
            print("24H ERROR:", e)
            await update.message.reply_text("❗ 24 soat ishlamayapti")

    # =========================
    # 5 KUN
    # =========================

    elif text == "📅 5 kunlik":
        try:
            msg = ""

            for i in range(5):
                day = data["daily"]["time"][i]
                max_t = data["daily"]["temperature_2m_max"][i]
                min_t = data["daily"]["temperature_2m_min"][i]

                msg += f"{day}\n🌡 {min_t}/{max_t}°C\n\n"

            await update.message.reply_text(msg)

        except Exception as e:
            print("5DAY ERROR:", e)
            await update.message.reply_text("❗ 5 kunlik ishlamayapti")

# =========================
# MAIN
# =========================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("BOT ISHLAYAPTI...")
    app.run_polling()

if __name__ == "__main__":
    main()
