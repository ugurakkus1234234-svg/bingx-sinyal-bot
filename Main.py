import requests
import time
import os
from telegram import Bot
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
import pandas as pd

# ====== API VE TELEGRAM ======
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)
TIMEFRAME = "5m"

def get_all_symbols():
    url = "https://open-api.bingx.com/openApi/spot/v1/symbols"
    r = requests.get(url).json()
    all_symbols = []
    for s in r.get("data", []):
        if s["quoteAsset"] == "USDT":
            all_symbols.append(s["symbol"])
    return all_symbols

def get_klines(symbol):
    url = "https://open-api.bingx.com/openApi/swap/v2/quote/klines"
    params = {"symbol": symbol, "interval": TIMEFRAME, "limit": 100}
    try:
        r = requests.get(url, params=params).json()
        data = r["data"]
        df = pd.DataFrame(data)
        df["close"] = df["close"].astype(float)
        return df
    except:
        return None

def analyze(symbol):
    df = get_klines(symbol)
    if df is None or df.empty:
        return None
    ema_fast = EMAIndicator(df["close"], 9).ema_indicator()
    ema_slow = EMAIndicator(df["close"], 21).ema_indicator()
    rsi = RSIIndicator(df["close"], 14).rsi()
    if ema_fast.iloc[-1] > ema_slow.iloc[-1] and rsi.iloc[-1] < 70:
        return "LONG 📈"
    elif ema_fast.iloc[-1] < ema_slow.iloc[-1] and rsi.iloc[-1] > 30:
        return "SHORT 📉"
    else:
        return None

def send_signal(symbol, direction):
    message = f"""
📊 **SİNYAL**
🪙 Coin: {symbol}
📍 Yön: {direction}
⏱ Zaman Dilimi: {TIMEFRAME}
⚠️ Not: TP/SL kendi riskine göre
"""
    bot.send_message(chat_id=CHAT_ID, text=message)

def main():
    symbols = get_all_symbols()
    print(f"{len(symbols)} coin taranıyor...")
    checked = set()
    while True:
        for symbol in symbols:
            if symbol in checked:
                continue
            signal = analyze(symbol)
            if signal:
                send_signal(symbol, signal)
                checked.add(symbol)
                time.sleep(10)
        time.sleep(300)

if __name__ == "__main__":
    main()
