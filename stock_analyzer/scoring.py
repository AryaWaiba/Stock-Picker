def factor_scores(fundamentals, valuation, technicals, risk):
    """
    Aggregates scores from all modules and provides a final recommendation.
    Weights:
    - Fundamentals: 40%
    - Valuation: 30%
    - Technicals: 20%
    - Risk: 10%
    """
    
    # Extract raw scores (0-10 scale in modules)
    f_score = fundamentals["score"] if fundamentals else 0
    v_score = valuation["score"] if valuation else 0
    t_score = technicals["score"] if technicals else 0
    r_score = risk["score"] if risk else 0
    
    # Normalize to 0-100
    f_score *= 10
    v_score *= 10
    t_score *= 10
    r_score *= 10
    
    # Weighted Sum
    total_score = (
        (f_score * 0.40) +
        (v_score * 0.30) +
        (t_score * 0.20) +
        (r_score * 0.10)
    )
    
    # Recommendation
    if total_score >= 70:
        recommendation = "BUY"
    elif total_score >= 50:
        recommendation = "HOLD"
    else:
        recommendation = "AVOID"
        
    return {
        "total_score": round(total_score, 1),
        "recommendation": recommendation,
        "breakdown": {
            "Fundamentals": round(f_score, 1),
            "Valuation": round(v_score, 1),
            "Technicals": round(t_score, 1),
            "Risk": round(r_score, 1)
        }
    }
