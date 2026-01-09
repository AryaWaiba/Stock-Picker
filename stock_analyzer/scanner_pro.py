import pandas as pd
import numpy as np
import os
import glob
from scipy.stats import percentileofscore
import datetime
import time
import ai_insights # Import the new module

MARKET_DATA_DIR = "market_data"
HISTORY_FILE = "scan_history.csv"
OUTPUT_FILE = "top10_pro.xlsx"

def load_market_data():
    """Loads all parquet files from market_data into a single DataFrame."""
    files = glob.glob(os.path.join(MARKET_DATA_DIR, "*.parquet"))
    if not files:
        print("No market data found. Please run data_update.py first.")
        return pd.DataFrame()
    
    # Freshness Check
    now = time.time()
    old_files = 0
    for f in files:
        if os.stat(f).st_mtime < now - 7 * 86400:
            old_files += 1
            
    if old_files > 0:
        print(f"WARNING: {old_files} data files are older than 7 days. Please run data_update.py.")
    
    print(f"Loading {len(files)} tickers...")
    df_list = [pd.read_parquet(f) for f in files]
    df = pd.concat(df_list, ignore_index=True)
    return df

def apply_hard_filters(df):
    """
    Applies binary pass/fail filters.
    1. Rev CAGR 3Y > 3%
    2. FCF > 0
    3. Price vs 200DMA > -15%
    4. Interest Cov / Debt Check (Debt/EBITDA < 4 if IntCov missing)
    """
    initial_count = len(df)
    
    # 1. Growth Filter (Relaxed to > 0%)
    df = df[df["Rev_CAGR_3Y"] > 0.0].copy()
    
    # 2. Cash Flow Filter
    df = df[df["FCF_Positive"] == True].copy()
    
    # 3. Kill Switch: Price vs 200DMA
    # Relaxed to -25% to allow "Deep Value" picks even if trend is weak
    mask_trend = (df["Price"] - df["MA200"]) / df["MA200"] > -0.25
    df = df[mask_trend].copy()
    
    # 4. Debt Filter (Debt/EBITDA < 6)
    # Generous filter for safety
    mask_debt = (df["Debt_EBITDA"] < 6) | (df["Debt_EBITDA"].isna())
    df = df[mask_debt].copy()
    
    print(f"Filters: {initial_count} -> {len(df)} tickers passed.")
    return df

def normalize_metrics(df):
    """
    Applies Sector-Relative Normalization across 7-Layer Framework metrics.
    """
    # Define metrics to normalize and their direction (True = Higher is Better)
    metrics_config = {
        # Fundamentals
        "ROIC": True,
        "Rev_CAGR_3Y": True,
        "Gross_Margin": True, # New
        
        # Valuation
        "ForwardPE": False, # Lower is better
        "PegRatio": False,  # Lower is better (Need to be careful with negative PEG? assume cleaned in data update)
        
        # Risk
        "Beta": False,      # Lower is better
        "Debt_EBITDA": False, # Lower is better
        
        # Technicals
        "RSI": True,        # Mid-range is best, but for raw percentile, High RSI = Strong Momentum logic (filtered by O/B later)
        "Vol_Avg": True     # Higher vol relative to avg? Or absolute? Let's use Relative Vol if available. 
                            # If not diff, just rank by volume liquidity?
    }
    
    df_scored = df.copy()
    df_scored["NormSource"] = "Sector" # Default
    
    for sector in df["Sector"].unique():
        sector_mask = df["Sector"] == sector
        sector_df = df[sector_mask]
        
        # Fallback to Universe if small sector
        if len(sector_df) < 5:
             df_scored.loc[sector_mask, "NormSource"] = "Universe (Fallback)"
             pass 

        for metric, higher_better in metrics_config.items():
            if metric not in sector_df.columns:
                continue
                
            if sector_df[metric].isna().all():
                continue
                
            ranks = sector_df[metric].rank(pct=True, ascending=higher_better) * 100
            df_scored.loc[sector_mask, f"Score_{metric}"] = ranks
            
    # Fill NaN scores with 50 (Neutral)
    score_cols = [f"Score_{m}" for m in metrics_config.keys() if f"Score_{m}" in df_scored]
    df_scored[score_cols] = df_scored[score_cols].fillna(50)
    
    return df_scored

