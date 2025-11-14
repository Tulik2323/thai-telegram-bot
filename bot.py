import os
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS
from deep_translator import GoogleTranslator
from pythainlp.transliterate import romanize  # for phonetic transcription

# === Environment variables ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://thai-telegram-bot-1.onrender.com")
PORT = int(os.getenv("PORT", "10000"))

# === Translate English → Thai ===
async def translate_to_thai(text):
    thai = GoogleTranslator(source="en", target="th").translate(text)
    phonetic = romanize(thai, engine="royin")  # convert Thai → Latin pronunciation
    formatted = f"🇹🇭 {thai}\n🗣️ {phonetic}\n🇬🇧 {text}"
    return thai, formatted

# === Voice generation ===
def create_voice(thai_text):
    thai_text = thai_text.strip()
    if not thai_text:
        return None
    filename = "thai_voice.mp3"
    tts = gTTS(text=thai_text, lang='th')
    tts.save(filename)
    return filename

# === /start command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me any English sentence and I’ll translate it to Thai, show the pronunciation, and play the voice 🎧"
    )

# === Handle messages ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.chat.send_action("typing")

    try:
        thai, formatted = await translate_to_thai(text)
        await update.message.reply_text(formatted)

        voice = create_voice(thai)
        if voice:
            with open(voice, "rb") as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    filename="thai_voice.mp3",
                    title="Thai Pronunciation 🇹🇭",
                    performer="ThaiBot",
                    caption="🎧 Thai voice"
                )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# === Main ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Starting Telegram Webhook server with Phonetic support...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )

if __name__ == "__main__":
    main()

