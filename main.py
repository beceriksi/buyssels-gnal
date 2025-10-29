import requests
import pandas as pd
import os
from datetime import datetime

# =================== Telegram Settings ===================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

MEXC_FUTURES_URL = "https://contract.mexc.com/api/v1/contract/tickers"

# =================== Telegram Functions ===================
def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Telegram bilgileri eksik! Lütfen secretleri kontrol et.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        r = requests.post(url, json=payload)
        print(f"Telegram mesaj durumu: {r.status_code}")
        if r.status_code != 200:
            print("Hata mesajı:", r.text)
    except Exception as e:
        print(f"Telegram error: {e}")

def send_test_message():
    print("🔹 Telegram test mesajı gönderiliyor...")
    send_telegram("✅ Bot çalışıyor! Bu test mesajıdır.")

# =================== Signal Detection ===================
def detect_signals(df):
    signals = []
    for _, row in df.iterrows():
        symbol = row["symbol"]
        price_change = float(row.get("rise_fall_rate", 0))
        volume = float(row.get("amount", 0))
        last_price = float(row.get("fair_price", 0))

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

# =================== Main ===================
def main():
    print(f"=== Çalışıyor... {datetime.now()} ===")
    
    # Test mesajını hemen gönder
    send_test_message()

    try:
        response = requests.get(MEXC_FUTURES_URL, timeout=10)
        if response.status_code != 200:
            print(f"API hatası: {response.status_code}")
            return

        data = response.json().get("data", [])
        if not data:
            print("❌ API'den veri alınamadı!")
            return

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
