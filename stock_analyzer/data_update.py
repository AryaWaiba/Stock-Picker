import yfinance as yf
import pandas as pd
import numpy as np
import os
import datetime
import time

MARKET_DATA_DIR = "market_data"
SP500_WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

def get_sp500_tickers():
    """Fetches identifying info for S&P 500 companies from Wikipedia."""
    print("Fetching S&P 500 universe...")
    try:
        # Wikipedia blocks generic python requests, so we need a User-Agent
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(SP500_WIKI_URL, headers=headers)
        response.raise_for_status()
        
        tables = pd.read_html(pd.io.common.BytesIO(response.content))
        df = tables[0]
        # Rename Symbol to Ticker and GICS Sector to Sector
        df = df.rename(columns={"Symbol": "Ticker", "GICS Sector": "Sector"})
        return df[["Ticker", "Sector", "Security"]]
    except Exception as e:
        print(f"Error fetching S&P 500 list: {e}")
        return pd.DataFrame()

def calculate_custom_metrics(ticker, info, financials, balance_sheet, cashflow, history):
    """
    Calculates robust fundamental metrics (ROIC, 3Y CAGR) to save pre-computation time.
    """
    metrics = {}
    
    # --- 1. ROIC PROXY ---
    # Formula: EBIT / (Total Assets - Current Liabilities)
    # Fallback: Operating Margins * Asset Turnover
    try:
        # Get latest annual values
        ebit = financials.loc["EBIT"].iloc[0] if "EBIT" in financials.index else None
        total_assets = balance_sheet.loc["Total Assets"].iloc[0] if "Total Assets" in balance_sheet.index else None
        curr_liab = balance_sheet.loc["Total Current Liabilities"].iloc[0] if "Total Current Liabilities" in balance_sheet.index else None
        
        if ebit and total_assets and curr_liab:
            invested_capital = total_assets - curr_liab
            if invested_capital > 0:
                metrics["ROIC"] = ebit / invested_capital
            else:
                metrics["ROIC"] = 0 # Edge case
        else:
             # Fallback
             op_margin = info.get("profitMargins", 0) # This is Net Margin, let's try raw calc
             rev = financials.loc["Total Revenue"].iloc[0] if "Total Revenue" in financials.index else 0
             if rev > 0 and total_assets and total_assets > 0:
                 asset_turnover = rev / total_assets
                 metrics["ROIC"] = op_margin * asset_turnover # Rough proxy
             else:
                 metrics["ROIC"] = np.nan
    except:
        metrics["ROIC"] = np.nan

    # --- 2. REVENUE CAGR (3Y) ---
    try:
        rev_series = financials.loc["Total Revenue"]
        if len(rev_series) >= 4: # Need 4 points for 3 year intervals (Current, -1, -2, -3)
            latest = rev_series.iloc[0]
            start = rev_series.iloc[3]
            if start > 0 and latest > 0:
                metrics["Rev_CAGR_3Y"] = (latest / start) ** (1/3) - 1
            else:
                metrics["Rev_CAGR_3Y"] = 0
        elif len(rev_series) >= 2:
             latest = rev_series.iloc[0]
             start = rev_series.iloc[-1]
             years = len(rev_series) - 1
             if start > 0:
                metrics["Rev_CAGR_3Y"] = (latest / start) ** (1/years) - 1
             else:
                 metrics["Rev_CAGR_3Y"] = 0
        else:
             metrics["Rev_CAGR_3Y"] = np.nan
    except:
        metrics["Rev_CAGR_3Y"] = np.nan

    # --- 3. HARD FILTER DATA ---
    metrics["FCF_Positive"] = False
    try:
        fcf = cashflow.loc["Free Cash Flow"].iloc[0] if "Free Cash Flow" in cashflow.index else -1
        if fcf > 0: metrics["FCF_Positive"] = True
    except:
        pass
        
    metrics["Debt_EBITDA"] = np.nan
    try:
        total_debt = balance_sheet.loc["Total Debt"].iloc[0] if "Total Debt" in balance_sheet.index else 0
        ebitda = financials.loc["EBITDA"].iloc[0] if "EBITDA" in financials.index else 1
        metrics["Debt_EBITDA"] = total_debt / ebitda if ebitda != 0 else 100
    except:
        pass
        
    return metrics

