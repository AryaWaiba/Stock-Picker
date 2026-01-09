import yfinance as yf
import pandas as pd
import numpy as np

def get_stock_data(ticker_symbol):
    """
    Fetches raw data for a given ticker from yfinance.
    Returns a dictionary containing:
    - info: Dictionary of stock info
    - history: DataFrame of price history (max period)
    - financials: DataFrame of annual financials
    - balance_sheet: DataFrame of annual balance sheet
    - cashflow: DataFrame of annual cashflow
    """
    ticker = yf.Ticker(ticker_symbol)
    
    # Fetch data
    try:
        info = ticker.info
        history = ticker.history(period="max")
        financials = ticker.financials
        balance_sheet = ticker.balance_sheet
        cashflow = ticker.cashflow
        
        # Basic validation
        if history.empty:
            return None
            
        return {
            "ticker": ticker, # Return the object itself for advanced usage if needed
            "symbol": ticker_symbol.upper(),
            "info": info,
            "history": history,
            "financials": financials,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow
        }
    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")
        return None

def get_market_price(data):
    """Extracts current market price from data."""
    if not data or "info" not in data:
        return None
    return data["info"].get("currentPrice") or data["info"].get("regularMarketPrice")

def get_sector_industry(data):
    """Extracts sector and industry."""
    if not data or "info" not in data:
        return "Unknown", "Unknown"
    return data["info"].get("sector", "Unknown"), data["info"].get("industry", "Unknown")
