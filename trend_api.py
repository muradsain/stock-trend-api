from fastapi import FastAPI
import requests

TRADIENT_API_KEY = "PASTE_YOUR_TRADIENT_API_KEY"

app = FastAPI()

# -----------------------------
# LOAD NSE SYMBOLS (FREE)
# -----------------------------
def load_nse_symbols():
    url = "https://raw.githubusercontent.com/sharanchetan/nse-stock-symbols/master/data/symbols.csv"
    symbols = set()

    try:
        csv_data = requests.get(url, timeout=10).text.splitlines()
        for row in csv_data[1:]:
            symbol = row.split(",")[0].strip().upper()
            symbols.add(symbol)
    except:
        pass

    # Add indices manually
    indices = {
        "NIFTY", "BANKNIFTY", "FINNIFTY",
        "SENSEX", "MIDCPNIFTY"
    }

    return symbols.union(indices)

ALLOWED_SYMBOLS = load_nse_symbols()

@app.get("/")
def home():
    return {
        "status": "StockTrend API Live",
        "symbols_loaded": len(ALLOWED_SYMBOLS)
    }

# -----------------------------
# TECHNICAL ANALYSIS
# -----------------------------
def analyze(data):
    rsi = data.get("rsi", 50)
    ema9 = data.get("ema_9", 0)
    ema21 = data.get("ema_21", 0)
    macd = data.get("macd", "neutral")

    direction = "SIDEWAYS"
    signal = "WAIT"
    confidence = 55

    if rsi > 55 and ema9 > ema21 and macd == "bullish":
        direction = "UP"
        signal = "BUY"
        confidence = round(min(85, rsi + 15), 2)

    elif rsi < 45 and ema9 < ema21 and macd == "bearish":
        direction = "DOWN"
        signal = "SELL"
        confidence = round(min(85, (100 - rsi) + 15), 2)

    return direction, signal, confidence

# -----------------------------
# PREDICTION API
# -----------------------------
@app.get("/predict/{symbol}")
def predict(symbol: str):
    symbol = symbol.upper()

    if symbol not in ALLOWED_SYMBOLS:
        return {
            "error": "Invalid NSE symbol",
            "message": "Symbol not found in NSE database"
        }

    url = f"https://api.tradient.org/v1/api/market/technicals?symbol={symbol}&duration=1"
    headers = {
        "Authorization": f"Bearer {TRADIENT_API_KEY}",
        "Accept": "application/json"
    }

    res = requests.get(url, headers=headers).json()

    if "data" not in res:
        return {"error": "Live market data unavailable"}

    tech = res["data"]
    direction, signal, confidence = analyze(tech)

    return {
        "symbol": symbol,
        "timeframe": "NEXT_1_HOUR",
        "direction": direction,
        "signal": signal,
        "confidence_percent": confidence,
        "indicators": {
            "RSI": tech.get("rsi"),
            "EMA_9": tech.get("ema_9"),
            "EMA_21": tech.get("ema_21"),
            "MACD": tech.get("macd")
        },
        "source": "NSE + Tradient",
        "note": "Educational probability-based prediction"
    }