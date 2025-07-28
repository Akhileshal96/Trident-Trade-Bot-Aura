# ✅ strategy_engine.py
import pandas as pd
from typing import Optional, Tuple, Any
from kite_api import get_historical_data, get_ltp, place_order
from utils import log_event, log_trade_to_csv
from datetime import datetime, time as dt_time
from risk_engine import get_all_open_positions, clear_position, record_trade, check_stop_loss

def calculate_ema(data: pd.DataFrame, period: int) -> pd.Series:
    return data['close'].ewm(span=period, adjust=False).mean()

def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = data['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def validate_candles(candles: Any) -> bool:
    if not candles or len(candles) < 50:
        return False
    sample = candles[0] if isinstance(candles, list) else {}
    if isinstance(sample, dict):
        return {'open', 'high', 'low', 'close', 'volume'}.issubset(sample.keys())
    elif isinstance(sample, (list, tuple)) and len(sample) >= 5:
        return True
    return False

def check_and_exit_stopped_trades():
    open_positions = get_all_open_positions()
    for symbol, pos in open_positions.items():
        ltp = get_ltp(f"NSE:{symbol}")
        if not ltp:
            continue
        if check_stop_loss(symbol, ltp):
            qty = pos["qty"]
            buy_price = pos["price"]
            place_order(symbol, "SELL", qty)
            record_trade(symbol, qty, buy_price, ltp)
            log_trade_to_csv(symbol, qty, "BUY", buy_price, ltp, (ltp - buy_price) * qty)
            clear_position(symbol)
            log_event(f"🔻 Auto-sold {symbol} @ ₹{ltp:.2f} due to stop-loss.")

def force_exit_all_positions():
    log_event("🔁 Initiating force exit of all open positions before 3:15 PM.")
    open_positions = get_all_open_positions()
    for symbol, pos in open_positions.items():
        ltp = get_ltp(f"NSE:{symbol}")
        if ltp:
            place_order(symbol, "SELL", pos["qty"])
            record_trade(symbol, pos["qty"], pos["price"], ltp)
            log_trade_to_csv(symbol, pos["qty"], "BUY", pos["price"], ltp, (ltp - pos["price"]) * pos["qty"])
            clear_position(symbol)
            log_event(f"✅ Force exited {symbol} before 3:15 PM at ₹{ltp}")

def generate_signal(symbol: str, ema_fast: int = 20, ema_slow: int = 50, rsi_period: int = 14, rsi_threshold: float = 50, macd_fast: int = 12, macd_slow: int = 26, macd_signal: int = 9, market_context: str = "neutral") -> Optional[str]:
    now = datetime.now().time()
    cutoff = dt_time(15, 10)

    check_and_exit_stopped_trades()

    if now >= cutoff:
        log_event(f"⛔ {symbol} - Skipped signal generation after {cutoff}")
        force_exit_all_positions()
        return None

    try:
        candles = get_historical_data(symbol)
    except Exception as e:
        log_event(f"{symbol} - ERROR fetching data: {str(e)}")
        return None

    if not validate_candles(candles):
        log_event(f"{symbol} - Invalid candle data. Signal skipped.")
        return None

    df = pd.DataFrame(candles)
    if df.shape[1] >= 5 and not {'open', 'high', 'low', 'close', 'volume'}.issubset(df.columns):
        df.columns = ['date', 'open', 'high', 'low', 'close', 'volume'][:df.shape[1]]

    try:
        df['ema_fast'] = calculate_ema(df, ema_fast)
        df['ema_slow'] = calculate_ema(df, ema_slow)
        df['rsi'] = calculate_rsi(df, rsi_period)
        df['macd'], df['macd_signal'], _ = calculate_macd(df, macd_fast, macd_slow, macd_signal)
    except Exception as e:
        log_event(f"{symbol} - ERROR in indicator calculation: {str(e)}")
        return None

    if len(df) < 2:
        log_event(f"{symbol} - Not enough data after indicator calc.")
        return None

    latest = df.iloc[-1]
    if market_context == "bearish":
        rsi_threshold -= 5
    elif market_context == "bullish":
        rsi_threshold += 5

    buy_score = sum([
        latest['ema_fast'] > latest['ema_slow'],
        latest['rsi'] > rsi_threshold,
        latest['macd'] > latest['macd_signal']
    ])
    sell_score = sum([
        latest['ema_fast'] < latest['ema_slow'],
        latest['rsi'] < rsi_threshold,
        latest['macd'] < latest['macd_signal']
    ])

    signal = None
    if buy_score >= 2:
        signal = "BUY"
        reason = f"BUY score={buy_score}, RSI={latest['rsi']:.1f}, Time={now}"
    elif sell_score >= 2:
        signal = "SELL"
        reason = f"SELL score={sell_score}, RSI={latest['rsi']:.1f}, Time={now}"
    else:
        reason = f"No consensus - BuyScore={buy_score}, SellScore={sell_score}, RSI={latest['rsi']:.1f}, Time={now}"

    log_event(f"{symbol} signal: {signal} | Price: {latest['close']} | Reason: {reason}")
    return signal

