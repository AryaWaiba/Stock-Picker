import sys
import os

# Ensure we can import modules from current directory
sys.path.append(os.getcwd())

import data_fetcher
import fundamentals
import valuation
import technicals
import risk
import scoring

def test_pipeline(ticker="AAPL"):
    print(f"--- Testing Pipeline for {ticker} ---")
    
    print("1. Fetching Data...")
    data = data_fetcher.get_stock_data(ticker)
    if not data:
        print("FAILED: Could not fetch data.")
        return
    print("MATCH: Data fetched successfully.")
    
    print("2. Running Fundamentals...")
    fund = fundamentals.analyze_fundamentals(data)
    print(f"MATCH: Fundamentals Score: {fund['score']:.2f}")
    
    print("3. Running Valuation...")
    val = valuation.analyze_valuation(data)
    print(f"MATCH: Valuation Score: {val['score']:.2f}")
    
    print("4. Running Technicals...")
    tech = technicals.analyze_technicals(data)
    print(f"MATCH: Technicals Score: {tech['score']:.2f}")
    
    print("5. Running Risk...")
    r = risk.analyze_risk(data)
    print(f"MATCH: Risk Score: {r['score']:.2f}")
    
    print("6. Aggregating Scores...")
    final = scoring.factor_scores(fund, val, tech, r)
    print(f"SUCCESS: Final Score: {final['total_score']} - Recommendation: {final['recommendation']}")
    
if __name__ == "__main__":
    test_pipeline()
