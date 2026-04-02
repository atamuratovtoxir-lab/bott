import logging
import os
import aiohttp
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler
)

# ================== CONFIG ==================
TOKEN = "8750583800:AAESA_ESsTR3iX3yJIgt_AzeRASSe1L441Q"
API_KEY = "0ebc0669786259cc3183b9f7d9d33ecd"

ADMIN_SECRET = "54776+;5+-'zruobtyivvhuj"

admin_users = set()
user_city = {}
blocked_users = set()

# ================== REGIONS ==================
regions = {
    "Toshkent": ["Toshkent", "Chirchiq", "Angren"],
    "Samarqand": ["Samarqand", "Kattaqo‘rg‘on", "Urgut"],
    "Buxoro": ["Buxoro", "Kogon", "G‘ijduvon"],
    "Xorazm": ["Urganch", "Xiva", "Hazorasp"],
    "Farg‘ona": ["Farg‘ona", "Marg‘ilon", "Qo‘qon"],
    "Namangan": ["Namangan", "Chortoq", "Pop"],
    "Andijon": ["Andijon", "Asaka", "Shahrixon"],
    "Qashqadaryo": ["Qarshi", "Shahrisabz", "Koson"],
    "Surxondaryo": ["Termiz", "Denov", "Sherobod"],
    "Jizzax": ["Jizzax", "G‘allaorol", "Do‘stlik"],
    "Navoiy": ["Navoiy", "Zarafshon", "Uchkuduk"],
    "Qoraqalpog‘iston": ["Nukus", "Taxiatosh", "Chimboy"]
}

# ================== HELPERS ==================
def is_admin(user_id):
    return user_id in admin_users

async def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},UZ&appid={API_KEY}&units=metric"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]

            if "rain" in desc:
                uz = "Yomg‘irli"
            elif "clear" in desc:
                uz = "Ochiq"
            elif "cloud" in desc:
                uz = "Bulutli"
            else:
                uz = desc

            return f"{temp}°C ({uz})"

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(r, callback_data=f"region|{r}")]
        for r in regions
    ]

    await update.message.reply_text(
        "👋 Assalomu alaykum!\nViloyatni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== CALLBACK ==================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    uid = query.from_user.id

    if data.startswith("region"):
        region = data.split("|")[1]

        buttons = [
            [InlineKeyboardButton(city, callback_data=f"city|{city}")]
            for city in regions[region]
        ]

        await query.edit_message_text(
            f"{region} → Shahar tanlang:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("city"):
        city = data.split("|")[1]
        user_city[uid] = city

        weather = await get_weather(city)
        now = datetime.now().strftime("%H:%M")

        text = f"""
🏙 Shahar: {city}
🕒 Vaqt: {now}

🌤 Ob-havo:
{weather}
"""

        await query.edit_message_text(text)

# ================== ADMIN CODE ==================
async def admin_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return

    code = context.args[0]

    if code == ADMIN_SECRET:
        admin_users.add(update.effective_user.id)
        await update.message.reply_text("👑 Admin bo‘ldingiz!")
    else:
        await update.message.reply_text("❌ Kod noto‘g‘ri")

# ================== PANEL ==================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    await update.message.reply_text(
        "👑 ADMIN PANEL\n\n"
        "/users\n"
        "/broadcast text\n"
        "/block id\n"
        "/unblock id\n"
        "/send id text\n"
        "/restart"
    )

# ================== BROADCAST ==================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    text = " ".join(context.args)

    for uid in user_city:
        await context.bot.send_message(uid, f"📢 {text}")

# ================== USERS ==================
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    text = "👥 Users:\n"
    for uid, city in user_city.items():
        text += f"{uid} → {city}\n"

    await update.message.reply_text(text)

# ================== BLOCK ==================
async def block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    uid = int(context.args[0])
    blocked_users.add(uid)

    await update.message.reply_text("⛔ Block")

# ================== UNBLOCK ==================
async def unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    uid = int(context.args[0])
    blocked_users.discard(uid)

    await update.message.reply_text("🔓 Unblock")

# ================== SEND ==================
async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    uid = int(context.args[0])
    text = " ".join(context.args[1:])

    await context.bot.send_message(uid, text)

# ================== RESTART ==================
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    await update.message.reply_text("♻️ Restart")
    os.execv("python", ["python"] + ["main.py"])

# ================== TEXT ==================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid in blocked_users:
        return

    if uid not in user_city:
        user_city[uid] = update.message.text
        await update.message.reply_text("📍 Shahar saqlandi")

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("code", admin_code))
    app.add_handler(CommandHandler("panel", panel))

    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("block", block))
    app.add_handler(CommandHandler("unblock", unblock))
    app.add_handler(CommandHandler("send", send))
    app.add_handler(CommandHandler("restart", restart))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🤖 Bot ishlayapti...")
    app.run_polling()

if __name__ == "__main__":
    main()
