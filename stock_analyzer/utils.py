import pandas as pd
import json
import os

def format_number(num, decimals=2):
    """
    Formats a large number into human-readable strings with K, M, B, T suffixes.
    
    Parameters:
        num (float or int): The number to format.
        decimals (int): Number of decimals to show (default 2).
    
    Returns:
        str: Formatted string.
    """
    if num is None:
        return "N/A"
    
    abs_num = abs(num)
    
    if abs_num >= 1_000_000_000_000:
        value = num / 1_000_000_000_000
        suffix = "T"
    elif abs_num >= 1_000_000_000:
        value = num / 1_000_000_000
        suffix = "B"
    elif abs_num >= 1_000_000:
        value = num / 1_000_000
        suffix = "M"
    elif abs_num >= 1_000:
        value = num / 1_000
        suffix = "K"
    else:
        return f"{num:.{decimals}f}"
    
    return f"{value:.{decimals}f}{suffix}"

def format_percent(num, decimals=2):
    """
    Converts a float to a percentage string.
    
    Parameters:
        num (float): Number to convert (e.g., 0.25 = 25%).
        decimals (int): Number of decimals to show (default 2).
    
    Returns:
        str: Formatted percentage.
    """
    if num is None:
        return "N/A"
    return f"{num * 100:.{decimals}f}%"

# Alias for backwards compatibility
format_large_number = format_number

# ===== WATCHLIST MANAGEMENT =====
WATCHLIST_FILE = "watchlist.json"

def load_watchlist():
    """Load watchlist from JSON file."""
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    return []

def save_watchlist(tickers):
    """Save watchlist to JSON file."""
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(list(set(tickers)), f)
    return True

def toggle_watchlist(ticker):
    """Add or remove a ticker from the watchlist."""
    wl = load_watchlist()
    if ticker in wl:
        wl.remove(ticker)
        msg = "Removed from"
    else:
        wl.append(ticker)
        msg = "Added to"
    save_watchlist(wl)
    return msg
