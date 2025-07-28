from datetime import datetime

_price_peaks = {}
_positions = {}
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
    return _positions.get(symbol)

def clear_position(symbol):
    _positions.pop(symbol, None)
    _price_peaks.pop(symbol, None)

def update_peak(symbol, ltp):
    if symbol not in _price_peaks or ltp > _price_peaks[symbol]:
        _price_peaks[symbol] = ltp

def get_peak(symbol):
    return _price_peaks.get(symbol, None)

def update_day_pnl(pnl):
    global _day_pnl
    _day_pnl += pnl

def can_trade():
    limit_profit = 2000
    limit_loss = -1000
    return _day_pnl < limit_profit and _day_pnl > limit_loss

def get_open_positions():
    return list(_positions.keys())
