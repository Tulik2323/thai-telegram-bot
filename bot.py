import os
import threading
from flask import Flask
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
from gtts import gTTS

# === Environment variables ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# === Flask dummy web server (for Render keep-alive) ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Thai Telegram Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# Start Flask server in background
threading.Thread(target=run_flask).start()

# === OpenAI translation function ===
async def translate_to_thai(text):
    prompt = (
        f"Translate the following English text to Thai and provide:\n"
        f"1. Thai translation\n"
        f"2. Transliteration (Latin letters)\n"
        f"3. English meaning\n\n"
        f"Text: {text}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

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

        # Extract first line (Thai) for voice
        thai_line = translation.split('\n')[0]
        voice_file = await generate_voice(thai_line)

        await update.message.rep
