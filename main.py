
import os
import json
from flask import Flask, request
import telebot
import google.generativeai as genai

# =============================
# 🔐 CONFIGURATION
# =============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
APP_URL = os.getenv("APP_URL")  # https://yourapp.koyeb.app

OWNER_ID = int(os.getenv("OWNER_ID", "7447651332"))  # your telegram id
ALLOWED_GROUPS = [-1002432150473]  # add your group/channel ids

AUTH_FILE = "authorized_users.json"

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
app = Flask(__name__)

# =============================
# 📁 AUTH FILE HANDLING
# =============================
def load_auth_users():
    if not os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "w") as f:
            json.dump([], f)
    with open(AUTH_FILE, "r") as f:
        return json.load(f)

def save_auth_users(users):
    with open(AUTH_FILE, "w") as f:
        json.dump(users, f)

# =============================
# 🔒 AUTH CHECK
# =============================
def authorized(message):
    cid = message.chat.id
    uid = message.from_user.id
    users = load_auth_users()

    if uid == OWNER_ID or uid in users or cid in ALLOWED_GROUPS:
        return True

    bot.reply_to(message, "🚫 You are not authorized to use this bot.")
    return False

# =============================
# 🧠 AI FEATURES
# =============================

@bot.message_handler(commands=["start"])
def start_cmd(message):
    if not authorized(message): return
    bot.reply_to(message, "👋 Welcome to the Gemini AI Bot!\nUse /ask to ask a question or /image to solve from a photo.")

@bot.message_handler(commands=["ask"])
def ask_cmd(message):
    if not authorized(message): return
    bot.reply_to(message, "🧠 Send your question now...")
    bot.register_next_step_handler(message, handle_question)

def handle_question(message):
    if not authorized(message): return
    question = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content(question)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

@bot.message_handler(commands=["image"])
def image_cmd(message):
    if not authorized(message): return
    bot.reply_to(message, "📸 Please send an image of the question.")

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    if not authorized(message): return
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("temp.jpg", 'wb') as new_file:
            new_file.write(downloaded_file)

        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        img = genai.upload_file("temp.jpg")
        response = model.generate_content(["Explain this question and provide answer in detail.", img])
        bot.reply_to(message, response.text)
        os.remove("temp.jpg")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error processing image: {e}")

# =============================
# 🧾 OWNER COMMANDS
# =============================

@bot.message_handler(commands=["auth"])
def auth_user(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Only the owner can use this command.")
        return

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚙️ Usage: /auth <telegram_id>")
            return

        new_id = int(parts[1])
        users = load_auth_users()
        if new_id not in users:
            users.append(new_id)
            save_auth_users(users)
            bot.reply_to(message, f"✅ User {new_id} authorized successfully.")
        else:
            bot.reply_to(message, "ℹ️ User already authorized.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

@bot.message_handler(commands=["authlist"])
def show_auth_list(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Only the owner can use this command.")
        return

    users = load_auth_users()
    if users:
        bot.reply_to(message, "👥 Authorized Users:\n" + "\n".join(map(str, users)))
    else:
        bot.reply_to(message, "❌ No authorized users yet.")

# =============================
# 🌐 FLASK WEBHOOK
# =============================

@app.route('/')
def home():
    return "🤖 Gemini AI Telegram Bot is live!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# =============================
# 🚀 KOYEB ENTRY POINT
# =============================
if __name__ == "__main__":
    bot.remove_webhook()
    if APP_URL:
        bot.set_webhook(url=f"{APP_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))