def calculate_final_score(df):
    """
    Weights the normalized scores into a final 0-100 score based on 7-Layer logic.
    """
    # 1. Quality (30%) - ROIC, Margins
    score_qual = (df.get("Score_ROIC", 50) * 0.6) + (df.get("Score_Gross_Margin", 50) * 0.4)
    
    # 2. Growth (20%) - Revenue CAGR
    score_grow = df.get("Score_Rev_CAGR_3Y", 50)
    
    # 3. Valuation (25%) - PE, PEG
    score_val = (df.get("Score_ForwardPE", 50) * 0.6) + (df.get("Score_PegRatio", 50) * 0.4)
    
    # 4. Technicals (15%) - RSI, Trend (Price vs MA200)
    # Calc Trend Score manually from Price vs MA200 deviation
    pct_above_ma200 = (df["Price"] / df["MA200"]) - 1
    score_trend = 50 + (pct_above_ma200 * 100).clip(-50, 50)
    
    score_tech = (df.get("Score_RSI", 50) * 0.4) + (score_trend * 0.6)
    
    # 5. Risk (10%) - Beta, Debt
    score_risk = (df.get("Score_Beta", 50) * 0.5) + (df.get("Score_Debt_EBITDA", 50) * 0.5)

    # Weighted Sum
    total = (score_qual * 0.30) + (score_grow * 0.20) + (score_val * 0.25) + (score_tech * 0.15) + (score_risk * 0.10)
    
    # Save Sub-Scores for UI Radar
    df["Score_Quality"] = score_qual
    df["Score_Growth"] = score_grow
    df["Score_Valuation"] = score_val
    df["Score_Technicals"] = score_tech
    df["Score_Risk"] = score_risk
    
    df["TotalScore"] = total
    return df

def update_history(df):
    """
    Updates scan_history.csv and calculates Rank Delta.
    """
    today = datetime.date.today().isoformat()
    
    # Prepare current snapshot
    snapshot = df[["Ticker", "TotalScore"]].copy()
    snapshot["Date"] = today
    snapshot["Rank"] = snapshot["TotalScore"].rank(ascending=False)
    
    if os.path.exists(HISTORY_FILE):
        history = pd.read_csv(HISTORY_FILE)
        # Remove today if exists (rerun support)
        history = history[history["Date"] != today]
        history = pd.concat([history, snapshot], ignore_index=True)
    else:
        history = snapshot
        
    history.to_csv(HISTORY_FILE, index=False)
    
    # Calculate Rank Delta (vs 7d Avg or Last)
    # Simplest: Rank Prev Day - Rank Today
    # If Prev Day missing, Delta = 0
    
    latest_ranks = snapshot.set_index("Ticker")["Rank"]
    
    # Get distinct dates
    dates = sorted(history["Date"].unique())
    if len(dates) > 1:
        prev_date = dates[-2]
        prev_ranks = history[history["Date"] == prev_date].set_index("Ticker")["Rank"]
        
        # Delta: Positive means improved rank (Lower number is better rank, so Prev - Curr)
        # e.g. Prev 10, Curr 5 -> 10 - 5 = +5 (Jumped 5 spots)
        df["Rank_Delta"] = df["Ticker"].map(lambda x: prev_ranks.get(x, 0) - latest_ranks.get(x, 0))
    else:
        df["Rank_Delta"] = 0
        
    return df

def generate_explanations(df):
    """
    Generates 'Why This Stock?' string using ai_insights module.
    """
    df["Rank"] = df["TotalScore"].rank(ascending=False)
    
    # Apply AI generation row by row
    insights = df.apply(ai_insights.generate_insight, axis=1)
    
    # Unpack tuple (Insight, Risk, Version)
    df["AI_Insight"] = [x[0] for x in insights]
    df["Risk_Note"] = [x[1] for x in insights]
    df["AI_Version"] = [x[2] for x in insights]
    
    # Confidence Score (Placeholder based on data completeness)
    # If key metrics are NaN (filled 50), confidence drops
    # For now, simple logic:
    df["Confidence"] = "High" 
    
    return df

if __name__ == "__main__":
    print("--- 5-STAR PRO SCANNER ---")
    
    # 1. Load Data
    df = load_market_data()
    if df.empty: exit()
    
    # 2. Hard Filters
    df_filtered = apply_hard_filters(df)
    
    if df_filtered.empty:
        print("No stocks passed the hard filters.")
        # exit() 
        
    # 3. Normalization & Scoring
    if not df_filtered.empty:
        df_scored = normalize_metrics(df_filtered)
        df_scored = calculate_final_score(df_scored)
        
        # 4. History Tracking
        df_scored = update_history(df_scored)
        
        # 5. Explain
        df_final = generate_explanations(df_scored)
        
        # 6. Output
        cols = ["Rank", "Ticker", "Name", "TotalScore", "Rank_Delta", "AI_Insight", "Risk_Note", "Confidence", "AI_Version", "Sector", "Price", "ForwardPE", "EPS_Growth_3Y", "Rev_CAGR_3Y", "ROIC", "GrossMarginTrend", "RSI", "MA200", "Debt_EBITDA", "Beta", "Score_Quality", "Score_Growth", "Score_Valuation", "Score_Technicals", "Score_Risk"]
        top10 = df_final.sort_values("TotalScore", ascending=False).head(10)[cols]
        
        print("\nTOP 10 STOCKS:")
        pd.set_option('display.max_colwidth', 50)
        print(top10[["Rank", "Ticker", "TotalScore", "AI_Insight", "Risk_Note"]].to_string(index=False))
        
        try:
            df_final.sort_values("TotalScore", ascending=False).head(20).to_excel(OUTPUT_FILE, index=False)
            print(f"\nSaved top 20 to {OUTPUT_FILE}")
        except Exception as e:
            print(f"Error saving Excel: {e}")
    else:
        print("No stocks passed filtering.")
