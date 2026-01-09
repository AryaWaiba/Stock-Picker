
# ai_insights.py
import pandas as pd

VERSION = "7-Layer-Framework-v3.0"

def generate_insight(row):
    """
    Generates a structured, institutional-grade narrative based on the 7-Layer Framework.
    """
    # Fundamentals
    rev_cagr = row.get("Rev_CAGR_3Y", 0)
    roic = row.get("ROIC", 0)
    # Valuation
    pe = row.get("ForwardPE", 0)
    peg = row.get("PegRatio", 0)
    # Technicals
    price = row.get("Price", 0)
    ma200 = row.get("MA200", 0)
    rsi = row.get("RSI", 50)
    # Risk
    beta = row.get("Beta", 1.0)
    
    # Scores
    score_qual = row.get("Score_Quality", 50)
    score_val = row.get("Score_Valuation", 50)
    score_tech = row.get("Score_Technicals", 50)
    
    # Thesis Hook
    rank = int(row.get('Rank', 0))
    sector = row.get('Sector', 'Market')
    thesis = f"Ranked #{rank} in {sector}."
    if score_qual > 70 and score_val > 70:
        thesis += " A rare 'Double Threat' offering both high quality and deep value."
    elif score_qual > 80:
        thesis += " A premium quality compounder with industry-leading fundamentals."
    elif score_val > 80:
        thesis += " A Deep Value play trading at a significant discount."
    elif score_tech > 80:
        thesis += " Showing strong momentum; technicals suggest accumulation."
        
    # Fundamentals
    fund_notes = []
    if rev_cagr > 0.15: fund_notes.append(f"Hyper-growth ({rev_cagr:.1%})")
    elif rev_cagr > 0.05: fund_notes.append(f"Steady growth ({rev_cagr:.1%})")
    if roic > 0.15: fund_notes.append(f"Wide Moat (ROIC {roic:.1%})")
    fund_str = f"**Business:** {' & '.join(fund_notes)}." if fund_notes else "Business: Reliable steady-state metrics."

    # Valuation
    val_notes = []
    if pe < 15: val_notes.append(f"Cheap P/E ({pe:.1f}x)")
    elif pe > 30: val_notes.append(f"Premium P/E ({pe:.1f}x)")
    if peg > 0 and peg < 1.0: val_notes.append(f"Undervalued PEG ({peg:.2f})")
    val_str = f"**Value:** {', '.join(val_notes)}." if val_notes else f"**Value:** Fairly priced (P/E {pe:.1f}x)."

    # Timing
    tech_notes = []
    if pd.notnull(ma200) and price > ma200: tech_notes.append("Uptrend (>200DMA)")
    elif pd.notnull(ma200): tech_notes.append("Below 200DMA (Caution)")
    if rsi < 35: tech_notes.append("Oversold (Bounce potential)")
    tech_str = f"**Timing:** {', '.join(tech_notes)}." if tech_notes else "**Timing:** Neutral setup."

    return f"{thesis} {fund_str} {val_str} {tech_str}", f"Beta: {beta:.2f}", VERSION

