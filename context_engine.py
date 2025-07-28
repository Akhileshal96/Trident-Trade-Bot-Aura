# context_engine.py

import pandas as pd
from kite_api import get_historical_data
from strategy_engine import calculate_ema
from utils import log_event

# Detect market context based on NIFTY 50 EMA(20/50)
def get_market_context():
    candles = get_historical_data("NIFTY 50")
    if not candles or len(candles) < 50:
        return "neutral"

    df = pd.DataFrame(candles)
    df['ema20'] = calculate_ema(df, 20)
    df['ema50'] = calculate_ema(df, 50)

    if df['ema20'].iloc[-1] > df['ema50'].iloc[-1]:
        context = "bullish"
    elif df['ema20'].iloc[-1] < df['ema50'].iloc[-1]:
        context = "bearish"
    else:
        context = "neutral"

    log_event(f"Market Context: {context}")
    return context