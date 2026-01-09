# Stock Analysis & Stock Picker App

A Python-first application designed to analyze stocks and provide Buy/Hold/Avoid recommendations based on fundamental, valuation, technical, and risk analysis.

## Features
- **Fundamental Analysis**: Revenue growth, ROE, Debt/Equity, etc.
- **Valuation**: P/E ratios, simple DCF/Intrinsic value.
- **Technicals**: RDA, MACD, Moving Averages.
- **Risk Analysis**: Beta, Volatility.
- **Weighted Scoring**: Comprehensive score (0-100) combining all metrics.

## Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   streamlit run app.py
   ```

## Architecture
- `data_fetcher.py`: Handles data retrieval from yfinance.
- Analysis modules: `fundamentals.py`, `valuation.py`, `technicals.py`, `risk.py`.
- `scoring.py`: Aggregates scores.
- `app.py`: Streamlit dashboard.


## RUN - Stocke picker\stock_analyzer> python -m streamlit run app.py