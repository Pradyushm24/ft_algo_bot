# Flattrade Paper Trading Bot for FinNift
This is a *paper trading bot* built using *Flattrade Broker API*, designed for FinNifty options trading based on a custom hedging strategy. It includes real-time monitoring, trailing stop loss, re-entry logic, and expiry-based forced exit.

## 📌 Strategy Details

- *Instruments:* FinNifty Options (Monthly expiry)
- *Lot Size:* 65
- *Entry Time:* After 9:20 AM
- *Position:*
  - Buy 5th OTM Call Option
  - Sell 3rd OTM Call Option
  - Buy 5th OTM Put Option
  - Sell 3rd OTM Put Option
- *Stop Loss:*
  - Trailing SL starts after ₹300 profit
  - ₹50 buffer and ₹1 trail thereafter
- *Re-entry Logic:*
  - If SL is hit, wait 5 minutes and re-enter if condition holds
- *Exit Logic:*
  - Exit when SL hits
  - If not exited, forced exit at *2:00 PM on FinNifty monthly expiry day (last Tuesday of the month)*

## ⚙ Setup Details

- *Language:* Python
- *Trading Mode:* *Paper Trading only* (no real orders)
- *Manual Pause System:* Use pause.txt file with "pause" or "resume"
- *Auto Token Management:* Token saved in token.txt file

## 📁 File Structure

- auth.py – Generates daily API token
- main.py – Runs the main strategy logic
- portfolio.py – Tracks and simulates paper portfolio
- trading_control.py – Controls strategy execution rules
- options_chain.py – Selects 3rd and 5th OTM strikes
- utils.py – Utilities for date/time/logs
- bot_cli.py – Command-line runner
- pause.txt – Type pause or resume to manually control bot
- token.txt – Stores daily generated token
- requirements.txt – Python dependencies

## 🚀 How to Run

1. Install dependencies:
