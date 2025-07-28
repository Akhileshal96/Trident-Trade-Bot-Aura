# 🚀 Trident Trade Bot V2 — Aura Edition

> Intelligent, risk-aware, GPT-powered algo trading bot for Zerodha & NIFTY 50 🇮🇳

---

### ⚡ Features

- 📊 Signal Generation using EMA(20/50), RSI, MACD
- 🧠 GPT-Veto System (Optional trade approval using OpenAI)
- 🔄 Trailing Stop Loss (+1.5% trigger, -2% SL from peak)
- 🔁 Smart Re-entry logic (only if price > previous peak +0.5%)
- 📉 Risk & PnL Guardrails (Daily loss cap ₹1000, profit cap ₹2000)
- ⏰ Time-Based Controls (3:10 PM = last signal; 3:15 PM = forced exit)
- 💬 Telegram Command Bot (/start, /stop, /status)
- 📁 Audit Logs: All trades & events with GPT/context/signal scores

---

### 🛠️ Setup Guide

1. 📦 Clone repo & install dependencies:

