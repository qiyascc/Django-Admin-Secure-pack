import logging
import random
import string
import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from django.conf import settings

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

async def send_admin_access_key(ip, user_agent, key):
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_LOG_CHANNEL:
        raise ValueError("Telegram settings are incomplete. Please check TELEGRAM_BOT_TOKEN and TELEGRAM_LOG_CHANNEL in your settings.")
    try:
        message = (
            f"🖥️ IP address: `{ip}`\n"
            f"🎈 Browser: `{user_agent}`\n\n"
            f"🔑 Key: `{key}`"
        )
        await bot.send_message(
            settings.TELEGRAM_LOG_CHANNEL,
            message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Failed to send message to Telegram: {e}")
        raise

@router.message(Command("start"))
async def send_welcome(message: Message):
    await message.reply(f"Your ID: {message.from_user.id}")

async def on_startup():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting bot...")
    await dp.start_polling(bot)

def start_bot():
    asyncio.run(on_startup())