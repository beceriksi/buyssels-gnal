import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# === AYARLAR ===
INTERVAL = "1h"
LIMIT = 200
TELEGRAM_TOKEN = ""   # ← eklersen bildirim alırsın
CHAT_ID = ""

# === Fonksiyonlar ===

def get_futures_symbols():
    """MEXC Futures’ta aktif tüm coin çiftlerini döndürür"""
    url = "https://contract.mexc.com/api/v1/contract/detail"
    data = requests.get(url).json()
    symbols = [item["symbol"] for item in data["data"] if item["state"] == 0]  # aktif olanlar
    return symbols

def get_klines(symbol, interval="1h", limit=200):
    """Her coin için mum verisi al"""
    url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval={interval}&limit={limit}"
    try:
        data = requests.get(url, timeout=10).json()
        df = pd.DataFrame(data["data"], columns=["t", "o", "h", "l", "c", "v"])
        df["o"] = df["o"].astype(float)
        df["c"] = df["c"].astype(float)
        df["v"] = df["v"].astype(float)
        return df
    except Exception:
        return None

def ema(series, period): return series.ewm(span=period, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(period).mean()
    avg_loss = pd.Series(loss).rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def macd(series, fast=12, slow=26, signal=9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line

def detect_signals(df):
    df["ema9"] = ema(df["c"], 9)
    df["ema21"] = ema(df["c"], 21)
    df["rsi"] = rsi(df["c"])
    macd_line, signal_line = macd(df["c"])
    df["macd"] = macd_line
    df["signal"] = signal_line

    # Whale filtreleri
    df["vol_spike"] = df["v"] > df["v"].rolling(20).mean() * 2
    df["green"] = df["c"] > df["o"]
    df["red"] = df["c"] < df["o"]
    df["small_move"] = abs(df["c"] - df["o"]) / df["c"] < 0.03

    df["whale_buy"] = df["vol_spike"] & df["green"] & df["small_move"]
    df["whale_sell"] = df["vol_spike"] & df["red"] & df["small_move"]
    df["trend_buy"] = (df["ema9"] > df["ema21"]) & (df["macd"] > df["signal"]) & (df["rsi"] > 50)
    df["trend_sell"] = (df["ema9"] < df["ema21"]) & (df["macd"] < df["signal"]) & (df["rsi"] < 50)
    df["final_buy"] = df["whale_buy"] | df["trend_buy"]
    df["final_sell"] = df["whale_sell"] | df["trend_sell"]
    return df

def notify_telegram(message):
    if TELEGRAM_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})

# === Ana Çalışma ===
def main():
    symbols = get_futures_symbols()
    print(f"🔍 {len(symbols)} futures çifti bulundu.\n")
    results = []

    for sym in symbols:
        df = get_klines(sym, INTERVAL, LIMIT)
        if df is None or len(df) < 50:
            continue
        df = detect_signals(df)
        last = df.iloc[-1]
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        if last["final_sell"]:
            msg = f"⚠️ SELL sinyali - {sym} ({INTERVAL})\nRSI: {last['rsi']:.1f}  Vol: {last['v']:.0f}"
            print(msg)
            notify_telegram(msg)
            results.append((sym, "SELL"))
        elif last["final_buy"]:
            msg = f"✅ BUY sinyali - {sym} ({INTERVAL})\nRSI: {last['rsi']:.1f}  Vol: {last['v']:.0f}"
            print(msg)
            notify_telegram(msg)
            results.append((sym, "BUY"))

        time.sleep(0.5)  # API limitine saygı

    print(f"\nToplam sinyal: {len(results)} coin bulundu.")
    for s, t in results:
        print(f"→ {s}: {t}")

if __name__ == "__main__":
    main()
