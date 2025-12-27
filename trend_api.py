from fastapi import FastAPI
import pandas as pd
import urllib.request, io
from datetime import datetime

app = FastAPI()

def fetch_data(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}?period1=1700000000&period2=9999999999&interval=1d&events=history"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req).read().decode()
    df = pd.read_csv(io.StringIO(data))
    return df.tail(120)

def indicators(df):
    close = df["Close"]
    df["EMA20"] = close.ewm(span=20).mean()
    df["EMA50"] = close.ewm(span=50).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

    return df.iloc[-1]

def analyze(latest):
    score = 0
    if latest["EMA20"] > latest["EMA50"]:
        score += 30
    else:
        score -= 30

    if latest["RSI"] > 60:
        score += 25
    elif latest["RSI"] < 40:
        score -= 25

    confidence = min(100, abs(score))

    if score > 20:
        trend = "UPTREND 🔼"
    elif score < -20:
        trend = "DOWNTREND 🔽"
    else:
        trend = "SIDEWAYS ➖"

    return trend, confidence

@app.get("/")
def home():
    return {"status": "API working"}

@app.get("/predict/{symbol}")
def predict(symbol: str):
    try:
        df = fetch_data(symbol)
        latest = indicators(df)
        trend, confidence = analyze(latest)

        return {
            "symbol": symbol,
            "trend": trend,
            "confidence_percent": confidence,
            "RSI": round(float(latest["RSI"]), 2),
            "price": round(float(latest["Close"]), 2),
            "time": datetime.now().strftime("%d-%m-%Y %H:%M")
        }
    except:
        return {"error": "Data unavailable"}
