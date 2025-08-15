import openai
import os
from typing import Optional
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_sector_from_openai(company_name: str, ticker: Optional[str] = None) -> Optional[str]:
    """
    Use OpenAI to determine the most likely sector for a company.
    
    Args:
        company_name (str): The name of the company
        ticker (Optional[str]): The ticker symbol if available
    
    Returns:
        Optional[str]: The sector name or None if error
    """
    try:
        # Get OpenAI API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("OpenAI API key not found in environment variables")
            return None
        
        # Set up OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Create prompt
        prompt = f"""
        Given the company information below, provide the most likely sector/industry classification.
        Return ONLY the sector name, nothing else.
        
        Company: {company_name}
        Ticker: {ticker if ticker else 'Not provided'}
        
        Common sectors include: Technology, Healthcare, Financial Services, Consumer Cyclical, 
        Consumer Defensive, Industrials, Energy, Basic Materials, Real Estate, Communication Services, 
        Utilities, etc.
        
        Sector:"""
        
        # Make API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst. Provide only the sector name, no additional text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=20,
            temperature=0.1
        )
        
        # Extract and clean the response
        sector = response.choices[0].message.content.strip()
        
        # Basic validation - ensure it looks like a sector name
        if sector and len(sector) < 50 and not sector.startswith("I'm sorry"):
            return sector
        else:
            return None
            
    except Exception as e:
        print(f"Error getting sector from OpenAI for {company_name}: {e}")
        return None

def get_ticker_from_openai(company_name: str) -> Optional[str]:
    """
    Use OpenAI to determine the most likely ticker symbol for a company.
    
    Args:
        company_name (str): The name of the company
    
    Returns:
        Optional[str]: The ticker symbol or None if error
    """
    try:
        # Get OpenAI API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("OpenAI API key not found in environment variables")
            return None
        
        # Set up OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Create prompt
        prompt = f"""
        Given the company name below, provide the most likely stock ticker symbol.
        Return ONLY the ticker symbol, nothing else.
        
        Company: {company_name}
        
        Common ticker examples:
        - Apple Inc -> AAPL
        - Microsoft Corporation -> MSFT
        - Tesla Inc -> TSLA
        - JPMorgan Chase & Co -> JPM
        - Goldman Sachs Group Inc -> GS
        - Hess Corporation -> HES
        - Advanced Micro Devices Inc -> AMD
        - Marvell Technology Inc -> MRVL
        - Discover Financial Services -> DFS
        - Ansys Inc -> ANSS
        - Shell PLC -> SHEL
        - United States Steel Corp -> X
        - Allstate Corp -> ALL
        - HCA Healthcare Inc -> HCA
        - BridgeBio Pharma Inc -> BBIO
        
        Ticker:"""
        
        # Make API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst. Provide only the ticker symbol, no additional text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        # Extract and clean the response
        ticker = response.choices[0].message.content.strip().upper()
        
        # Basic validation - ensure it looks like a ticker symbol
        if ticker and len(ticker) <= 6 and ticker.isalnum():
            return ticker
        else:
            return None
            
    except Exception as e:
        print(f"Error getting ticker from OpenAI for {company_name}: {e}")
        return None

def get_ticker_with_fallback(company_name: str, use_cache: bool = True) -> Optional[str]:
    """
    Get ticker symbol with caching to avoid repeated API calls.
    
    Args:
        company_name (str): The name of the company
        use_cache (bool): Whether to use cached results
    
    Returns:
        Optional[str]: The ticker symbol or None if error
    """
    # Simple in-memory cache
    if not hasattr(get_ticker_with_fallback, 'cache'):
        get_ticker_with_fallback.cache = {}
    
    # Create cache key
    cache_key = f"ticker_{company_name}"
    
    # Check cache first
    if use_cache and cache_key in get_ticker_with_fallback.cache:
        return get_ticker_with_fallback.cache[cache_key]
    
    # Get ticker from OpenAI
    ticker = get_ticker_from_openai(company_name)
    
    # Cache the result
    if ticker:
        get_ticker_with_fallback.cache[cache_key] = ticker
    
    return ticker

def get_sector_with_fallback(company_name: str, ticker: Optional[str] = None, use_cache: bool = True) -> Optional[str]:
    """
    Get sector information with caching to avoid repeated API calls.
    
    Args:
        company_name (str): The name of the company
        ticker (Optional[str]): The ticker symbol if available
        use_cache (bool): Whether to use cached results
    
    Returns:
        Optional[str]: The sector name or None if error
    """
    # Simple in-memory cache (in production, you might want to use Redis or a database)
    if not hasattr(get_sector_with_fallback, 'cache'):
        get_sector_with_fallback.cache = {}
    
    # Create cache key
    cache_key = f"{company_name}_{ticker}" if ticker else company_name
    
    # Check cache first
    if use_cache and cache_key in get_sector_with_fallback.cache:
        return get_sector_with_fallback.cache[cache_key]
    
    # Get sector from OpenAI
    sector = get_sector_from_openai(company_name, ticker)
    
    # Cache the result
    if sector:
        get_sector_with_fallback.cache[cache_key] = sector
    
    return sector
