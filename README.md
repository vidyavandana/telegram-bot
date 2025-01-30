**Telegram Bot with Gemini AI**

This project implements a Telegram bot that leverages Gemini AI for chatting, analyzing images/files, and performing web searches. The bot is powered by the Google Gemini API and MongoDB for storing user interactions and file analysis results.
__Features__

    User Registration:The bot asks for user contact information when a new user interacts with it.
    Chat with Gemini AI: Users can chat with the bot, and it responds using the Gemini AI model.
    Image/File Analysis: Users can upload images or files, and the bot will analyze and describe them using Gemini AI.
    Web Search: Users can perform web searches using SerpAPI, and the bot will return the top search results.
    MongoDB Integration: All chat data and file analysis results are saved in a MongoDB database for persistence.

__Prerequisites__

Before running the bot, ensure the following dependencies are installed:

    Python 3.8+
    MongoDB (for storing user data and file analysis)
    Telegram Bot Token (from @BotFather on Telegram)
    Gemini API Key (for interacting with the Gemini AI)
    SerpAPI Key (for performing web searches)
    .env file for storing sensitive information such as API keys and MongoDB URI.

