import os
import telebot
import google.generativeai as genai
from flask import Flask, request

# 🔑 Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "7447651332"))
GROUP_ID = int(os.getenv("GROUP_ID", "-1002432150473"))

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# Flask app for webhook (Koyeb)
app = Flask(__name__)

@app.route("/" + BOT_TOKEN, methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200


# 🟢 /start command
@bot.message_handler(commands=["start"])
def start(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "👋 AI Doubt Solver Active!\nUse /ask for text questions or /image for photo-based ones.")
    else:
        bot.reply_to(message, "⚠️ Access Denied! Only owner or allowed group can use this bot.")


# 🧠 /ask command
@bot.message_handler(commands=["ask"])
def ask_cmd(message):
    if message.chat.id != GROUP_ID and message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⛔ Access denied.")
        return
    bot.reply_to(message, "🧠 Send your question now...")
    bot.register_next_step_handler(message, handle_question)


def handle_question(message):
    question = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content(question)
        bot.reply_to(message, f"💡 Answer:\n{response.text}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")


# 📸 /image command
@bot.message_handler(commands=["image"])
def image_cmd(message):
    if message.chat.id != GROUP_ID and message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⛔ Access denied.")
        return
    bot.reply_to(message, "📸 Please send the image of your question.")


@bot.message_handler(content_types=["photo"])
def handle_image(message):
    if message.chat.id != GROUP_ID and message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⛔ Access denied.")
        return
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("temp.jpg", "wb") as f:
            f.write(downloaded_file)

        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        img = genai.upload_file("temp.jpg")
        response = model.generate_content(["Explain and solve this question in Gujarati.", img])
        bot.reply_to(message, response.text)
        os.remove("temp.jpg")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error processing image: {e}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)