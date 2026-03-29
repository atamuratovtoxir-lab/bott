import os
import re
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN ="8748481611:AAE_UMeNiPb9XNpuxeJzj119KcogWokixuw"

def download_video(url):
    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'format': 'best[height<=720]/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for file in os.listdir():
        if file.startswith("video"):
            return file

    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom!\n\n"
        "🤖 Men video yuklovchi botman.\n"
        "📥 YouTube yoki Instagram link yuboring.\n"
        "⚡ Men 720p sifatda tez yuklab beraman!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if re.search(r'http', text):
        await update.message.reply_text("⚡ Yuklanmoqda...")

        try:
            file_path = download_video(text)

            if file_path:
                caption = "📥 Bu bilan yuklandi: @tezda_yuklaydi_yt_insta_bot"

                await update.message.reply_video(
                    video=open(file_path, 'rb'),
                    caption=caption
                )

                os.remove(file_path)
            else:
                await update.message.reply_text("❌ Yuklab bo‘lmadi")
        except Exception as e:
            await update.message.reply_text(f"Xatolik: {str(e)}")
    else:
        await update.message.reply_text("❗ Faqat link yuboring")

app = ApplicationBuilder().token(TOKEN).connect_timeout(30).read_timeout(30).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot ishlayapti...")

app.run_polling()
