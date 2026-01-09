# stock_picker_daily.py
import yfinance as yf
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD
from datetime import datetime

# -----------------------------
# 1. List of tickers to scan
# -----------------------------
# Example: S&P 500 tickers (shortened for demo)
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'JPM', 'V', 'DIS']

# -----------------------------
# 2. Function: Fundamental Score
# -----------------------------
def fundamental_score(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        score = 0

        # Revenue growth YoY %
        if 'revenueGrowth' in info and info['revenueGrowth']:
            rev_growth = info['revenueGrowth'] * 100
            score += min(max(rev_growth/20*10,0),10)  # scale to 0-10

        # EPS growth %
        if 'earningsQuarterlyGrowth' in info and info['earningsQuarterlyGrowth']:
            eps_growth = info['earningsQuarterlyGrowth'] * 100
            score += min(max(eps_growth/20*10,0),10)

        # Debt-to-Equity
        if 'debtToEquity' in info and info['debtToEquity'] is not None:
            de = info['debtToEquity']
            if de < 1:
                score += 10
            elif de < 2:
                score += 5
            else:
                score += 0

        return min(score,30)  # fundamental max score
    except:
        return 0

# -----------------------------
# 3. Function: Technical Score
# -----------------------------
def technical_score(ticker):
    try:
        df = yf.download(ticker, period='6mo', interval='1d', progress=False)
        if df.empty:
            return 0

        score = 0
        
        # Ensure flat columns for ta library if MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Moving Averages
        df['MA50'] = df['Close'].rolling(50).mean()
        df['MA200'] = df['Close'].rolling(200).mean()
        if df['MA50'].iloc[-1] > df['MA200'].iloc[-1]:
            score += 5  # Bullish

        # RSI
        rsi_series = RSIIndicator(df['Close'], window=14).rsi()
        rsi = rsi_series.iloc[-1]
        
        if rsi < 30:
            score += 5  # Oversold, potential buy
        elif rsi < 50:
            score += 3

        # MACD
        macd_series = MACD(df['Close']).macd_diff()
        macd = macd_series.iloc[-1]
        
        if macd > 0:
            score += 5  # bullish

        return min(score, 20)
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return 0

# -----------------------------
# 4. Function: Risk Score
# -----------------------------
def risk_score(ticker):
    try:
        df = yf.download(ticker, period='1y', interval='1d', progress=False)
        if df.empty: return 0
        
        # Ensure flat columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        returns = df['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # annualized
        if volatility < 0.2:
            return 10
        elif volatility < 0.35:
            return 5
        else:
            return 0
    except:
        return 0

# -----------------------------
# 5. Main: Score & Rank
# -----------------------------
if __name__ == "__main__":
    print(f"Starting Scan of {len(tickers)} tickers...")
    results = []

    for ticker in tickers:
        print(f"Scanning {ticker}...")
        f_score = fundamental_score(ticker)
        t_score = technical_score(ticker)
        r_score = risk_score(ticker)
        
        # Weighted score
        total_score = f_score*0.4 + t_score*0.4 + r_score*0.2
        
        results.append({
            'Ticker': ticker,
            'Fundamental': f_score,
            'Technical': t_score,
            'Risk': r_score,
            'Total Score': total_score
        })

    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values(by='Total Score', ascending=False).reset_index(drop=True)

    # -----------------------------
    # 6. Top 10 Stocks
    # -----------------------------
    top10 = df_results.head(10)

    # Add recommendation
    def recommendation(score):
        if score >= 20:
            return "Buy"
        elif score >= 15:
            return "Hold"
        else:
            return "Avoid"

    top10['Recommendation'] = top10['Total Score'].apply(recommendation)

    # -----------------------------
    # 7. Output
    # -----------------------------
    print(f"\n--- Top 10 Stocks as of {datetime.today().strftime('%Y-%m-%d')} ---")
    print(top10[['Ticker','Total Score','Recommendation','Fundamental','Technical','Risk']])

    # Optional: Save to Excel
    try:
        top10.to_excel("top10_stocks.xlsx", index=False)
        print("\nSaved result to 'top10_stocks.xlsx'")
    except Exception as e:
        print(f"\nCould not save Excel: {e} (Do you have openpyxl installed?)")
