import os
import time
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
from dotenv import load_dotenv
from utils import log_event

load_dotenv()

API_KEY = os.getenv("ZERODHA_API_KEY")
API_SECRET = os.getenv("ZERODHA_API_SECRET")
ACCESS_TOKEN = os.getenv("ZERODHA_ACCESS_TOKEN", "")

kite = KiteConnect(api_key=API_KEY, timeout=10)

try:
    kite.set_access_token(ACCESS_TOKEN)
except Exception as e:
    log_event(f"⚠️ Failed to set access token: {e}")

# === Retry Wrapper ===
def retry(func, retries=2, delay=2):
    for i in range(retries):
        try:
            return func()
        except Exception as e:
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise e

# === Index instrument tokens (hardcoded for Zerodha indices) ===
INDEX_TOKENS = {
    "NIFTY 50": 256265,
    "BANKNIFTY": 260105,
    "NIFTY NEXT 50": 540249
}

# === Instrument token cache ===
_instrument_cache = {}

# === Get Instrument Token ===
def get_instrument_token(symbol):
    symbol = symbol.upper()
    
    if symbol in _instrument_cache:
        return _instrument_cache[symbol]

    # ✅ Check for known index tokens
    if symbol in INDEX_TOKENS:
        _instrument_cache[symbol] = INDEX_TOKENS[symbol]
        return INDEX_TOKENS[symbol]

    try:
        time.sleep(1.5)
        instruments = retry(lambda: kite.instruments("NSE"))
        for inst in instruments:
            if inst["tradingsymbol"].upper() == symbol:
                _instrument_cache[symbol] = inst["instrument_token"]
                return _instrument_cache[symbol]
    except Exception as e:
        log_event(f"Error getting instrument token for {symbol}: {e}")
    return None

# === 📈 Get Historical Data ===
def get_historical_data(symbol, interval="5minute", days=5):
    try:
        time.sleep(1.5)
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        token = get_instrument_token(symbol)
        if not token:
            raise ValueError(f"Invalid token for symbol: {symbol}")
        return retry(lambda: kite.historical_data(
            instrument_token=token,
            from_date=from_date,
            to_date=to_date,
            interval=interval
        ))
    except Exception as e:
        log_event(f"Error fetching historical data for {symbol}: {e}")
        return []

# === 🔍 Get LTP ===
def get_ltp(symbol):
    try:
        # 🧼 Clean symbol just in case it already includes NSE:
        symbol = symbol.replace("NSE:", "").strip().upper()
        full_symbol = f"NSE:{symbol}"
        time.sleep(1.5)
        ltp_data = retry(lambda: kite.ltp([full_symbol]))
        return ltp_data[full_symbol]['last_price']
    except Exception as e:
        log_event(f"Error getting LTP for {symbol}: {e}")
        return None

# === 🛒 Place Order ===
def place_order(tradingsymbol, transaction_type, quantity, product="MIS", order_type="MARKET"):
    try:
        time.sleep(1.5)
        order_id = retry(lambda: kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NSE,
            tradingsymbol=tradingsymbol,
            transaction_type=transaction_type,
            quantity=quantity,
            product=product,
            order_type=order_type
        ))
        log_event(f"✅ Order placed: {order_id} | {tradingsymbol} | {transaction_type}")
        return order_id
    except Exception as e:
        log_event(f"❌ Error placing order for {tradingsymbol}: {e}")
        return None

# === ✅ Kite Session Health Check ===
def is_kite_ready():
    try:
        _ = kite.profile()
        return True
    except Exception:
        return False

