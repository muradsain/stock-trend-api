from fastapi import FastAPI
import random

app = FastAPI()

@app.get("/")
def home():
    return {"status": "API working"}

@app.get("/predict/{symbol}")
def predict(symbol: str):
    symbol = symbol.upper()

    # Simulated AI logic (Render-safe)
    trend = random.choice(["UPTREND", "DOWNTREND", "SIDEWAYS"])
    confidence = round(random.uniform(62, 89), 2)

    return {
        "symbol": symbol,
        "market": "INDIAN",
        "trend": trend,
        "confidence_percent": confidence,
        "note": "AI probability model (educational)"
    }
