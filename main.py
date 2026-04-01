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

# 📍 REGION + SHAHAR + KOORDINATA
regions = {
    "Toshkent viloyati": {
        "Toshkent": (41.31, 69.24), "Chirchiq": (41.47, 69.58),
        "Angren": (41.02, 70.14), "Olmaliq": (40.85, 69.60), "Bekobod": (40.22, 69.27)
    },
    "Samarqand viloyati": {
        "Samarqand": (39.65, 66.97), "Urgut": (39.40, 67.25),
        "Ishtixon": (39.97, 66.49), "Kattaqo‘rg‘on": (39.90, 66.26)
    },
    "Farg‘ona viloyati": {
        "Farg‘ona": (40.39, 71.78), "Qo‘qon": (40.52, 70.94),
        "Marg‘ilon": (40.47, 71.72), "Rishton": (40.35, 71.28)
    },
    "Andijon viloyati": {
        "Andijon": (40.78, 72.34), "Asaka": (40.64, 72.24),
        "Shahrixon": (40.71, 72.06), "Xonobod": (40.80, 72.97)
    },
    "Namangan viloyati": {
        "Namangan": (41.00, 71.67), "Chortoq": (41.07, 71.82),
        "Kosonsoy": (41.25, 71.55), "Pop": (40.87, 71.11)
    },
    "Buxoro viloyati": {
        "Buxoro": (39.77, 64.42), "Kogon": (39.72, 64.55),
        "G‘ijduvon": (40.10, 64.68)
    },
    "Navoiy viloyati": {
        "Navoiy": (40.10, 65.37), "Zarafshon": (41.57, 64.23),
        "Karmana": (40.09, 65.38)
    },
    "Qashqadaryo viloyati": {
        "Qarshi": (38.86, 65.79), "Shahrisabz": (39.05, 66.83),
        "Kitob": (39.12, 66.88)
    },
    "Surxondaryo viloyati": {
        "Termiz": (37.22, 67.28), "Denov": (38.27, 67.90),
        "Boysun": (38.20, 67.20)
    },
    "Xorazm viloyati": {
        "Urganch": (41.55, 60.63), "Xiva": (41.38, 60.36),
        "Xonqa": (41.47, 60.78)
    },
    "Jizzax": {
        "Jizzax": (40.12, 67.84), "Zomin": (39.96, 68.40),
        "G‘allaorol": (40.02, 67.60)
    },
    "Qoraqalpog‘iston": {
        "Nukus": (42.46, 59.61), "Taxiatosh": (42.32, 59.60),
        "Chimboy": (42.93, 59.77)
    }
}

# 🌦 WEATHER
async def get_weather(city):
    for r in regions.values():
        if city in r:
            lat, lon = r[city]

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,weathercode,precipitation_probability&daily=temperature_2m_max,temperature_2m_min&timezone=Asia/Tashkent"

    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            return await r.json()

# 🌧 SMART ALERT
def rain_alert(data, city):
    for i in range(48):
        code = data["hourly"]["weathercode"][i]
        if 51 <= code <= 99:
            t = data["hourly"]["time"][i]
            prob = data["hourly"]["precipitation_probability"][i]
            return f"""🌧 DIQQAT!

📍 {city}
📅 {t[:10]}
⏰ {t[11:16]}

Yomg‘ir ehtimoli: {prob}%"""
    return None

# 📊 GRAFIK
async def graph(update, city):
    data = await get_weather(city)

    dates = data["daily"]["time"]
    max_t = data["daily"]["temperature_2m_max"]
    min_t = data["daily"]["temperature_2m_min"]

    plt.figure()
    plt.plot(dates, max_t)
    plt.plot(dates, min_t)
    plt.xticks(rotation=45)
    plt.tight_layout()

    file = "g.png"
    plt.savefig(file)
    plt.close()

    with open(file, "rb") as f:
        await update.message.reply_photo(f)

    os.remove(file)

# 📌 MENYU
def main_menu():
    return ReplyKeyboardMarkup([
        ["🌤 Hozirgi ob-havo", "📊 24 soat"],
        ["📅 5 kunlik", "⚙️ Sozlamalar"]
    ], resize_keyboard=True)

# 🚀 START
async def start(update: Update, context):
    name = update.effective_user.first_name

    await update.message.reply_text(
        f"👋 Salom {name}!\n\nOb-havo olish uchun viloyat/shahar tanlang!",
        reply_markup=ReplyKeyboardMarkup([["📍 Belgilash"]], resize_keyboard=True)
    )

# 📍 REGION MENU
async def regions_menu(update):
    kb = [[r] for r in regions]
    kb.append(["🔙 Orqaga"])
    await update.message.reply_text("📍 Viloyat tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

# ⚙️ SETTINGS
async def settings(update):
    kb = [["🔄 Shaharni almashtirish"], ["🔙 Orqaga"]]
    await update.message.reply_text("⚙️ Sozlamalar", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

# 🎯 HANDLE
async def handle(update: Update, context):
    text = update.message.text
    uid = update.effective_user.id

    if text == "🔙 Orqaga":
        if uid in user_city:
            return await update.message.reply_text("🏠 Bosh menyu", reply_markup=main_menu())
        else:
            return await start(update, context)

    if text == "📍 Belgilash":
        return await regions_menu(update)

    if text == "⚙️ Sozlamalar":
        return await settings(update)

    if text == "🔄 Shaharni almashtirish":
        return await regions_menu(update)

    if text in regions:
        kb = [[c] for c in regions[text]]
        kb.append(["🔙 Orqaga"])
        return await update.message.reply_text("🏙 Shahar tanlang:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    for r in regions.values():
        if text in r:
            user_city[uid] = text
            return await update.message.reply_text(f"✅ {text} saqlandi", reply_markup=main_menu())

    city = user_city.get(uid)
    if not city:
        return await update.message.reply_text("❗ Avval shahar tanlang")

    data = await get_weather(city)

    if text == "🌤 Hozirgi ob-havo":
        cw = data["current_weather"]
        msg = f"""📍 {city}

🌡 {cw['temperature']}°C
💨 {cw['windspeed']} km/h"""
        alert = rain_alert(data, city)
        if alert:
            msg += "\n\n" + alert
        return await update.message.reply_text(msg)

    if text == "📊 24 soat":
        msg = f"📊 {city}\n\n"
        for i in range(24):
            t = data["hourly"]["time"][i][11:16]
            temp = data["hourly"]["temperature_2m"][i]
            msg += f"{t} → {temp}°C\n"
        return await update.message.reply_text(msg)

    if text == "📅 5 kunlik":
        return await graph(update, city)

# 🌅 AUTO XABAR
async def morning_job(context):
    for uid, city in user_city.items():
        try:
            data = await get_weather(city)
            cw = data["current_weather"]

            await context.bot.send_message(
                chat_id=uid,
                text=f"🌅 {city}\n🌡 {cw['temperature']}°C"
            )

            alert = rain_alert(data, city)
            if alert:
                await context.bot.send_message(chat_id=uid, text=alert)

        except:
            pass

# 🚀 RUN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(morning_job, "cron", hour=8, minute=0, args=[app])
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("🔥 BOT ISHLADI")
    app.run_polling()

if __name__ == "__main__":
    main()
