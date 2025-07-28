# main.py

import asyncio
import csv
from datetime import datetime, time
from kite_api import get_ltp, place_order
from strategy_engine import generate_signal
from risk_engine import (
    set_position, get_position, clear_position,
    update_peak, get_peak,
    update_day_pnl, get_open_positions, can_trade
)
from context_engine import get_market_context
from utils import log_event, log_trade_to_csv
from telegram_bot import setup_bot_handlers
from state_manager import get_status
import gpt_filter


async def get_nifty50_symbols():
    file_path = "data/nifty50.csv"
    symbols = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) > 2:
                    symbols.append(row[2].strip())
        log_event(f"✅ Loaded {len(symbols)} NIFTY 50 symbols from CSV")
    except Exception as e:
        log_event(f"❌ Error reading NIFTY 50 CSV: {e}")
        # fallback
        symbols = ["RELIANCE", "INFY", "TCS", "HDFCBANK"]
        log_event(f"📎 Fallback symbols used: {symbols}")
    return symbols


def get_available_balance():
    from kite_api import kite
    try:
        margins = kite.margins(segment="equity")
        return margins["available"]["cash"]
    except Exception as e:
        log_event(f"⚠️ Error getting wallet balance: {e}")
        return 0


async def trade_loop():
    while True:
        if not get_status():
            log_event("⛔ BOT PAUSED. Waiting to resume...")
            await asyncio.sleep(10)
            continue

        now = datetime.now().time()
        if now >= time(15, 10):
            log_event("🕒 15:10 reached. No new trades will be accepted.")
            await asyncio.sleep(60)
            continue

        if now >= time(15, 15):
            log_event("🔚 15:15 — closing all open positions.")
            for symbol in get_open_positions():
                position = get_position(symbol)
                if position:
                    ltp = get_ltp(f"NSE:{symbol}")
                    if ltp:
                        qty = position["qty"]
                        order_id = place_order(symbol, "SELL", qty)
                        if order_id:
                            pnl = (ltp - position["price"]) * qty
                            update_day_pnl(pnl)
                            log_trade_to_csv(symbol, qty, "SELL", position["price"], ltp, pnl)
                            clear_position(symbol)
                            log_event(f"✅ Final exit: {symbol} | PnL: {pnl:.2f}")
            break

        if not can_trade():
            log_event("🚫 Daily loss/profit guard hit. Skipping cycle.")
            await asyncio.sleep(60)
            continue

        context = get_market_context()
        symbols = await get_nifty50_symbols()

        for symbol in symbols:
            await asyncio.sleep(2.5)  # prevent overloading
            trade_signal = generate_signal(symbol, market_context=context)

            log_event(f"📊 [{symbol}] Signal: {trade_signal}")
            if not trade_signal:
                continue

            approved = gpt_filter.gpt_trade_approval(symbol, trade_signal, context)
            if not approved:
                log_event(f"🙅 GPT vetoed trade: {symbol} [{trade_signal}]")
                continue

            ltp = get_ltp(f"NSE:{symbol}")
            if not ltp:
                log_event(f"⚠️ Could not retrieve LTP for {symbol}")
                continue

            balance = get_available_balance()
            if balance < ltp:
                log_event(f"💸 Insufficient balance to enter {symbol}. Needed: {ltp}, Available: {balance}")
                continue

            qty = max(1, int(balance // ltp))
            position = get_position(symbol)

            # 👀 Open position SL tracking
            if position and position["side"] == "BUY":
                update_peak(symbol, ltp)
                peak = get_peak(symbol)
                sl_trigger = peak * 0.98
                trail_start = position["price"] * 1.015

                if ltp >= trail_start and ltp <= sl_trigger:
                    log_event(f"📉 Trail SL hit on {symbol}. Peak: {peak}, LTP: {ltp}")
                    order_id = place_order(symbol, "SELL", position["qty"])
                    if order_id:
                        pnl = (ltp - position["price"]) * position["qty"]
                        update_day_pnl(pnl)
                        log_trade_to_csv(symbol, position["qty"], "SELL", position["price"], ltp, pnl,
                                         gpt_approval=True, context=context)
                        clear_position(symbol)
                        continue

            # 🎯 Entry
            if trade_signal == "BUY" and not position:
                peak = get_peak(symbol)
                if peak and ltp < peak * 1.005:
                    log_event(f"⚠️ Re-entry blocked on {symbol} — LTP not 0.5% above last peak.")
                    continue
                order_id = place_order(symbol, "BUY", qty)
                if order_id:
                    set_position(symbol, "BUY", ltp, qty)
                    log_event(f"✅ BUY order placed for {symbol} | Qty: {qty} | Price: {ltp}")

            # 🧾 Regular SELL
            elif trade_signal == "SELL" and position and position["side"] == "BUY":
                order_id = place_order(symbol, "SELL", position["qty"])
                if order_id:
                    pnl = (ltp - position["price"]) * position["qty"]
                    update_day_pnl(pnl)
                    log_trade_to_csv(symbol, position["qty"], "SELL", position["price"], ltp, pnl,
                                     gpt_approval=True, context=context)
                    log_event(f"✅ SELL order executed for {symbol}, PnL: {pnl:.2f}")
                    clear_position(symbol)

        await asyncio.sleep(60)


if __name__ == "__main__":
    log_event("🚀 Launching Trident Aura Bot!")
    bot = setup_bot_handlers()
    import nest_asyncio
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    loop.create_task(trade_loop())
    bot.run_until_disconnected()
