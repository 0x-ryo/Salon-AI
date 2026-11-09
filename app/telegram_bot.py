"""
Channel 2: Telegram Messaging Bot Integration for Urban Trim & Groom Barber Salon.
Allows customers to interact with the salon via their existing Telegram app (Zero new app install).
"""

import os
import sys
import logging
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from database.db import init_db
from engine.hybrid_agent import HybridSalonAgent

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize DB
init_db()

# Shared Agent Instance
agent = HybridSalonAgent()


async def start_command(update, context):
    """Handles /start command on Telegram."""
    welcome_text = (
        "💈 **Welcome to Urban Trim & Groom Barber Salon!** 💈\n\n"
        "I am your instant 24/7 AI salon assistant. You can chat with me naturally to:\n"
        "• Check prices & service menu (`/services`)\n"
        "• View opening hours & location (`/hours`)\n"
        "• Book an appointment with your preferred barber\n"
        "• Check or cancel your existing booking (`/cancel`)\n"
        "• Connect with our human manager\n\n"
        "How can I help you today? You can type e.g. *'How much for haircut?'* or *'Book Vikram at 5pm tomorrow'*."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def services_command(update, context):
    """Handles /services command."""
    response = agent.handle_message("What services and rates do you offer?", engine_mode="Hybrid")
    await update.message.reply_text(response["response"], parse_mode="Markdown")


async def hours_command(update, context):
    """Handles /hours command."""
    response = agent.handle_message("What are your opening timings?", engine_mode="Hybrid")
    await update.message.reply_text(response["response"], parse_mode="Markdown")


async def cancel_command(update, context):
    """Handles /cancel command."""
    response = agent.handle_message("I want to cancel my booking", engine_mode="Hybrid")
    await update.message.reply_text(response["response"], parse_mode="Markdown")


async def handle_customer_message(update, context):
    """Routes customer text messages through the Hybrid AI Engine."""
    user_text = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    logger.info(f"Received message from Telegram User {username} ({user_id}): {user_text}")

    # Process via AI Engine
    ai_output = agent.handle_message(user_text, engine_mode="Hybrid")

    reply = ai_output["response"]
    await update.message.reply_text(reply, parse_mode="Markdown")


def run_telegram_bot(token=None):
    """
    Launches Telegram Polling Bot.
    If no token is supplied, runs in dry-run verification mode.
    """
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")

    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("\n=======================================================")
        print("💈 Urban Trim & Groom - Telegram Bot Channel")
        print("=======================================================")
        print("NOTICE: No TELEGRAM_BOT_TOKEN provided.")
        print("To connect live Telegram:")
        print("1. Open Telegram, search '@BotFather', type '/newbot'")
        print("2. Copy the token provided by BotFather")
        print("3. Run: python -m app.telegram_bot <YOUR_TOKEN>")
        print("=======================================================\n")
        return

    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("services", services_command))
    app.add_handler(CommandHandler("hours", hours_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_customer_message))

    print(f"🚀 Telegram Bot active and listening for customer messages...")
    app.run_polling()


if __name__ == "__main__":
    cli_token = sys.argv[1] if len(sys.argv) > 1 else None
    run_telegram_bot(cli_token)