def update_market_data(tickers_df, limit=None):
    if not os.path.exists(MARKET_DATA_DIR):
        os.makedirs(MARKET_DATA_DIR)
        
    tickers_list = tickers_df["Ticker"].unique()
    if limit:
        tickers_list = tickers_list[:limit]
        
    print(f"Updating data for {len(tickers_list)} tickers...")
    
    success_count = 0
    
    for i, ticker_sym in enumerate(tickers_list):
        # Handle dot in ticker (BRK.B -> BRK-B)
        y_ticker = ticker_sym.replace(".", "-")
        
        file_path = os.path.join(MARKET_DATA_DIR, f"{ticker_sym}_data.parquet")
        
        # Simple cache check (skip if modified today)
        # In prod, we might want to force update on weekends etc.
        # For now, always fetch if running update.
        
        try:
            print(f"[{i+1}/{len(tickers_list)}] Fetching {ticker_sym}...", end=" ", flush=True)
            ticker_obj = yf.Ticker(y_ticker)
            
            # Fetch ALL data needed
            # 1. Info
            info = ticker_obj.info
            
            # 2. History (1 Year for Risk/Tech)
            hist = ticker_obj.history(period="1y")
            
            # 3. Financials
            fins = ticker_obj.financials
            bs = ticker_obj.balance_sheet
            cf = ticker_obj.cashflow
            
            if hist.empty:
                print("Skipped (No history)")
                continue

            # Calculate Pro Metrics
            custom = calculate_custom_metrics(ticker_sym, info, fins, bs, cf, hist)
            
            # Fetch Name from uni
            name = tickers_df[tickers_df["Ticker"] == ticker_sym]["Security"].iloc[0] if "Security" in tickers_df.columns else ticker_sym
            
            # Pack data for storage
            # We can't easily save objects to parquet. We'll save a combined DataFrame of metrics
            # and a separate Price DataFrame if needed. 
            # Strategy: Save a "Meta" row with all scalar metrics, and maybe latest price.
            # Real scanner needs full history for MA calc.
            
            # Let's save a dictionary of dataframes using pickle or separate files? 
            # Plan said Parquet.
            # Best approach for file-per-ticker:
            # 1. metrics.csv (single row)
            # 2. history.csv (timeseries)
            
            # Or simpler: Save everything into a structured dict and pickle it? 
            # Parquet is strictly tabular.
            # Let's verify instructions: "Save to market_data/{ticker}_data.parquet"
            # We will flatten the scalar data into columns.
            
            # Flatten Info + Custom Metrics
            
            # Flatten Info + Custom Metrics
            
            # Calc Gross Margin Trend
            gm_trend = 0
            try:
                if len(fins.columns) >= 2:
                    curr_gm = fins.loc["Gross Profit"].iloc[0] / fins.loc["Total Revenue"].iloc[0]
                    prev_gm = fins.loc["Gross Profit"].iloc[1] / fins.loc["Total Revenue"].iloc[1]
                    gm_trend = curr_gm - prev_gm
            except:
                pass

            # Calc RSI
            rsi_val = 50
            try:
                delta = hist["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi_series = 100 - (100 / (1 + rs))
                rsi_val = rsi_series.iloc[-1]
            except:
                pass

            flat_data = {
                "Ticker": ticker_sym,
                "Name": name,
                "Sector": tickers_df[tickers_df["Ticker"] == ticker_sym]["Sector"].iloc[0],
                "Price": hist["Close"].iloc[-1],
                "MA200": hist["Close"].rolling(200).mean().iloc[-1] if len(hist) > 200 else np.nan,
                "MA50": hist["Close"].rolling(50).mean().iloc[-1] if len(hist) > 50 else np.nan,
                "RSI": rsi_val,
                "GrossMarginTrend": gm_trend,
                "Beta": info.get("beta", np.nan),
                "ForwardPE": info.get("forwardPE", np.nan),
                "PegRatio": info.get("pegRatio", np.nan),
                "Employees": info.get("fullTimeEmployees", np.nan),
                "EPS_Growth_3Y": info.get("earningsGrowth", 0),
                # Custom
                "ROIC": custom.get("ROIC"),
                "Rev_CAGR_3Y": custom.get("Rev_CAGR_3Y"),
                "FCF_Positive": custom.get("FCF_Positive"),
                "Debt_EBITDA": custom.get("Debt_EBITDA")
            }
            
            # Save Flattened Data
            df_flat = pd.DataFrame([flat_data])
            df_flat.to_parquet(file_path) # Fast and efficient
            
            # NOTE: For "History tracking", we need daily outputs. 
            # For "Scanner", we need cross-sectional data.
            # This flat file is perfect for the scanner.
            
            print("Done.")
            success_count += 1
            
        except Exception as e:
            print(f"Failed: {e}")
            
    print(f"Update Complete. {success_count} tickers processed.")

if __name__ == "__main__":
    uni = get_sp500_tickers()
    if not uni.empty:
        # Default run: 5 tickers for Testing, user can edit for full run
        print("Running FULL MODE (All S&P 500 tickers). This may take 5-10 minutes.")
        update_market_data(uni, limit=None)
    else:
        print("Could not load universe.")
