import pandas as pd
import numpy as np

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze_technicals(data):
    """
    Analyzes technical indicators (SMA, RSI, MACD) and returns a score/signal.
    """
    if data is None:
        return None
        
    history = data.get("history")
    if history is None or history.empty:
        return None
    
    # Use Close price
    close = history["Close"]
    
    metrics = {}
    scores = {}
    reasons = []

    # 1. Moving Averages
    sma_50 = close.rolling(window=50).mean().iloc[-1]
    sma_200 = close.rolling(window=200).mean().iloc[-1]
    current_price = close.iloc[-1]
    
    metrics["SMA 50"] = sma_50
    metrics["SMA 200"] = sma_200
    metrics["Price"] = current_price
    
    # Trend Analysis
    if current_price > sma_50 > sma_200:
        scores["Trend"] = 10
        reasons.append("Strong Uptrend (Price > SMA50 > SMA200)")
    elif current_price > sma_200:
        scores["Trend"] = 7
        reasons.append("Uptrend (Price > SMA200)")
    elif current_price < sma_50 < sma_200:
        scores["Trend"] = 0
        reasons.append("Strong Downtrend (Price < SMA50 < SMA200)")
    else:
        scores["Trend"] = 4 # Choppy
        
    # 2. RSI (14)
    # Manual RSI calc to avoid 'ta' dependency issues if library missing
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up / ema_down
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    
    metrics["RSI (14)"] = current_rsi
    
    if 30 <= current_rsi <= 70:
        scores["RSI"] = 10 # Healthy
    elif current_rsi < 30:
        scores["RSI"] = 5 # Oversold (could be opportunity or crash)
        reasons.append("Oversold (RSI < 30)")
    else: # > 70
        scores["RSI"] = 3 # Overbought
        reasons.append("Overbought (RSI > 70)")
        
    # 3. MACD
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    
    metrics["MACD"] = macd.iloc[-1]
    if macd.iloc[-1] > signal.iloc[-1]:
        scores["Momentum"] = 8
        reasons.append("Bullish MACD Cross")
    else:
        scores["Momentum"] = 2
        
    # 4. Volume Spike / Demand
    # Current Vol vs 20-Day Avg Vol
    vol = history["Volume"]
    avg_vol = vol.rolling(window=20).mean().iloc[-1]
    curr_vol = vol.iloc[-1]
    metrics["Vol/Avg"] = curr_vol / avg_vol if avg_vol > 0 else 1.0
    
    if curr_vol > 1.5 * avg_vol:
        scores["Volume"] = 10
        reasons.append("High Volume Spike (>1.5x Avg)")
    elif curr_vol > avg_vol:
        scores["Volume"] = 7
    else:
        scores["Volume"] = 5
        
    # 5. Support / Risk Reward
    # Proximity to 52-Week Low (Buying near support is safer)
    low_52 = close.rolling(window=252).min().iloc[-1]
    high_52 = close.rolling(window=252).max().iloc[-1]
    metrics["52W Low"] = low_52
    metrics["52W High"] = high_52
    
    # Position in Range (0 = at Low, 1 = at High)
    if high_52 > low_52:
        range_pos = (current_price - low_52) / (high_52 - low_52)
        metrics["Range Pos"] = range_pos
        
        if range_pos < 0.20:
             scores["Support"] = 9
             reasons.append("Near 52W Support")
        elif range_pos > 0.80:
             scores["Support"] = 3 # Near Resistance measures breakout/overbought? Context dependent.
        else:
             scores["Support"] = 6
    else:
        scores["Support"] = 5

    final_score = np.mean(list(scores.values()))
    
    return {
        "metrics": metrics,
        "scores": scores,
        "score": final_score,
        "reasons": reasons
    }
