import os
import threading
from flask import Flask
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from google.generativeai import GenerativeModel, configure
from gtts import gTTS
import sys
from telegram.error import Conflict

# === Environment variables ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# === Configure Gemini (force v1) ===
configure(api_key=GEMINI_API_KEY)
model = GenerativeModel(model_name="models/gemini-1.5-flash")

# === Flask dummy server (keep-alive for Render) ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Thai Telegram Bot (Gemini 1.5 Flash, v1 API)"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask).start()

# === Translate English → Thai ===
async def translate_to_thai(text):
    prompt = (
        f"Translate this English text to Thai and show:\n"
        f"1. Thai translation\n"
        f"2. Transliteration (Latin)\n"
        f"3. English meaning\n\n"
        f"Text: {text}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()

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
        translation = await translate_to_thai(user_text)
        thai_line = translation.split('\n')[0]
        voice_file = await generate_voice(thai_line)
        await update.message.reply_text(translation)
        await update.message.reply_audio(audio=InputFile(voice_file))
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me any English sentence and I'll reply in Thai (Gemini 1.5 Flash v1)."
    )

def main():
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot is running with Gemini 1.5 Flash (v1 API)...")
    try:
        bot_app.run_polling()
    except Conflict:
        print("⚠️ Another instance is already running. Exiting.")
        sys.exit()

if __name__ == "__main__":
    main()
