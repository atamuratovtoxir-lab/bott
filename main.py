import aiohttp
from datetime import datetime, timedelta
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "8750583800:AAESA_ESsTR3iX3yJIgt_AzeRASSe1L441Q"
API_KEY = "0ebc0669786259cc3183b9f7d9d33ecd"

ADMIN_PASSWORD = "54776+;5+-'zruobtyivvhuj"

admin_users = set()
user_city = {}

# ================== REGION ==================
regions = {
    "Toshkent": ["Toshkent", "Chirchiq", "Angren"],
    "Samarqand": ["Samarqand", "Urgut", "Kattaqo‘rg‘on"],
    "Xorazm": ["Urgench", "Xiva", "Hazorasp"],
    "Buxoro": ["Buxoro", "G‘ijduvon", "Kogon"],
    "Farg‘ona": ["Farg‘ona", "Marg‘ilon", "Qo‘qon"],
    "Andijon": ["Andijon", "Asaka", "Xonobod"],
    "Namangan": ["Namangan", "Pop", "Chortoq"],
    "Qashqadaryo": ["Qarshi", "Shahrisabz", "Koson"],
    "Surxondaryo": ["Termiz", "Denov", "Boysun"],
    "Jizzax": ["Jizzax", "Zomin", "G‘allaorol"],
    "Navoiy": ["Navoiy", "Zarafshon", "Karmana"],
    "Qoraqalpog‘iston": ["Nukus", "To‘rtko‘l", "Chimboy"]
}

# ================== TIME ==================
def uz_time():
    return (datetime.utcnow() + timedelta(hours=5)).strftime("%d.%m.%Y %H:%M")

# ================== WEATHER ==================
async def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},UZ&appid={API_KEY}&units=metric&lang=uz"

    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            d = await r.json()

    temp = d["main"]["temp"]
    desc = d["weather"][0]["description"]

    if "rain" in desc:
        emoji = "🌧"
    elif "cloud" in desc:
        emoji = "☁️"
    else:
        emoji = "☀️"

    return temp, desc, emoji

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [[r] for r in regions]

    await update.message.reply_text(
        "🤖 ULTRA WEATHER BOT\n\n📍 Viloyatni tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ================== ADMIN PANEL ==================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 Parolni kiriting:")

# ================== HANDLE ==================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    # ADMIN LOGIN
    if text == ADMIN_PASSWORD:
        admin_users.add(uid)
        await update.message.reply_text("👑 Admin panelga kirdingiz!")
        return

    # ADMIN COMMAND
    if uid in admin_users and text.startswith("/broadcast"):
        msg = text.replace("/broadcast", "").strip()

        for u in user_city.keys():
            await context.bot.send_message(u, f"📢 Admin: {msg}")

        return

    # REGION
    if text in regions:
        keyboard = [[c] for c in regions[text]]

        await update.message.reply_text(
            "🏙 Shaharni tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    # CITY
    for cities in regions.values():
        if text in cities:
            user_city[uid] = text

            temp, desc, emoji = await get_weather(text)

            await update.message.reply_text(
f"""
📍 {text}
🕒 {uz_time()}

🌤 Ob-havo:
🌡 {temp}°C
{emoji} {desc}
"""
            )
            return

# ================== FORECAST ==================
async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    city = user_city.get(uid)

    if not city:
        return

    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city},UZ&appid={API_KEY}&units=metric"

    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            d = await r.json()

    text = f"🕒 {city} 24 soat:\n\n"

    for i in d["list"][:8]:
        time = i["dt_txt"][11:16]
        temp = i["main"]["temp"]
        desc = i["weather"][0]["main"]

        text += f"{time} — {temp}°C ({desc})\n"

    await update.message.reply_text(text)

# ================== YOMG'IR ==================
async def rain_check(context):
    for uid, city in user_city.items():

        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city},UZ&appid={API_KEY}&units=metric"

        async with aiohttp.ClientSession() as s:
            async with s.get(url) as r:
                d = await r.json()

        for i in d["list"][:5]:
            if "rain" in i["weather"][0]["main"].lower():
                await context.bot.send_message(
                    uid,
                    f"⚠️ {city} da yomg‘ir bo‘lishi mumkin!"
                )
                break

# ================== DAILY ==================
async def daily(context):

    for uid, city in user_city.items():
        temp, desc, emoji = await get_weather(city)

        await context.bot.send_message(
            uid,
            f"🌅 Kunlik\n📍 {city}\n{emoji} {temp}°C\n{desc}"
        )

# ================== MAIN ==================
def main():

    app = ApplicationBuilder().token(TOKEN).build()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(daily, "cron", hour=8)
    scheduler.add_job(rain_check, "interval", hours=6)
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("forecast", forecast))
    app.add_handler(CommandHandler("adminpanel", admin_panel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🔥 ULTRA BOT RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
