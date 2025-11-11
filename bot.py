import os
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS
from deep_translator import GoogleTranslator

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://thai-telegram-bot-1.onrender.com")
PORT = int(os.getenv("PORT", "10000"))

# --- translate EN -> TH ---
async def translate_to_thai(text: str):
    thai = GoogleTranslator(source="en", target="th").translate(text)
    return thai, f"🇹🇭 {thai}\n🇬🇧 {text}"

# --- TTS ---
def make_tts(th_text: str) -> str | None:
    th_text = (th_text or "").strip()
    if not th_text:
        return None
    fname = "thai_voice.mp3"
    tts = gTTS(text=th_text, lang="th")
    tts.save(fname)
    return fname

# --- handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me any English sentence and I'll translate it to Thai (with audio)."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return
    await update.message.chat.send_action("typing")

    try:
        thai, formatted = await translate_to_thai(text)
        await update.message.reply_text(formatted)

        voice = make_tts(thai)
        if voice:
            await update.message.reply_audio(audio=InputFile(voice))
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Starting webhook server…")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,                       # לא מדפיסים/מראים את הטוקן בלוגים
        webhook_url=f"{WEBHOOK_HOST}/{BOT_TOKEN}" # כתובת השירות שלך ב-Render
    )

if __name__ == "__main__":
    main()