def generate_fidelity_card(ticker, rating, metrics):
    """
    Generates a professional analyst note card (HTML) for a stock.
    Targeting the specialized layout from the user request.
    """
    # Color mapping
    color_map = {"BUY": "#00C805", "HOLD": "#FFC107", "AVOID": "#E63946", "SELL": "#E63946"}
    rating_color = color_map.get(rating, "#000000")
    light_rating_color = rating_color + "15" # 15% opacity for background

    # Extract metrics
    pe = metrics.get("PE", 0)
    f_pe = metrics.get("ForwardPE", 0)
    rev_growth = metrics.get("RevenueGrowth", 0)
    eps_growth = metrics.get("EPSGrowth", 0)
    roe = metrics.get("ROE", 0)
    debt_equity = metrics.get("DebtToEquity", 0)
    beta = metrics.get("Beta", 0)
    rsi = metrics.get("RSI", 50)
    price = metrics.get("Price", 0)
    name = metrics.get("CompanyName", ticker)
    rank = metrics.get("Rank", "-")
    
    # Absolute Scores (out of 10 for display logic, but here they are 0-100)
    s_fund = metrics.get("Score_Fundamentals", 0) or metrics.get("Score_Quality", 0)
    s_tech = metrics.get("Score_Technicals", 0)
    s_risk = metrics.get("Score_Risk", 0)
    total_score = metrics.get("TotalScore", 0)
    max_score = 30 + 20 + 10 # Fundamentals(30) + Tech(20) + Risk(10) - Based on UI image

    # Verdict Logic for Bullet Points
    why_choose = []
    if rev_growth > 0.10: why_choose.append(f"Strong revenue growth of {rev_growth:.1%} indicates expanding business")
    if eps_growth > 0.12: why_choose.append(f"Impressive EPS growth of {eps_growth:.1%} shows profitability improvement")
    if roe > 0.20: why_choose.append(f"Excellent ROE of {roe:.1%} shows efficient capital use")
    if s_fund > 70: why_choose.append("Institutional quality financial health and stability")
    if not why_choose: why_choose.append("Stable market position and sector leadership")

    why_avoid = []
    if pe > 30: why_avoid.append(f"High P/E ratio of {pe:.1f} indicates overvaluation risk")
    if debt_equity > 100: why_avoid.append(f"High debt-to-equity of {debt_equity:.1f} increases financial risk")
    if total_score < 15: why_avoid.append(f"Low overall score of {total_score:.1f}/60 suggests limited upside potential")
    if s_tech < 30: why_avoid.append("Weak technical setup indicates poor price action")
    if not why_avoid: why_avoid.append("Competitive sector headwinds may affect performance")

    # Component for Summary Score
    def make_score_kpi(label, value, max_val, color):
        return f"""<div style="flex:1; border-left: 3px solid {color}; padding-left: 10px; margin-right: 15px;">
<div style="font-size: 11px; color: #888; text-transform: uppercase; font-weight: 600;">{label} Score</div>
<div style="font-size: 18px; font-weight: 700; color: #333;">{value:.1f}/{max_val}</div>
</div>"""

    # Component for Key Metrics
    def m_item(l, v):
        return f'<span style="margin-right:15px; font-size:11px; color:#555;"><b style="color:#888; text-transform:uppercase;">{l}:</b> {v}</span>'

    # Construction
    html = f"""<div style="border: 1px solid #e0e0e0; border_radius: 8px; padding: 25px; background: #fff; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; box-shadow: 0 2px 5px rgba(0,0,0,0.02); color: #333; margin: 15px 0;">
<!-- Header -->
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
<div style="display: flex; gap: 15px; align-items: center;">
<div style="background: #f0f4f8; color: #174291; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 18px;">#{rank}</div>
<div>
<div style="font-size: 20px; font-weight: 800; color: #111;">{ticker}</div>
<div style="font-size: 12px; color: #888; margin-top: -2px;">{name}</div>
<div style="font-size: 18px; font-weight: 700; margin-top: 5px;">${price:,.2f}</div>
</div>
</div>
<div style="text-align: right;">
<div style="background: {light_rating_color}; color: {rating_color}; padding: 5px 15px; border-radius: 20px; font-weight: 800; font-size: 13px; display: inline-block; border: 1px solid {rating_color}30;">{rating}</div>
<div style="font-size: 24px; font-weight: 800; color: {rating_color}; margin-top: 8px;">{total_score:.1f}/60</div>
</div>
</div>
<hr style="border: 0; border-top: 1px solid #f0f0f0; margin: 0 0 15px 0;">
<!-- Score Mini Dashboard -->
<div style="display: flex; margin-bottom: 25px;">
{make_score_kpi("Fundamental", s_fund * 0.3, 30, "#174291")}
{make_score_kpi("Technical", s_tech * 0.2, 20, "#8b5cf6")}
{make_score_kpi("Risk", s_risk * 0.1, 10, "#f59e0b")}
</div>
<!-- Pro/Con Section -->
<div style="display: flex; gap: 40px; margin-bottom: 25px;">
<div style="flex: 1;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
<span style="color: #00C805; font-size: 16px;">✅</span>
<span style="font-weight: 700; color: #128848; font-size: 14px;">Why Choose This Stock</span>
</div>
<ul style="padding-left: 15px; margin: 0; font-size: 12px; color: #555; line-height: 1.6;">
{"".join([f'<li style="margin-bottom:6px;">{b}</li>' for b in why_choose])}
</ul>
</div>
<div style="flex: 1;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
<span style="color: #E63946; font-size: 16px;">❌</span>
<span style="font-weight: 700; color: #D32F2F; font-size: 14px;">Why Avoid This Stock</span>
</div>
<ul style="padding-left: 15px; margin: 0; font-size: 12px; color: #555; line-height: 1.6;">
{"".join([f'<li style="margin-bottom:6px;">{b}</li>' for b in why_avoid])}
</ul>
</div>
</div>
<!-- Key Metrics Bar -->
<div style="border-top: 1px solid #f0f0f0; border-bottom: 1px solid #f0f0f0; padding: 12px 0; margin-bottom: 20px;">
<div style="font-size: 11px; font-weight: 800; color: #333; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">Key Metrics</div>
<div style="display: flex; flex-wrap: wrap;">
{m_item("Revenue Growth", f"{rev_growth:.1%}")}
{m_item("EPS Growth", f"{eps_growth:.1%}")}
{m_item("PE Ratio", f"{pe:.2f}")}
{m_item("ROE", f"{roe:.1%}")}
{m_item("Debt to Equity", f"{debt_equity:.2f}")}
{m_item("Forward PE", f"{f_pe:.2f}")}
{m_item("Beta", f"{beta:.2f}")}
</div>
</div>
<!-- Score Breakdown Visual -->
<div style="margin-top: 20px;">
<div style="font-size: 11px; font-weight: 800; color: #333; margin-bottom: 15px; text-transform: uppercase;">Score Breakdown</div>
<div style="display: flex; align-items: flex-end; gap: 40px; height: 100px; padding-bottom: 20px; border-bottom: 2px solid #eee;">
<div style="flex: 1; text-align: center;">
<div style="background: #3b82f6; height: {s_fund}%; border-radius: 4px 4px 0 0; min-height: 2px;"></div>
<div style="font-size: 10px; margin-top: 8px; color: #666;">Fundamental</div>
</div>
<div style="flex: 1; text-align: center;">
<div style="background: #e5e7eb; height: {s_tech}%; border-radius: 4px 4px 0 0; min-height: 2px;"></div>
<div style="font-size: 10px; margin-top: 8px; color: #666;">Technical</div>
</div>
<div style="flex: 1; text-align: center;">
<div style="background: #f59e0b; height: {s_risk}%; border-radius: 4px 4px 0 0; min-height: 2px;"></div>
<div style="font-size: 10px; margin-top: 8px; color: #666;">Risk</div>
</div>
</div>
<div style="display: flex; justify-content: center; margin-top: 10px;">
<span style="font-size: 10px; color: #999;">Category</span>
</div>
<div style="margin-top: 25px; padding-top: 15px; border-top: 1px dashed #eee; text-align: center; font-size: 11px; color: #999; line-height: 1.5;">
This tool is for informational purposes only and does not constitute financial advice. Always conduct your own research before making investment decisions.
</div>
</div>"""
    return html
