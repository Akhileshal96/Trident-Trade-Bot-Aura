import openai
from utils import log_event
import os

openai.api_key = os.getenv("OPENAI_API_KEY", "sk-...")  # Set this in your .env

def gpt_trade_approval(symbol, side, context):
    prompt = f"Should we place a {side} trade for {symbol}? Market context: {context}. Reply YES or NO."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        result = response.choices[0].message.content.strip().upper()
        approved = result.startswith("YES")
        log_event(f"GPT Approval for {symbol} [{side}]: {approved} – Reply: {result}")
        return approved
    except Exception as e:
        log_event(f"GPT API error: {e}")
        return False
