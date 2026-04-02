import logging
import aiohttp
import matplotlib.pyplot as plt
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8750583800:AAESA_ESsTR3iX3yJIgt_AzeRASSe1L441Q"
API_KEY = "0ebc0669786259cc3183b9f7d9d33ecd"

logging.basicConfig(level=logging.INFO)

# ===== VILOYATLAR =====
regions = {
    "Toshkent viloyati": ["Tashkent", "Chirchiq", "Angren"],
    "Toshkent shahri": ["Tashkent", "Bektemir", "Almalyk"],
    "Andijon": ["Andijan", "Asaka", "Khanabad"],
    "Farg‘ona": ["Fergana", "Kokand", "Margilan"],
    "Namangan": ["Namangan", "Chust", "Kosonsoy"],
    "Samarqand": ["Samarkand", "Urgut", "Kattakurgan"],
    "Buxoro": ["Bukhara", "Gijduvan", "Kagan"],
    "Xorazm": ["Urgench", "Khiva", "Pitnak"],
    "Qashqadaryo": ["Karshi", "Shahrisabz", "Kitab"],
    "Surxondaryo": ["Termez", "Denau", "Sherabad"],
    "Jizzax": ["Jizzakh", "Zomin", "Gallaorol"],
    "Sirdaryo": ["Gulistan", "Yangiyer", "Shirin"],
    "Navoiy": ["Navoi", "Zarafshan", "Uchkuduk"]
}

user_city = {}

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[r] for r in regions.keys()]
    await update.message.reply_text(
        "Viloyatni tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ===== API =====
async def get_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

# ===== HOZIRGI =====
async def current_weather(update, context):
    city = user_city.get(update.effective_user.id)
    if not city:
        return await update.message.reply_text("Avval shahar tanlang!")

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=uz"
    data = await get_json(url)

    temp = data["main"]["temp"]
    desc = data["weather"][0]["description"]

    await update.message.reply_text(f"{city}\n🌡 {temp}°C\n☁️ {desc}")

# ===== 24 SOAT =====
async def forecast_24(update, context):
    city = user_city.get(update.effective_user.id)
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric&lang=uz"

    data = await get_json(url)

    msg = f"{city} 24 soatlik:\n"
    for i in range(8):
        t = data["list"][i]["main"]["temp"]
        time = data["list"][i]["dt_txt"]
        msg += f"{time} → {t}°C\n"

    await update.message.reply_text(msg)

# ===== GRAFIK =====
async def graph_5(update, context):
    city = user_city.get(update.effective_user.id)
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"

    data = await get_json(url)

    temps, dates = [], []

    for i in range(0, 40, 8):
        temps.append(data["list"][i]["main"]["temp"])
        dates.append(data["list"][i]["dt_txt"][:10])

    plt.figure()
    plt.plot(dates, temps)
    plt.title(f"{city} 5 kunlik ob-havo")
    plt.savefig("weather.png")

    await update.message.reply_photo(photo=open("weather.png", "rb"))

# ===== HANDLE =====
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # viloyat
    if text in regions:
        keyboard = [[c] for c in regions[text]]
        return await update.message.reply_text(
            "Shaharni tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    # shahar
    for cities in regions.values():
        if text in cities:
            user_city[user_id] = text

            keyboard = [
                ["🌤 Hozirgi ob-havo"],
                ["🕒 24 soatlik ob-havo"],
                ["📊 5 kunlik grafik"],
                ["🔄 Shaharni almashtirish"]
            ]

            return await update.message.reply_text(
                f"{text} tanlandi!",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )

    # tugmalar
    if text == "🌤 Hozirgi ob-havo":
        return await current_weather(update, context)

    if text == "🕒 24 soatlik ob-havo":
        return await forecast_24(update, context)

    if text == "📊 5 kunlik grafik":
        return await graph_5(update, context)

    if text == "🔄 Shaharni almashtirish":
        return await start(update, context)

# ===== AVTO YUBORISH =====
async def daily_weather(app):
    for user_id, city in user_city.items():
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        data = await get_json(url)

        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]

        await app.bot.send_message(
            chat_id=user_id,
            text=f"🌅 Bugungi ob-havo ({city})\n🌡 {temp}°C\n☁️ {desc}"
        )

# ===== YOMG‘IR ALERT =====
async def rain_alert(app):
    for user_id, city in user_city.items():
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        data = await get_json(url)

        for item in data["list"][:8]:
            if "rain" in item:
                await app.bot.send_message(
                    chat_id=user_id,
                    text=f"🌧 DIQQAT! {city} da yomg‘ir kutilmoqda!"
                )
                break

# ===== MAIN =====
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: daily_weather(app), "cron", hour=8, minute=0)
    scheduler.add_job(lambda: rain_alert(app), "interval", hours=3)
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("🔥 BOT ISHGA TUSHDI")
    app.run_polling()
