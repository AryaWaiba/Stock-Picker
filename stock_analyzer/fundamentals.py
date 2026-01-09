import pandas as pd
import numpy as np

def analyze_fundamentals(data):
    """
    Analyzes fundamental metrics and returns a dictionary with raw values and a score (0-10).
    """
    if data is None:
        return None

    financials = data.get("financials")
    balance_sheet = data.get("balance_sheet")
    cashflow = data.get("cashflow")
    info = data.get("info", {})

    metrics = {}
    scores = {}
    reasons = []

    # Helper to get latest value with fallback
    def get_latest(df, key):
        if df is None or df.empty:
            return 0
        try:
            # yfinance rows are metrics, cols are dates. Get latest date.
            if key in df.index:
                return df.loc[key].iloc[0]
        except:
            pass
        return 0

    # 1. Revenue Growth (CAGR 3Y if possible, else 1Y)
    try:
        rev = financials.loc["Total Revenue"]
        if len(rev) >= 3:
            # CAGR 3 Year
            latest = rev.iloc[0]
            start = rev.iloc[2] # 3 years ago
            cagr = (latest / start) ** (1/3) - 1
            metrics["Revenue Growth (3Y)"] = cagr
        elif len(rev) >= 2:
            latest = rev.iloc[0]
            start = rev.iloc[1]
            growth = (latest - start) / start
            metrics["Revenue Growth (1Y)"] = growth
        else:
             metrics["Revenue Growth"] = 0
             metrics["Revenue Growth (1Y)"] = 0
    except:
        metrics["Revenue Growth"] = 0

    rev_growth = metrics.get("Revenue Growth (3Y)", metrics.get("Revenue Growth (1Y)", 0))
    if rev_growth > 0.15: scores["Growth"] = 10
    elif rev_growth > 0.10: scores["Growth"] = 8
    elif rev_growth > 0.05: scores["Growth"] = 6
    elif rev_growth > 0: scores["Growth"] = 4
    else: scores["Growth"] = 0
    
    if rev_growth > 0.10: reasons.append(f"Strong Revenue Growth ({rev_growth:.1%})")
    elif rev_growth < 0: reasons.append(f"Negative Revenue Growth ({rev_growth:.1%})")

    # 2. Return on Equity (ROE)
    roe = info.get("returnOnEquity", 0)
    metrics["ROE"] = roe
    if roe > 0.20: scores["Profitability"] = 10
    elif roe > 0.15: scores["Profitability"] = 8
    elif roe > 0.10: scores["Profitability"] = 6
    elif roe > 0.0: scores["Profitability"] = 4
    else: scores["Profitability"] = 0

    if roe > 0.15: reasons.append(f"High ROE ({roe:.1%})")

    # 3. Debt-to-Equity
    de = info.get("debtToEquity", 0) / 100 # yfinance returns percentage often
    metrics["Debt/Equity"] = de
    # Lower is better usually
    if de < 0.5: scores["Health"] = 10
    elif de < 1.0: scores["Health"] = 8
    elif de < 2.0: scores["Health"] = 5
    else: scores["Health"] = 2
    
    if de > 2.0: reasons.append(f"High leverage (D/E: {de:.2f})")

    # 4. FCF Margin
    try:
        fcf = get_latest(cashflow, "Free Cash Flow")
        rev = get_latest(financials, "Total Revenue")
        fcf_margin = fcf / rev if rev != 0 else 0
        metrics["FCF Margin"] = fcf_margin
        
        if fcf_margin > 0.20: scores["Cash Gen"] = 10
        elif fcf_margin > 0.10: scores["Cash Gen"] = 8
        elif fcf_margin > 0.05: scores["Cash Gen"] = 6
        elif fcf_margin > 0: scores["Cash Gen"] = 4
        else: scores["Cash Gen"] = 0
        
        if fcf_margin > 0.15: reasons.append("Cash printing machine")
    except:
        metrics["FCF Margin"] = 0
        scores["Cash Gen"] = 5 # Neutral if n/a

    # 5. Margins Trend (Gross Margin)
    # Rising margins = efficiency/pricing power
    try:
        current_rev = financials.loc["Total Revenue"].iloc[0]
        prev_rev = financials.loc["Total Revenue"].iloc[1]
        
        current_gm = financials.loc["Gross Profit"].iloc[0] / current_rev
        prev_gm = financials.loc["Gross Profit"].iloc[1] / prev_rev
        
        metrics["Gross Margin"] = current_gm
        metrics["Gross Margin Trend"] = current_gm - prev_gm
        
        if current_gm > prev_gm:
            scores["Margins"] = 10
            reasons.append("Margins expanding")
        elif current_gm > 0.40: # High absolute margin
            scores["Margins"] = 8
            reasons.append("High Gross Margin (>40%)")
        else:
            scores["Margins"] = 5
    except:
        metrics["Gross Margin"] = 0
        metrics["Gross Margin Trend"] = 0
        scores["Margins"] = 5

    # 6. Returns on Capital / Moat Proxy
    # High ROIC + High Margin = Moat
    if scores.get("Profitability", 0) >= 8 and scores.get("Margins", 0) >= 8:
        scores["Moat"] = 10
        reasons.append("Wide Moat (High ROE + Margins)")
    else:
        scores["Moat"] = 5

    # Aggregate Score
    final_score = np.mean(list(scores.values()))
    
    return {
        "metrics": metrics,
        "scores": scores,
        "score": final_score,
        "reasons": reasons
    }
