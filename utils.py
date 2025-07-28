# utils.py

import os
from datetime import datetime

LOG_DIR = "data"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(os.path.join(LOG_DIR, "events.log"), "a") as f:
        f.write(log_msg + "\n")


def log_trade_to_csv(symbol, qty, side, entry_price, exit_price, pnl):
    from csv import writer
    with open(os.path.join(LOG_DIR, "trade_log.csv"), "a", newline="") as file:
        csv_writer = writer(file)
        if file.tell() == 0:
            csv_writer.writerow(["Time", "Symbol", "Qty", "Side", "Entry", "Exit", "PnL"])
        csv_writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol, qty, side, entry_price, exit_price, pnl
        ])