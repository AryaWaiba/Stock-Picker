import pandas as pd
import numpy as np

def analyze_valuation(data):
    """
    Analyzes valuation metrics (P/E, DCF) and returns a score (0->Overvalued, 10->Undervalued).
    Note: High score = Good Value (Undervalued).
    """
    if data is None:
        return None
        
    info = data.get("info", {})
    cashflow = data.get("cashflow")
    
    metrics = {}
    scores = {}
    reasons = []

    current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    
    # 1. P/E Ratio vs Benchmark
    # Using 20 as a generic safe benchmark, or info['trailingPE']
    pe = info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    
    metrics["Trailing P/E"] = pe
    metrics["Forward P/E"] = forward_pe
    
    # Heuristic: Lower P/E is better value (generalizing)
    # < 15: Good, < 25: Fair, > 25: Expensive (This is sector dependent but we simplify)
    pe_to_use = forward_pe if forward_pe else pe
    
    if pe_to_use:
        if pe_to_use < 15: scores["PE"] = 9
        elif pe_to_use < 25: scores["PE"] = 6
        elif pe_to_use < 40: scores["PE"] = 3
        else: scores["PE"] = 1
        
        if pe_to_use < 15: reasons.append("Low P/E Ratio")
        elif pe_to_use > 40: reasons.append("Very high P/E valuation")
    else:
        scores["PE"] = 5 # Neutral if N/A (e.g. unprofitable)

    # 2. PEG Ratio (Price/Earnings to Growth)
    # PEG < 1 is undervalued, PEG < 1.5 is fair for high quality
    peg = info.get("pegRatio")
    metrics["PEG"] = peg
    
    if peg:
        if peg < 1.0: 
            scores["PEG"] = 10
            reasons.append(f"Undervalued PEG ({peg:.2f})")
        elif peg < 1.5: 
            scores["PEG"] = 8
        elif peg < 2.0: 
            scores["PEG"] = 5
        else: 
            scores["PEG"] = 3
            reasons.append(f"Rich PEG ({peg:.2f})")
            
    # 3. Price to Sales
    ps = info.get("priceToSalesTrailing12Months")
    metrics["P/S"] = ps
    if ps:
        if ps < 2: scores["PS"] = 9
        elif ps < 5: scores["PS"] = 6
        else: scores["PS"] = 3

    # 3. Simple DCF (Discounted Cash Flow)
    # Value = FCF / (Discount Rate - Growth Rate) (Gordon Growth for Terminal)
    # Using simplistic 5Y growth phase + Terminal
    try:
        shares_outstanding = info.get("sharesOutstanding", 1)
        fcf = cashflow.loc["Free Cash Flow"].iloc[0] if "Free Cash Flow" in cashflow.index else 0
        
        if fcf > 0:
            growth_rate = 0.08 # Conservative 8% growth assumption
            discount_rate = 0.10 # 10% discount rate
            terminal_growth = 0.03
            
            # 5 Year Projection
            future_cashflows = [fcf * ((1 + growth_rate) ** i) for i in range(1, 6)]
            terminal_value = (future_cashflows[-1] * (1 + terminal_growth)) / (discount_rate - terminal_growth)
            
            dcf_value = sum([fc / ((1 + discount_rate) ** (i+1)) for i, fc in enumerate(future_cashflows)])
            dcf_value += terminal_value / ((1 + discount_rate) ** 5)
            
            intrinsic_value = dcf_value / shares_outstanding
            metrics["Intrinsic Value (DCF)"] = intrinsic_value
            
            # Upside
            upside = (intrinsic_value - current_price) / current_price
            metrics["DCF Upside"] = upside
            
            if upside > 0.30: scores["DCF"] = 10
            elif upside > 0.10: scores["DCF"] = 8
            elif upside > -0.10: scores["DCF"] = 5
            else: scores["DCF"] = 2
            
            if upside > 0.20: reasons.append(f"Undervalued by {upside:.0%} (DCF)")
            elif upside < -0.20: reasons.append(f"Overvalued by {-upside:.0%} (DCF)")
            
        else:
            # Negative FCF, DCF not reliable
            metrics["Intrinsic Value (DCF)"] = 0
            scores["DCF"] = 3
            reasons.append("Negative Free Cash Flow")
            
    except Exception as e:
        metrics["DCF Error"] = str(e)
        scores["DCF"] = 5

    # Aggregate
    final_score = np.mean(list(scores.values()))
    
    return {
        "metrics": metrics,
        "scores": scores,
        "score": final_score,
        "reasons": reasons
    }
