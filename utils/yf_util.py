import yfinance as yf
import pandas as pd
from typing import Dict, Optional, Tuple
import time

try:
    from .openai_util import get_sector_with_fallback, get_ticker_with_fallback
    from .ticker_mapping import ticker_mapping
except ImportError:
    try:
        from openai_util import get_sector_with_fallback, get_ticker_with_fallback
        from ticker_mapping import ticker_mapping
    except ImportError:
        # Fallback if modules are not available
        def get_sector_with_fallback(company_name: str, ticker: Optional[str] = None, use_cache: bool = True) -> Optional[str]:
            return "Unknown"
        def get_ticker_with_fallback(company_name: str, use_cache: bool = True) -> Optional[str]:
            return None
        # Create a dummy ticker mapping
        class DummyTickerMapping:
            def get_ticker(self, company_name: str) -> Optional[str]:
                return None
            def get_sector(self, company_name: str) -> Optional[str]:
                return None
            def add_mapping(self, company_name: str, ticker: str, sector: str = "Unknown", source: str = "auto"):
                pass
        ticker_mapping = DummyTickerMapping()

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

def get_stock_sector(ticker: str, company_name: Optional[str] = None) -> Optional[str]:
    """
    Get the sector information for a given stock ticker with CSV mapping and OpenAI fallback.
    
    Args:
        ticker (str): Stock ticker symbol
        company_name (Optional[str]): Company name for fallback
    
    Returns:
        Optional[str]: Sector name, or None if error
    """
    # 1. First, check CSV mapping if company name is provided
    if company_name:
        csv_sector = ticker_mapping.get_sector(company_name)
        if csv_sector and csv_sector != "Unknown":
            return csv_sector
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Check if it's an ETF first
        if info.get('quoteType') == 'ETF' or info.get('category') == 'ETF':
            return "ETF"
        
        # Check company name for ETF indicators
        if company_name and any(keyword in company_name.upper() for keyword in ['ETF', 'EXCHANGE TRADED FUND', 'TRUST', 'FUND']):
            return "ETF"
        
        # Try different possible sector fields
        sector = info.get('sector') or info.get('industry') or info.get('category')
        
        if sector and sector != "Unknown":
            # Add to CSV mapping for future use
            if company_name:
                ticker_mapping.add_mapping(company_name, ticker, sector, source="yfinance")
            return sector
        
        # If Yahoo Finance doesn't provide sector, try OpenAI fallback
        if company_name:
            print(f"Yahoo Finance couldn't find sector for {ticker}, trying OpenAI fallback...")
            openai_sector = get_sector_with_fallback(company_name, ticker)
            if openai_sector and openai_sector != "Unknown":
                # Add to CSV mapping for future use
                ticker_mapping.add_mapping(company_name, ticker, openai_sector, source="openai")
                return openai_sector
        
        return "Unknown"
        
    except Exception as e:
        print(f"Error getting sector for {ticker}: {e}")
        
        # Check company name for ETF indicators even if Yahoo Finance fails
        if company_name and any(keyword in company_name.upper() for keyword in ['ETF', 'EXCHANGE TRADED FUND', 'TRUST', 'FUND']):
            return "ETF"
        
        # Try OpenAI fallback if Yahoo Finance fails
        if company_name:
            print(f"Trying OpenAI fallback for {ticker}...")
            openai_sector = get_sector_with_fallback(company_name, ticker)
            if openai_sector and openai_sector != "Unknown":
                # Add to CSV mapping for future use
                ticker_mapping.add_mapping(company_name, ticker, openai_sector, source="openai")
                return openai_sector
        
        return "Unknown"

def get_stock_info_batch(tickers: list, company_names: Dict[str, str] = None, period: str = "1mo") -> Dict[str, Dict]:
    """
    Get price changes and sectors for multiple tickers with rate limiting.
    
    Args:
        tickers (list): List of stock ticker symbols
        company_names (Dict[str, str]): Dictionary mapping tickers to company names
        period (str): Time period for price change calculation
    
    Returns:
        Dict[str, Dict]: Dictionary with ticker as key and {'price_change': float, 'sector': str} as value
    """
    results = {}
    
    for ticker in tickers:
        try:
            # Get price change
            price_change = get_stock_price_change(ticker, period)
            
            # Get company name for sector detection
            company_name = company_names.get(ticker) if company_names else None
            
            # Get sector
            sector = get_stock_sector(ticker, company_name)
            
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
    Extract ticker symbol from CUSIP or company name with CSV mapping and OpenAI fallback.
    
    Args:
        cusip (str): CUSIP or company name
    
    Returns:
        Optional[str]: Ticker symbol if found
    """
    # Remove common suffixes and clean up
    clean_name = str(cusip).upper().strip()
    
    # 1. First, check CSV mapping
    csv_ticker = ticker_mapping.get_ticker(clean_name)
    if csv_ticker:
        return csv_ticker
    
    # 2. Check local hardcoded mapping (legacy fallback)
    local_mapping = {
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
        'CISCO': 'CSCO',
        'HESS': 'HES',
        'ADVANCED MICRO DEVICES': 'AMD',
        'BRIDGEBIO PHARMA': 'BBIO',
        'MARVELL TECHNOLOGY': 'MRVL',
        'DISCOVER FINL SVCS': 'DFS',
        'ANSYS': 'ANSS',
        'SHELL': 'SHEL',
        'GOLDMAN SACHS': 'GS',
        'UNITED STATES STL': 'X',
        'ALLSTATE': 'ALL',
        'HCA HEALTHCARE': 'HCA'
    }
    
    # Check for exact matches in local mapping
    for company, ticker in local_mapping.items():
        if company in clean_name:
            return ticker
    
    # 3. If no match found, try OpenAI fallback
    try:
        openai_ticker = get_ticker_with_fallback(str(cusip))
        if openai_ticker:
            print(f"OpenAI found ticker for {cusip}: {openai_ticker}")
            # Add to CSV mapping for future use
            ticker_mapping.add_mapping(clean_name, openai_ticker, source="openai")
            return openai_ticker
    except Exception as e:
        print(f"OpenAI ticker extraction failed for {cusip}: {e}")
    
    # If no match found, return None
    return None
