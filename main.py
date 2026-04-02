import logging
import aiohttp
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
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
    text = (
        "👋 Assalomu alaykum!\n\n"
        "🤖 Ob-havo botga xush kelibsiz!\n\n"
        "📍 Viloyatni tanlang:"
    )

    keyboard = [[r] for r in regions.keys()]

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ===== API =====
async def get_json(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

# ===== OB-HAVO TEXT =====
def weather_text(desc):
    desc = desc.lower()
    if "clear" in desc:
        return "☀️ ochiq"
    elif "cloud" in desc:
        return "☁️ bulutli"
    elif "rain" in desc:
        return "🌧 yomg‘irli"
    elif "snow" in desc:
        return "❄️ qorli"
    elif "thunder" in desc:
        return "⛈ momaqaldiroqli"
    return desc

# ===== HOZIRGI =====
async def current_weather(update, context):
    city = user_city.get(update.effective_user.id)

    if not city:
        return

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=uz"
    data = await get_json(url)

    temp = data["main"]["temp"]
    desc = data["weather"][0]["main"]

    await update.message.reply_text(
        f"📍 {city}\n🌡 Harorat: {temp}°C\n☁️ Holat: {weather_text(desc)}"
    )

# ===== 24 SOAT =====
async def forecast_24(update, context):
    city = user_city.get(update.effective_user.id)
    if not city:
        return

    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric&lang=uz"
    data = await get_json(url)

    msg = f"🕒 {city} 24 soatlik ob-havo:\n\n"

    for i in range(8):
        item = data["list"][i]
        time = item["dt_txt"][11:16]
        temp = item["main"]["temp"]
        desc = item["weather"][0]["main"]

        msg += f"{time} — {temp}°C ({weather_text(desc)})\n"

    await update.message.reply_text(msg)

# ===== GRAFIK =====
async def graph_5(update, context):
    city = user_city.get(update.effective_user.id)
    if not city:
        return

    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    data = await get_json(url)

    temps = []
    dates = []

    for i in range(0, 40, 8):
        temps.append(data["list"][i]["main"]["temp"])
        dates.append(data["list"][i]["dt_txt"][:10])

    plt.figure()
    plt.plot(dates, temps, marker="o")
    plt.title(f"{city} 5 kunlik ob-havo")
    plt.grid()

    plt.savefig("weather.png")

    await update.message.reply_photo(photo=open("weather.png", "rb"))

# ===== HANDLE =====
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text in regions:
        keyboard = [[c] for c in regions[text]]

        await update.message.reply_text(
            "Shaharni tanlang:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    for cities in regions.values():
        if text in cities:
            user_city[user_id] = text

            keyboard = [
                ["🌤 Hozirgi ob-havo"],
                ["🕒 24 soatlik ob-havo"],
                ["📊 5 kunlik grafik"],
                ["🔄 Shaharni almashtirish"]
            ]

            await update.message.reply_text(
                f"📍 {text} tanlandi!",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            return

    if text == "🌤 Hozirgi ob-havo":
        await current_weather(update, context)

    elif text == "🕒 24 soatlik ob-havo":
        await forecast_24(update, context)

    elif text == "📊 5 kunlik grafik":
        await graph_5(update, context)

    elif text == "🔄 Shaharni almashtirish":
        await start(update, context)

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("🔥 BOT ISHLADI")
    app.run_polling()

if __name__ == "__main__":
    main()
