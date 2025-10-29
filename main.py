import requests
import pandas as pd
import time
import os
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

MEXC_FUTURES_URL = "https://contract.mexc.com/api/v1/contract/tickers"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

def detect_signals(df):
    signals = []
    for _, row in df.iterrows():
        symbol = row["symbol"]
        price_change = float(row["rise_fall_rate"])
        volume = float(row["amount"])
        last_price = float(row["fair_price"])

        # === BUY SINYALİ ===
        if price_change > 2 and volume > 1000000:
            signals.append(f"🟢 BUY sinyali: {symbol} | Değişim: {price_change:.2f}% | Hacim: {volume/1000:.1f}K")

        # === SELL SINYALİ ===
        if price_change < -2 and volume > 1000000:
            signals.append(f"🔴 SELL sinyali: {symbol} | Düşüş: {price_change:.2f}% | Hacim: {volume/1000:.1f}K")

        # === BALİNA SATIŞI (henüz düşmemiş ama hacim yüksek) ===
        if -1 < price_change < 0 and volume > 5000000:
            signals.append(f"🐋 Balina satışı olabilir: {symbol} | Değişim: {price_change:.2f}% | Hacim: {volume/1000:.1f}K")

    return signals

def main():
    print(f"=== Çalışıyor... {datetime.now()} ===")
    try:
        response = requests.get(MEXC_FUTURES_URL)
        data = response.json().get("data", [])
        df = pd.DataFrame(data)
        signals = detect_signals(df)

        if signals:
            message = "📊 MEXC Futures Sinyalleri:\n\n" + "\n".join(signals)
            send_telegram(message)
            print("Sinyal gönderildi ✅")
        else:
            print("Sinyal bulunamadı ❌")

    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    main()
