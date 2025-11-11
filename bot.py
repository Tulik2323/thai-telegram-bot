import os
import threading
from flask import Flask
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS
from deep_translator import GoogleTranslator
import sys
from telegram.error import Conflict

# === Environment variables ===
BOT_TOKEN = os.getenv("BOT_TOKEN")

# === Flask dummy server ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Thai Telegram Bot is running with Deep Translator!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask).start()

# === Translate English → Thai ===
async def translate_to_thai(text):
    thai_text = GoogleTranslator(source='en', target='th').translate(text)
    translation = f"🇹🇭 {thai_text}\n🇬🇧 {text}"
    return thai_text, translation

# === Voice ===
async def generate_voice(thai_text):
    tts = gTTS(text=thai_text, lang='th')
    filename = "thai_voice.mp3"
    tts.save(filename)
    return filename

# === Telegram handler ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.chat.send_action("typing")
    try:
        thai_text, translation = await translate_to_thai(user_text)
        voice_file = await generate_voice(thai_text)
        await update.message.reply_text(translation)
        await update.message.reply_audio(audio=InputFile(voice_file))
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# === /start command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me any English sentence and I'll translate it to Thai using Google Translate."
    )

# === Main entrypoint ===
def main():
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot is running with Deep Translator...")
    try:
        bot_app.run_polling()
    except Conflict:
        print("⚠️ Another instance is already running. Exiting.")
        sys.exit()

if __name__ == "__main__":
    main()
