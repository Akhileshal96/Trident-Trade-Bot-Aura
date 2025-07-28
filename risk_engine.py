import os
from dotenv import load_dotenv
from utils import log_event

load_dotenv()

# Risk Configuration from .env
MAX_CAPITAL = float(os.getenv("MAX_CAPITAL", 50000))
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", 1000))
MAX_DAILY_PROFIT = float(os.getenv("MAX_DAILY_PROFIT", 2000))
STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", 2))  # Percentage stop-loss

# State Variables
trade_log = []
daily_pnl = 0
open_trades = {}  # Format: { "RELIANCE": {"side": "BUY", "price": 200.0, "qty": 1} }

# Can place new trade?
def can_trade():
    if daily_pnl <= -MAX_DAILY_LOSS:
        log_event("Daily loss limit hit. Stopping trades.")
        return False
    if daily_pnl >= MAX_DAILY_PROFIT:
        log_event("Daily profit target reached. Locking profits.")
        return False
    return True

# Update daily PnL
def update_pnl(symbol, pnl):
    global daily_pnl
    daily_pnl += pnl
    log_event(f"Updated daily PnL: {daily_pnl:.2f}")

# Log closed trade and PnL
def record_trade(symbol, qty, buy_price, sell_price):
    pnl = (sell_price - buy_price) * qty
    update_pnl(symbol, pnl)
    trade_log.append({
        "symbol": symbol,
        "qty": qty,
        "buy": buy_price,
        "sell": sell_price,
        "pnl": pnl
    })

# Get current position (if any)
def get_position(symbol):
    return open_trades.get(symbol)

# Save new open position
def set_position(symbol, side, price, qty):
    open_trades[symbol] = {
        "side": side,
        "price": price,
        "qty": qty
    }

# Remove position from memory
def clear_position(symbol):
    if symbol in open_trades:
        del open_trades[symbol]

# Default capital per trade (1/10th of MAX_CAPITAL)
def get_capital_per_trade():
    return MAX_CAPITAL / 10

# Get all open BUY positions
def get_all_open_positions():
    return {
        symbol: pos for symbol, pos in open_trades.items()
        if pos.get("side") == "BUY"
    }

# Check if symbol's LTP has breached stop-loss
def check_stop_loss(symbol, current_price):
    position = open_trades.get(symbol)
    if not position or position["side"] != "BUY":
        return False

    buy_price = position["price"]
    sl_price = buy_price * (1 - STOP_LOSS_PERCENT / 100)

    if current_price <= sl_price:
        log_event(f"[STOP-LOSS] {symbol} breached SL. Buy @ ₹{buy_price:.2f}, LTP @ ₹{current_price:.2f}, SL @ ₹{sl_price:.2f}")
        return True
    return False

