import logging
import os
import google.generativeai as genai
import pymongo
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from serpapi import GoogleSearch
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv("key.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Setup Logging
logging.basicConfig(level=logging.INFO)

# Initialize APIs
genai.configure(api_key=GEMINI_API_KEY)
client = pymongo.MongoClient(MONGO_URI)
db = client["telegram_bot"]
users_col = db["users"]
chats_col = db["chats"]
files_col = db["files"]

# Start Command
async def start(update: Update, context: CallbackContext) -> None:  
    user = update.message.from_user
    existing_user = users_col.find_one({"chat_id": user.id})

    if not existing_user:
        users_col.insert_one({"chat_id": user.id, "first_name": user.first_name, "username": user.username})
        await update.message.reply_text(
            "Welcome! Please share your contact using the button below.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Share Contact", request_contact=True)]], one_time_keyboard=True
            )
        )
    else:
        await update.message.reply_text(f"Hey my friend !! Is everything ok?? How can I help you today?")
    
    logging.debug(f"Sent welcome message to {user.username}")

# Handle Contact Info
async def contact_handler(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    phone_number = update.message.contact.phone_number
    users_col.update_one({"chat_id": user.id}, {"$set": {"phone_number": phone_number}})
    await update.message.reply_text("Phone number saved! How can I help you?")


# Chat with Gemini AI
async def chat(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    text = update.message.text

    try:
        # Sending the request to Gemini using the GenerativeModel
        response = model.generate_content(text)

        # Log the response from Gemini for debugging
        logging.info(f"Gemini response: {response}")

        # Check if the response is valid and extract the bot reply
        if response:
            bot_reply = response.text  # Extract the text from the response object
            # Insert the chat data into MongoDB
            chats_col.insert_one({"chat_id": user.id, "user_input": text, "bot_response": bot_reply})
            # Send the response to the user
            await update.message.reply_text(bot_reply)
        else:
            # Handle case where no response is received
            await update.message.reply_text("Sorry, I couldn't get a response from Gemini AI.")
    except Exception as e:
        # Log the full error message and stack trace
        logging.error(f"Error in calling Gemini API: {str(e)}")
        await update.message.reply_text("There was an error while processing your request.")

# Handle Image/File
async def file_handler(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    file = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
    file_path = (await context.bot.get_file(file)).file_path

    try:
        # Describe the image or file using Gemini AI
        analysis = model.generate_content(f"Describe this image: {file_path}")
        bot_reply = analysis.text  # Extract the text description of the file/image
        
        # Insert the file data and analysis into MongoDB
        files_col.insert_one({"chat_id": user.id, "file_path": file_path, "description": bot_reply})

        # Send the analysis response to the user
        await update.message.reply_text(f"Analysis: {bot_reply}")
    except Exception as e:
        logging.error(f"Error in image/file analysis: {str(e)}")
        await update.message.reply_text("There was an error analyzing the file.")
# Web Search
async def web_search(update: Update, context: CallbackContext) -> None:
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Please enter a search query. Example: /websearch AI trends")
        return
    
    # Debug: Log the query
    logging.info(f"Searching for: {query}")
    
    # Perform the search using SerpAPI
    search = GoogleSearch({"q": query, "api_key": SERPAPI_KEY})
    results = search.get_dict().get("organic_results", [])
    
    # Debug: Log the results fetched
    logging.info(f"Search results: {results}")
    
    if results:
        top_results = "\n".join([f"{res['title']}: {res['link']}" for res in results[:3]])
        await update.message.reply_text(f"Top search results:\n{top_results}")
    else:
        await update.message.reply_text("No results found.")

# Help Command
async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Here are the commands you can use:\n\n"
        "/start - Starts the bot and registers you\n"
        "/help - Shows this help message\n"
        "/websearch <query> - Searches the web using the provided query\n"
        "Send any text to chat with Gemini AI\n"
        "Upload an image or file for analysis\n"
    )
    await update.message.reply_text(help_text)

# Main Function
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))  # Add /help command
    application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))  # Chat with Gemini
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, file_handler))
    application.add_handler(CommandHandler("websearch", web_search))
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
