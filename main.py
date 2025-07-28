# main.py

import asyncio
from kite_api import get_ltp, place_order
from strategy_engine import generate_signal
from risk_engine import can_trade, set_position, get_position, clear_position, record_trade
from context_engine import get_market_context
from utils import log_event, log_trade_to_csv
from telegram_bot import setup_bot_handlers
from state_manager import get_status
from kite_api import kite

from datetime import datetime
import os
import csv
import time

# Read NIFTY 50 symbols from a local CSV file
async def get_nifty50_symbols():
    file_path = "data/nifty50.csv"
    symbols = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for row in reader:
                if len(row) > 2:
                    symbols.append(row[2].strip())
        log_event(f"Loaded {len(symbols)} NIFTY 50 symbols from local CSV")
    except Exception as e:
        log_event(f"Failed to read NIFTY 50 CSV: {e}")
        symbols = ["RELIANCE", "INFY", "TCS", "HDFCBANK"]
        log_event(f"Using fallback symbols: {symbols}")
    return symbols


def get_available_balance():
    try:
        margins = kite.margins(segment="equity")
        balance = margins['available']['cash']
        log_event(f"Available wallet balance: {balance}")
        return balance
    except Exception as e:
        log_event(f"Error fetching wallet balance: {e}")
        return 0


async def trade_loop():
    while True:
        if not get_status():
            log_event("Bot is stopped. Waiting to resume...")
            await asyncio.sleep(10)
            continue

        if not can_trade():
            log_event("Trading conditions not met (daily cap/loss). Waiting...")
            await asyncio.sleep(60)
            continue

        context = get_market_context()
        log_event(f"Market Context: {context}")
        symbols = await get_nifty50_symbols()

        for symbol in symbols:
            await asyncio.sleep(5)  # Delay between requests to avoid rate limits
            #signal = generate_signal(symbol)
            signal = generate_signal(symbol, market_context=context)
            log_event(f"Signal for {symbol}: {signal}")
            if not signal:
                continue

            ltp = get_ltp(f"NSE:{symbol}")
            if ltp is None:
                log_event(f"Failed to get LTP for {symbol}")
                continue

            available_balance = get_available_balance()
            if available_balance < ltp:
                log_event(f"Insufficient wallet balance to buy {symbol}. Required: {ltp}, Available: {available_balance}")
                continue

            qty = max(1, int(available_balance // ltp))
            position = get_position(symbol)

            if signal == "BUY" and not position:
                log_event(f"Placing BUY order for {symbol}, Qty: {qty}, LTP: {ltp}")
                order_id = place_order(symbol, "BUY", qty)
                if order_id:
                    log_event(f"BUY order placed for {symbol}, Order ID: {order_id}")
                    set_position(symbol, "BUY", ltp, qty)

            elif signal == "SELL" and position and position["side"] == "BUY":
                log_event(f"Placing SELL order for {symbol}, Qty: {position['qty']}, LTP: {ltp}")
                order_id = place_order(symbol, "SELL", position["qty"])
                if order_id:
                    log_event(f"SELL order placed for {symbol}, Order ID: {order_id}")
                    record_trade(symbol, position["qty"], position["price"], ltp)
                    log_trade_to_csv(symbol, position["qty"], "BUY", position["price"], ltp, (ltp - position["price"]) * position["qty"])
                    clear_position(symbol)

        await asyncio.sleep(60)  # Wait before next loop


if __name__ == "__main__":
    log_event("Starting Trident Trade Bot V2...")
    bot = setup_bot_handlers()
    loop = asyncio.get_event_loop()
    loop.create_task(trade_loop())
    bot.run_until_disconnected()
