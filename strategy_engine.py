# strategy_engine.py

import pandas as pd

def calculate_ema(df, period):
    return df["close"].ewm(span=period, adjust=False).mean()

def calculate_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(df):
    ema_12 = calculate_ema(df, 12)
    ema_26 = calculate_ema(df, 26)
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def generate_signal(symbol, market_context=None):
    from kite_api import get_historical_data
    from utils import log_event

    try:
        candles = get_historical_data(symbol)
        if not candles or len(candles) < 50:
            log_event(f"⚠️ {symbol} - Not enough candle data. Skipping.")
            return None

        df = pd.DataFrame(candles)
        df["ema20"] = calculate_ema(df, 20)
        df["ema50"] = calculate_ema(df, 50)
        df["rsi"] = calculate_rsi(df)
        df["macd"], df["macd_signal"] = calculate_macd(df)

        latest = df.iloc[-1]

        score = 0
        reasons = []

        if latest["ema20"] > latest["ema50"]:
            score += 1
            reasons.append("EMA20 > EMA50")
        if latest["rsi"] > 50:
            score += 1
            reasons.append("RSI > 50")
        if latest["macd"] > latest["macd_signal"]:
            score += 1
            reasons.append("MACD > Signal")

        if latest["ema20"] < latest["ema50"]:
            score -= 1
            reasons.append("EMA20 < EMA50")
        if latest["rsi"] < 50:
            score -= 1
            reasons.append("RSI < 50")
        if latest["macd"] < latest["macd_signal"]:
            score -= 1
            reasons.append("MACD < Signal")

        readable_reason = ", ".join(reasons)

        if score >= 2:
            log_event(f"{symbol} signal: BUY | Score: {score} | Reason: {readable_reason}")
            return "BUY"
        elif score <= -2:
            log_event(f"{symbol} signal: SELL | Score: {score} | Reason: {readable_reason}")
            return "SELL"
        else:
            log_event(f"{symbol} signal: None | Score: {score} | Reason: {readable_reason}")
            return None

    except Exception as e:
        log_event(f"❌ Signal gen error for {symbol}: {e}")
        return None
