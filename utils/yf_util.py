import yfinance as yf
import pandas as pd
from typing import Dict, Optional, Tuple
import time

def get_stock_price_change(ticker: str, period: str = "1mo") -> Optional[float]:
    """
    Get the percentage change in stock price over a specified period.
    
    Args:
        ticker (str): Stock ticker symbol
        period (str): Time period (e.g., "1mo", "3mo", "6mo", "1y")
    
    Returns:
        Optional[float]: Percentage change, or None if error
    """
    try:
        # Add .TO for Toronto Stock Exchange if needed, or handle other exchanges
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if len(hist) < 2:
            return None
            
        # Calculate percentage change from first to last price
        first_price = hist.iloc[0]['Close']
        last_price = hist.iloc[-1]['Close']
        change_pct = ((last_price - first_price) / first_price) * 100
        
        return change_pct
        
    except Exception as e:
        print(f"Error getting price change for {ticker}: {e}")
        return None

def get_stock_sector(ticker: str) -> Optional[str]:
    """
    Get the sector information for a given stock ticker.
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        Optional[str]: Sector name, or None if error
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Try different possible sector fields
        sector = info.get('sector') or info.get('industry') or info.get('category')
        
        return sector if sector else "Unknown"
        
    except Exception as e:
        print(f"Error getting sector for {ticker}: {e}")
        return "Unknown"

def get_stock_info_batch(tickers: list, period: str = "1mo") -> Dict[str, Dict]:
    """
    Get price changes and sectors for multiple tickers with rate limiting.
    
    Args:
        tickers (list): List of stock ticker symbols
        period (str): Time period for price change calculation
    
    Returns:
        Dict[str, Dict]: Dictionary with ticker as key and {'price_change': float, 'sector': str} as value
    """
    results = {}
    
    for ticker in tickers:
        try:
            # Get price change
            price_change = get_stock_price_change(ticker, period)
            
            # Get sector
            sector = get_stock_sector(ticker)
            
            results[ticker] = {
                'price_change': price_change,
                'sector': sector
            }
            
            # Rate limiting to avoid API issues
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            results[ticker] = {
                'price_change': None,
                'sector': "Unknown"
            }
    
    return results

def extract_ticker_from_cusip(cusip: str) -> Optional[str]:
    """
    Extract ticker symbol from CUSIP or company name.
    This is a simplified approach - in practice you might need a more robust mapping.
    
    Args:
        cusip (str): CUSIP or company name
    
    Returns:
        Optional[str]: Ticker symbol if found
    """
    # This is a simplified mapping - you might want to use a proper CUSIP to ticker database
    # For now, we'll try to extract common patterns
    
    # Remove common suffixes and clean up
    clean_name = str(cusip).upper().strip()
    
    # Common patterns for major companies
    ticker_mapping = {
        'APPLE': 'AAPL',
        'MICROSOFT': 'MSFT',
        'ALPHABET': 'GOOGL',
        'AMAZON': 'AMZN',
        'TESLA': 'TSLA',
        'BERKSHIRE': 'BRK.A',
        'JPMORGAN': 'JPM',
        'BANK OF AMERICA': 'BAC',
        'WELLS FARGO': 'WFC',
        'UNITEDHEALTH': 'UNH',
        'JOHNSON & JOHNSON': 'JNJ',
        'PROCTER & GAMBLE': 'PG',
        'VISA': 'V',
        'MASTERCARD': 'MA',
        'NVIDIA': 'NVDA',
        'META': 'META',
        'NETFLIX': 'NFLX',
        'SALESFORCE': 'CRM',
        'ORACLE': 'ORCL',
        'CISCO': 'CSCO'
    }
    
    # Check for exact matches first
    for company, ticker in ticker_mapping.items():
        if company in clean_name:
            return ticker
    
    # If no match found, return None
    return None
