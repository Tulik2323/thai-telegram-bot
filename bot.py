import os
import threading
import requests
from flask import Flask
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS
import sys
from telegram.error import Conflict

# === Environment variables ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# === Flask dummy server ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Thai Telegram Bot is running with OpenRouter!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask).start()

# === Function: OpenRouter AI ===
def openrouter_generate(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/tulik2323/thai-telegram-bot",
        "X-Title": "Thai Translation Bot"
    }
    data = {
        "model": "mistralai/mistral-7b-instruct",  # אתה יכול לשנות למודל אחר (למשל meta-llama/llama-3-8b-instruct)
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return f"⚠️ OpenRouter Error {response.status_code}: {response.text}"

# === Translate English → Thai ===
async def translate_to_thai(text):
    prompt = (
        f"Translate this English text to Thai and show:\n"
        f"1. Thai translation\n"
        f"2. Transliteration (Latin letters)\n"
        f"3. English meaning\n\n"
        f"Text: {text}"
    )
    return openrouter_generate(prompt)

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
        "👋 Hi! Send me any English sentence and I'll reply in Thai using OpenRouter (Mistral model)."
    )

def main():
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot is running with OpenRouter (Mistral model)...")
    try:
        bot_app.run_polling()
    except Conflict:
        print("⚠️ Another instance is already running. Exiting.")
        sys.exit()

if __name__ == "__main__":
    main()
