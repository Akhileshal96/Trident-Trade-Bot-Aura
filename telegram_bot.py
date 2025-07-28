# telegram_bot.py

from telethon import TelegramClient, events
from dotenv import load_dotenv, set_key
import os
from utils import log_event
from state_manager import set_running, set_stopped, get_status
from kiteconnect import KiteConnect
from datetime import datetime
from kite_api import kite, API_KEY, API_SECRET

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ✅ List of admin Telegram user IDs
ADMIN_USER_IDS = [728623146]  # Replace with real admin user IDs

def is_admin(user_id):
    return user_id in ADMIN_USER_IDS

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if not is_admin(event.sender_id):
        await event.respond("🚫 You are not authorized to use this command.")
        return
    set_running()
    await event.respond("✅ Trading bot started.")

@client.on(events.NewMessage(pattern='/stop'))
async def stop_handler(event):
    if not is_admin(event.sender_id):
        await event.respond("🚫 You are not authorized to use this command.")
        return
    set_stopped()
    await event.respond("🛑 Trading bot stopped.")

@client.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    status = get_status()
    await event.respond(f"📊 Bot Status: {'Running' if status else 'Stopped'}")

@client.on(events.NewMessage(pattern='/token (.+)'))
async def token_update_handler(event):
    if not is_admin(event.sender_id):
        await event.respond("🚫 You are not authorized to perform this action.")
        return

    request_token = event.pattern_match.group(1).strip().replace("'", "")
    try:
        kite_session = KiteConnect(api_key=API_KEY)
        user_data = kite_session.generate_session(request_token, api_secret=API_SECRET)
        access_token = user_data["access_token"]

        set_key(".env", "ZERODHA_ACCESS_TOKEN", access_token)
        kite.set_access_token(access_token)
        await event.respond("🔐 Access token generated and updated successfully.")
    except Exception as e:
        log_event(f"❌ Error generating access token: {e}")
        await event.respond("❌ Failed to generate access token.")

@client.on(events.NewMessage(pattern='/wallet'))
async def wallet_handler(event):
    if not is_admin(event.sender_id):
        await event.respond("🚫 You are not authorized to use this command.")
        return

    try:
        margins = kite.margins(segment="equity")
        balance = margins.get("available", {}).get("live_balance")
        if balance is not None:
            await event.respond(f"💰 Zerodha Wallet Balance (Equity): ₹{balance:.2f}")
        else:
            await event.respond("⚠️ Could not fetch wallet balance.")
    except Exception as e:
        log_event(f"Error fetching Zerodha wallet balance: {e}")
        await event.respond("❌ Failed to fetch wallet balance.")

@client.on(events.NewMessage(pattern='/log_full'))
async def log_handler(event):
    if not is_admin(event.sender_id):
        await event.respond("🚫 You are not authorized to access logs.")
        return

    log_path = "data/events.log"
    txt_path = "data/event_log.txt"

    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as log_file:
                content = log_file.read()

            with open(txt_path, "w") as txt_file:
                txt_file.write(content)

            await event.respond("📄 Log file converted and sending as text file...", file=txt_path)

        except Exception as e:
            log_event(f"Error converting log to txt: {e}")
            await event.respond("❌ Failed to convert and send log file.")
    else:
        await event.respond("⚠️ events.log file not found.")



@client.on(events.NewMessage(pattern='/log'))
async def log_handler(event):
    if not is_admin(event.sender_id):
        await event.respond("🚫 You are not authorized to access logs.")
        return

    log_path = "data/events.log"

    if not os.path.exists(log_path):
        await event.respond("⚠️ events.log file not found.")
        return

    try:
        with open(log_path, "r") as log_file:
            lines = log_file.readlines()

        now = datetime.now()
        matching_logs = []

        for line in lines:
            try:
                timestamp_str = line.split("]")[0].strip("[")
                log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                if log_time <= now:
                    matching_logs.append(line.strip())
            except Exception:
                continue

        last_20 = matching_logs[-20:]

        if not last_20:
            await event.respond("⚠️ No logs found up to current time.")
            return

        log_text = "📋 Last 20 logs:\n\n" + "\n".join(last_20)

        # Telegram message character limit = 4096, truncate if needed
        if len(log_text) > 4000:
            log_text = log_text[-4000:]

        await event.respond(log_text)

    except Exception as e:
        log_event(f"Error retrieving logs: {e}")
        await event.respond("❌ Failed to fetch log data.")

@client.on(events.NewMessage)
async def unknown_handler(event):
    await event.respond(
        "Unknown command.\n\nAvailable:\n/start\n/stop\n/status\n/token <request_token>\n/wallet\n/log"
    )

def setup_bot_handlers():
    return client
