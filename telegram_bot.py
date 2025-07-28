# telegram_bot.py

from telethon import TelegramClient, events
from state_manager import set_running, set_stopped, get_status
from utils import log_event
import os
from dotenv import load_dotenv

load_dotenv()

# Required ENV vars
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "123456"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Session name = persistent auth
client = TelegramClient('trident_session', TELEGRAM_API_ID, TELEGRAM_API_HASH).start(bot_token=TELEGRAM_BOT_TOKEN)

@client.on(events.NewMessage(pattern="/start"))
async def handle_start(event):
    set_running()
    await event.respond("✅ Bot started.")
    log_event("🟢 Telegram: /start — Bot started by user.")

@client.on(events.NewMessage(pattern="/stop"))
async def handle_stop(event):
    set_stopped()
    await event.respond("⛔ Bot stopped.")
    log_event("🔴 Telegram: /stop — Bot stopped by user.")

@client.on(events.NewMessage(pattern="/status"))
async def handle_status(event):
    status = "🟢 Running" if get_status() else "🔴 Stopped"
    await event.respond(f"📡 Bot Status: {status}")
    log_event(f"📥 Telegram: /status — Replied with {status}")

@client.on(events.NewMessage(pattern=r'/say (.+)'))
async def handle_say(event):
    message = event.pattern_match.group(1)
    log_event(f"📣 Announcement: {message}")
    await event.respond(f"🗣️ Broadcasted:\n{message}")

def setup_bot_handlers():
    return client
