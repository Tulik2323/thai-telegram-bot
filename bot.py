import os
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from gtts import gTTS
import threading
from flask import Flask

# === Environment variables ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# === Function to translate English → Thai ===
async def translate_to_thai(text):
    prompt = f"Translate the following English text to Thai and provide:\n1. Thai translation\n2. Transliteration (Latin letters)\n3. English meaning\n\nText: {text}"
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

# === Voice generation ===
async def generate_voice(thai_text):
    tts = gTTS(text=thai_text, lang='th')
    filename = "thai_voice.mp3"
    tts.save(filename)
    return filename

# === Handler for user messages ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.chat.send_action("typing")

    translation = await translate_to_thai(user_text)

    # Try to extract Thai line for voice
    thai_line = translation.split('\n')[0]
    voice_file = await generate_voice(thai_line)

    await update.message.reply_text(translation)
    await update.message.reply_audio(audio=InputFile(voice_file))

# === Start command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! Send me any English sentence and I'll reply in Thai with translation and pronunciation.")

# ====== DUMMY WEB SERVER (for Render free plan) ======
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Thai Telegram Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# === Main ===
def main():
    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running...")

    # Start Flask in background thread
    threading.Thread(target=run_flask, daemon=True).start()

    bot_app.run_polling()

if __name__ == "__main__":
    main()
