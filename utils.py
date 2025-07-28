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

def log_trade_to_csv(symbol, qty, side, entry_price, exit_price, pnl,
                     gpt_approval=None, context=None, score=None):
    from csv import writer
    file_path = os.path.join(LOG_DIR, "trade_log.csv")
    write_header = not os.path.exists(file_path) or os.path.getsize(file_path) == 0

    with open(file_path, "a", newline="") as f:
        csv_writer = writer(f)
        if write_header:
            csv_writer.writerow([
                "Time", "Symbol", "Qty", "Side", "Entry", "Exit", "PnL",
                "GPT_Approval", "Context", "Score"
            ])
        csv_writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol, qty, side, entry_price, exit_price, pnl,
            gpt_approval or "", context or "", score or ""
        ])
