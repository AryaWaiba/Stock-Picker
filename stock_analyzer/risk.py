import pandas as pd
import numpy as np

def analyze_risk(data):
    """
    Analyzes risk metrics (Beta, Volatility, Drawdown).
    Returns score (Higher score = Lower Risk / Safer).
    """
    if data is None:
        return None
        
    history = data.get("history")
    info = data.get("info", {})
    
    metrics = {}
    scores = {}
    reasons = []

    # 1. Beta (Market Risk)
    beta = info.get("beta")
    metrics["Beta"] = beta
    
    # Beta < 1 means less volatile than market -> Safe
    if beta:
        if beta < 0.8: scores["Beta"] = 10
        elif beta < 1.2: scores["Beta"] = 7
        elif beta < 1.5: scores["Beta"] = 4
        else: scores["Beta"] = 1
        
        if beta > 1.5: reasons.append(f"High Volatility (Beta: {beta:.2f})")
    else:
        scores["Beta"] = 5 # Neutral

    # 2. Daily Volatility (Annualized)
    if history is not None and not history.empty:
        rets = history["Close"].pct_change().dropna()
        volatility = rets.std() * np.sqrt(252) # Annualized
        metrics["Volatility"] = volatility
        
        # Determine safety based on general market standards
        # < 20% low, > 40% high
        if volatility < 0.15: scores["Vol"] = 10
        elif volatility < 0.25: scores["Vol"] = 7
        elif volatility < 0.40: scores["Vol"] = 4
        else: scores["Vol"] = 1
        
        # 3. Max Drawdown (1Y)
        # Look at last year
        one_year = history.iloc[-252:]
        rolling_max = one_year["Close"].cummax()
        drawdown = (one_year["Close"] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        metrics["Max Drawdown"] = max_drawdown
        
        if max_drawdown > -0.10: scores["DD"] = 10 # Dropped less than 10%
        elif max_drawdown > -0.20: scores["DD"] = 8
        elif max_drawdown > -0.40: scores["DD"] = 4
        else: scores["DD"] = 0
        
        if max_drawdown < -0.30: reasons.append(f"Heavy Drawdown ({max_drawdown:.1%})")

    # Aggregate (Higher score = Safer)
    final_score = np.mean(list(scores.values()))

    return {
        "metrics": metrics,
        "scores": scores,
        "score": final_score,
        "reasons": reasons
    }
