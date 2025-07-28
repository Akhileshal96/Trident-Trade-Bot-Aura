# gpt_filter.py

import openai
from utils import log_event
import os

# Get GPT key from .env
openai.api_key = os.getenv("OPENAI_API_KEY")  # example: sk-xxxxxxxxxxxx

def gpt_trade_approval(symbol, side, context):
    prompt = f"""You are a trading assistant. A signal suggests placing a {side.upper()} trade on {symbol}.
    Current market context: {context}.
    Should this trade be executed now? Reply with YES or NO only.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        decision = response['choices'][0]['message']['content'].strip().upper()
        approved = decision.startswith("YES")
        log_event(f"GPT Approval [{symbol} | {side}] = {approved} → Reply: {decision}")
        return approved
    except Exception as e:
        log_event(f"GPT FILTER ERROR [{symbol}]: {e}")
        return False  # safer to veto if GPT fails
