import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# === Secrets'dan al ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
INTERVAL = "1h"
LIMIT = 200

# === Telegram gönderim fonksiyonu ===
def send_message(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram bilgileri eksik.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram hatası:", e)

# === Sinyal tespiti ===
def detect_signals(df):
    df['ma_fast'] = df['close'].rolling(9).mean()
    df['ma_slow'] = df['close'].rolling(21).mean()
    df['rsi'] = calc_rsi(df['close'])

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if last['ma_fast'] > last['ma_slow'] and prev['ma_fast'] <= prev['ma_slow'] and last['rsi'] < 70:
        return "BUY"
    elif last['ma_fast'] < last['ma_slow'] and prev['ma_fast'] >= prev['ma_slow'] and last['rsi'] > 30:
        return "SELL"
    return None

# === RSI hesaplama ===
def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# === MEXC verisi çekme ===
def get_klines(symbol):
    url = f"https://www.mexc.com/open/api/v2/market/kline?symbol={symbol}_USDT&type={INTERVAL}&limit={LIMIT}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("data") is None:
            return None
        df = pd.DataFrame(data["data"])
        df.columns = ["time", "open", "high", "low", "close", "volume"]
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        print(f"API hatası ({symbol}):", e)
        return None

# === Ana fonksiyon ===
def main():
    coins = ["BTC", "ETH", "SOL", "BNB", "DOGE"]  # örnek liste
    for coin in coins:
        df = get_klines(coin)
        if df is None or len(df) < 50:
            continue
        signal = detect_signals(df)
        if signal:
            msg = f"{coin} {signal} sinyali geldi! ({INTERVAL})"
            print(msg)
            send_message(msg)

if __name__ == "__main__":
    main()
