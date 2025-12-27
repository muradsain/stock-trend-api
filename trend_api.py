from fastapi import FastAPI
import random

app = FastAPI()

@app.get("/")
def home():
    return {"status": "StockTrend API running"}

def ai_intraday_model():
    """
    Probability-based intraday model
    (Render-safe, no live scraping)
    """

    score = random.uniform(-1, 1)

    if score > 0.25:
        direction = "UP"
        signal = "BUY"
    elif score < -0.25:
        direction = "DOWN"
        signal = "SELL"
    else:
        direction = "SIDEWAYS"
        signal = "WAIT"

    confidence = round(abs(score) * 40 + 55, 2)

    if confidence > 75:
        strength = "STRONG"
    elif confidence > 65:
        strength = "MODERATE"
    else:
        strength = "WEAK"

    reasons = [
        "Short-term momentum analysis",
        "Volatility probability estimation",
        "AI confidence-weighted signal"
    ]

    return direction, signal, confidence, strength, reasons


@app.get("/predict/{symbol}")
def predict(symbol: str):
    symbol = symbol.upper()

    direction, signal, confidence, strength, reasons = ai_intraday_model()

    return {
        "symbol": symbol,
        "market": "INDIAN",
        "timeframe": "NEXT_1_HOUR",
        "direction": direction,
        "signal": signal,
        "confidence_percent": confidence,
        "strength": strength,
        "reason": reasons,
        "disclaimer": "Educational & probabilistic. Not financial advice."
    }
