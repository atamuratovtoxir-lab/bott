import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8640980822:AAEjmVcoZ0X6PfK0uDA-cT3drqbU_9n6YBU"

SECRET_CODE = "72636288272783838"
admins = set()
users = set()

logging.basicConfig(level=logging.INFO)

# MENU
def menu():
    return ReplyKeyboardMarkup(
        [["📰 Yangiliklar"]],
        resize_keyboard=True
    )

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.add(user_id)

    if user_id in admins:
        await update.message.reply_text(
            "👮 Admin panelga xush kelibsiz!",
            reply_markup=menu()
        )
    else:
        await update.message.reply_text(
            "🇺🇿 WERTU | NEWS\n\n"
            "📢 Siz yangiliklarni olasiz.",
            reply_markup=menu()
        )

# Xabarlar
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Admin qilish kodi
    if text == SECRET_CODE and user_id not in admins:
        admins.add(user_id)

        await update.message.reply_text("✅ Siz ADMIN bo‘ldingiz!")
        return

    # Agar admin bo‘lsa → broadcast
    if user_id in admins:
        for uid in users:
            try:
                await context.bot.send_message(chat_id=uid, text=text)
            except:
                pass
        return

    # Oddiy user
    if text == "📰 Yangiliklar":
        await update.message.reply_text("📰 Hozir yangiliklar yo‘q.")

# MAIN
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 Bot ishga tushdi")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
