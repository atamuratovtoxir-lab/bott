from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8640980822:AAEjmVcoZ0X6PfK0uDA-cT3drqbU_9n6YBU"

SECRET_CODE = "72636288272783838"
admins = set()
users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.add(user_id)

    if user_id in admins:
        await update.message.reply_text("👮 Admin panel")
    else:
        await update.message.reply_text("🇺🇿 Botga xush kelibsiz!")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if text == SECRET_CODE and user_id not in admins:
        admins.add(user_id)
        await update.message.reply_text("✅ Siz ADMIN bo‘ldingiz!")
        return

    if user_id in admins:
        for uid in users:
            try:
                await context.bot.send_message(chat_id=uid, text=text)
            except:
                pass

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 Bot ishga tushdi")

    # ❗ MUHIM: asyncio.run YO‘Q!
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
