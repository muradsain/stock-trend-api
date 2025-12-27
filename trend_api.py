from fastapi import FastAPI
import yfinance as yf
import pandas as pd
import requests
import time

app = FastAPI(title="StockTrend AI API")

# ---------------------------
# NSE SYMBOL AUTO-FETCH
# ---------------------------
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com"
}

def fetch_nse_symbols():
    try:
        s = requests.Session()
        s.headers.update(NSE_HEADERS)
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
        data = s.get(url, timeout=10).json()
        return {item["symbol"] for item in data["data"]}
    except:
        return set()

# Cache symbols (refresh every 6 hours)
LAST_FETCH = 0
NSE_SYMBOLS = set()

def get_symbols():
    global LAST_FETCH, NSE_SYMBOLS
    if time.time() - LAST_FETCH > 21600 or not NSE_SYMBOLS:
        NSE_SYMBOLS = fetch_nse_symbols()
        NSE_SYMBOLS.update({
            "NIFTY", "BANKNIFTY", "FINNIFTY",
            "SENSEX", "MIDCPNIFTY"
        })
        LAST_FETCH = time.time()
    return NSE_SYMBOLS

# ---------------------------
# TECHNICAL INDICATORS
# ---------------------------
def add_indicators(df):
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))

    exp1 = df["Close"].ewm(span=12).mean()
    exp2 = df["Close"].ewm(span=26).mean()
    df["MACD"] = exp1 - exp2
    df["SIGNAL"] = df["MACD"].ewm(span=9).mean()

    df["VOL_MA"] = df["Volume"].rolling(20).mean()
    return df

# ---------------------------
# AI-LIKE SCORING ENGINE
# ---------------------------
def ai_score(latest):
    score = 0

    if latest["RSI"] < 30:
        score += 2
    elif latest["RSI"] > 70:
        score -= 2

    score += 1 if latest["EMA20"] > latest["EMA50"] else -1
    score += 1 if latest["MACD"] > latest["SIGNAL"] else -1
    score += 1 if latest["Volume"] > latest["VOL_MA"] else 0

    return score

# ---------------------------
# API ROUTES
# ---------------------------
@app.get("/")
def home():
    return {
        "status": "StockTrend AI running",
        "data_type": "Technical probability (not financial advice)"
    }

@app.get("/predict/{symbol}")
def predict(symbol: str):
    symbol = symbol.upper()
    symbols = get_symbols()

    if symbol not in symbols:
        return {"error": "Invalid NSE symbol"}

    yf_symbol = (
        "^NSEI" if symbol == "NIFTY"
        else symbol + ".NS"
    )

    df = yf.download(
        yf_symbol,
        period="5d",
        interval="5m",
        progress=False
    )

    if df.empty or len(df) < 50:
        return {"error": "Market data unavailable"}

    df = add_indicators(df)
    latest = df.iloc[-1]

    score = ai_score(latest)

    trend = "UP" if score > 0 else "DOWN"
    confidence = min(95, max(55, abs(score) / 5 * 100))

    return {
        "symbol": symbol,
        "trend_next_hour": trend,
        "confidence_percent": round(confidence, 2),
        "indicators": {
            "rsi": round(latest["RSI"], 2),
            "ema20": round(latest["EMA20"], 2),
            "ema50": round(latest["EMA50"], 2),
            "macd": round(latest["MACD"], 2),
            "volume_strength": "HIGH" if latest["Volume"] > latest["VOL_MA"] else "NORMAL"
        },
        "note": "AI-based probability, not guaranteed outcome"
    }