# risk_engine.py

from datetime import datetime

_positions = {}
_price_peaks = {}
_day_pnl = 0

def set_position(symbol, side, entry_price, qty):
    _positions[symbol] = {
        "side": side,
        "price": entry_price,
        "qty": qty,
        "entry_time": datetime.now()
    }
    _price_peaks[symbol] = entry_price

def get_position(symbol):
    return _positions.get(symbol, None)

def clear_position(symbol):
    if symbol in _positions:
        del _positions[symbol]
    if symbol in _price_peaks:
        del _price_peaks[symbol]

def update_peak(symbol, ltp):
    if symbol not in _price_peaks or ltp > _price_peaks[symbol]:
        _price_peaks[symbol] = ltp

def get_peak(symbol):
    return _price_peaks.get(symbol, None)

def update_day_pnl(pnl):
    global _day_pnl
    _day_pnl += pnl

def can_trade():
    return -1000 < _day_pnl < 2000

def get_open_positions():
    return list(_positions.keys())
