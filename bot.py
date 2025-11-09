import os
import threading
from flask import Flask
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai
from gtts import gTTS
import sys
from telegram.error import Conflict

# === Environment variables ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# === Configure Gemini ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# === Flask dummy web server (keep-alive for Render) ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Thai Telegram Bot is running with Gemini (gemini-pro)!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# Start Flask in background
threading.Thread(target=run_flask).start()

# === Translation using Gemini ===
async def translate_to_thai(text):
    prompt = (
        f"Translate the following English text to Thai and provide:\n"
        f"1. Thai translation\n"
        f"2. Transliteration (Latin letters)\n"
        f"3. English meaning\n\n"
        f"Text: {text}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()

# === Voice generation ===
async def generate_voice(thai_text):
    tts = gTTS(text=thai_text, lang='th')
    filename = "thai_voice.mp3"
    tts.save(filename)
    return filename

# === Telegram message handler ===
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

# === /start command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me any English sentence and I'll reply in Thai (via Gemini-pro) with translation and pronunciation."
    )

# === Main entrypoint ===
def main():
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot is running with Gemini (gemini-pro)...")
    try:
        app_telegram.run_polling()
    except Conflict:
        print("⚠️ Another instance is already running. Exiting.")
        sys.exit()

if __name__ == "__main__":
    main()
