
import telebot
import google.generativeai as genai
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Welcome!\nUse /ask to ask any question or /image to solve from a photo.")

@bot.message_handler(commands=['ask'])
def ask_cmd(message):
    bot.reply_to(message, "🧠 Send your question now...")
    bot.register_next_step_handler(message, handle_question)

def handle_question(message):
    question = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content(question)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

@bot.message_handler(commands=['image'])
def image_cmd(message):
    bot.reply_to(message, "📸 Please send an image of the question.")

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("temp.jpg", 'wb') as new_file:
            new_file.write(downloaded_file)

        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        img = genai.upload_file("temp.jpg")
        response = model.generate_content(["Explain the question and give answer.", img])
        bot.reply_to(message, response.text)
        os.remove("temp.jpg")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error processing image: {e}")

bot.polling()
